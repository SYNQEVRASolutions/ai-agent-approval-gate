"""Run this to see the gate decide, cap, block and log. python3 test_approval_gate.py"""
from approval_gate import Action, ApprovalGate, Risk


def main():
    g = ApprovalGate(caps={Risk.LOW.value: 2, Risk.MEDIUM.value: 1, Risk.HIGH.value: 1},
                     approver=lambda a: a.name == "change_protection_setting")

    print("1. two low risk actions run, the third hits the hourly cap")
    for i in range(3):
        d, out = g.execute(Action(f"create_ticket_{i}", Risk.LOW), lambda a: "ok")
        print("  ", i + 1, d.allowed, "|", d.reason)

    print("2. medium risk is allowed once, then capped")
    for i in range(2):
        d, _ = g.execute(Action(f"start_chiller_{i}", Risk.MEDIUM), lambda a: "ok")
        print("  ", i + 1, d.allowed, "|", d.reason)

    print("3. irreversible high risk is refused even with an approver")
    d = g.check(Action("switch_load", Risk.HIGH, reversible=False))
    print("  ", d.allowed, "|", d.reason)

    print("4. reversible high risk runs only after a named human approves")
    d, _ = g.execute(Action("change_protection_setting", Risk.HIGH, reversible=True), lambda a: "ok")
    print("  ", d.allowed, "|", d.reason)

    print("5. audit trail keeps every decision")
    for row in g.audit_trail():
        print("  ", row["risk"], row["action"], "allowed=" + str(row["allowed"]))

    assert g.audit_trail()
    print("OK")


if __name__ == "__main__":
    main()
