"""Approval gate for AI agents that act on real systems.

An agent is allowed to propose any action. Whether it may *execute* one depends on
the risk class, the remaining caps for the hour, and whether it can be undone.

No dependencies. Python 3.9+.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Callable, Dict, List, Optional


class Risk(str, Enum):
    LOW = "low"          # ticket creation, logging, read-only follow ups
    MEDIUM = "medium"    # start standby chiller, raise work order with cost
    HIGH = "high"        # change a protection setting, switch load


@dataclass
class Action:
    name: str
    risk: Risk
    reversible: bool = True
    cost: float = 0.0
    reason: str = ""
    evidence: List[str] = field(default_factory=list)


@dataclass
class Decision:
    allowed: bool
    requires_human: bool
    reason: str


class ApprovalGate:
    """Decides if an agent proposal may run, and keeps an audit trail.

    caps: max executions per hour per risk class.
    approver: callable that returns True when a named human approved the action.
    clock: injectable for tests.
    """

    def __init__(self, caps: Optional[Dict[str, int]] = None,
                 approver: Optional[Callable[[Action], bool]] = None,
                 clock: Optional[Callable[[], datetime]] = None):
        self.caps = caps or {Risk.LOW.value: 30, Risk.MEDIUM.value: 6, Risk.HIGH.value: 1}
        self.approver = approver
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.log: List[dict] = []
        self._executed: List[tuple] = []

    def _executed_last_hour(self, risk: Risk) -> int:
        now = self.clock()
        self._executed = [(t, r) for (t, r) in self._executed if (now - t).total_seconds() < 3600]
        return sum(1 for _, r in self._executed if r == risk)

    def check(self, action: Action) -> Decision:
        if not action.reversible and action.risk is Risk.HIGH:
            return self._record(action, Decision(False, True,
                "irreversible high risk action: blocked, needs a documented rollback"))
        used = self._executed_last_hour(action.risk)
        cap = self.caps.get(action.risk.value, 0)
        if used >= cap:
            return self._record(action, Decision(False, True,
                f"hourly cap reached for {action.risk.value} ({used}/{cap}): escalate instead of improvising"))
        if action.risk is Risk.HIGH:
            approved = bool(self.approver and self.approver(action))
            return self._record(action, Decision(approved, True,
                "high risk: executed after human approval" if approved
                else "high risk: waiting for a named human approval"))
        return self._record(action, Decision(True, False, f"{action.risk.value} risk within caps"))

    def execute(self, action: Action, run: Callable[[Action], object]):
        decision = self.check(action)
        if not decision.allowed:
            return decision, None
        self._executed.append((self.clock(), action.risk))
        return decision, run(action)

    def _record(self, action: Action, decision: Decision) -> Decision:
        self.log.append({
            "at": self.clock().isoformat(), "action": action.name,
            "risk": action.risk.value, "allowed": decision.allowed,
            "requires_human": decision.requires_human, "reason": decision.reason,
            "cost": action.cost, "evidence": list(action.evidence),
        })
        return decision

    def audit_trail(self) -> List[dict]:
        return list(self.log)
