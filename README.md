# AI Agent Approval Gate: risk classes, caps and an audit trail

A small, dependency-free Python module for AI agents that act on real systems: data
center power, plant equipment, tickets, work orders, anything where a wrong action
costs money.

An agent may propose anything. Whether it may **execute** depends on three things:
the risk class of the action, the remaining hourly cap for that class, and whether
the action can be undone.

```python
from approval_gate import Action, ApprovalGate, Risk

gate = ApprovalGate(caps={Risk.LOW.value: 30, Risk.MEDIUM.value: 6, Risk.HIGH.value: 1},
                    approver=lambda action: on_call_engineer_approved(action))

decision, result = gate.execute(
    Action("start_standby_chiller", Risk.MEDIUM, reason="cooling headroom 4%",
           evidence=["supply_temp 24.1C", "outside_temp 41C"]),
    run=lambda action: plant.start_chiller(2),
)

if not decision.allowed:
    escalate(decision.reason)
```

## What the five layers look like in code

| Layer | What it does | Where it lives |
|---|---|---|
| Read only | Agent observes for two weeks before it is trusted | your data path |
| Propose, do not act | Agent drafts an action with evidence | `Action.evidence` |
| Approval gate by risk | Low runs, high waits for a named human | `Risk` + `approver` |
| Hard caps | Actions per hour, spend, blast radius | `caps` |
| Audit trail | Every input, decision and output, timestamped | `gate.audit_trail()` |

## Why this exists

In November 2026 four UK regulators confirmed that the business using an autonomous
agent carries the liability, not the model provider. Handing an agent authority without
a gate is an operational risk, not a technical detail.

## Run the demo

```bash
python3 test_approval_gate.py
```

It prints a cap being hit, an irreversible action being refused, and a reversible high
risk action running only after approval.

## Install

No dependencies. Copy `approval_gate.py` into your project, or:

```bash
pip install git+https://github.com/SYNQEVRASolutions/ai-agent-approval-gate
```

## Contents

- `approval_gate.py` - the gate, risk classes, caps, audit trail
- `test_approval_gate.py` - runnable demo and cap/approval checks
- `docs/agent-liability-checklist.md` - the pre-deployment checklist

## Who builds this

SYNQEVRA Solutions builds AI agents, chatbots and custom software for data centers,
plants and workshops: UPS, generator, cooling, compressor and PLC telemetry.

Contact: fatircompanyai@gmail.com
