from ait.agents import ChildAgent, ParentAgent


def test_parent_instructs_child_with_tape() -> None:
    child = ChildAgent(
        name="security-child",
        capabilities={"security:xss"},
        memory={4: "<script>alert(1)</script>"},
    )
    parent = ParentAgent(children={"security": child})

    reply = parent.instruct("security", domain="security", action="xss", target=4, priority=9)

    assert reply.tape == "s4x9"
    assert reply.child == "security-child"
    assert reply.result["ok"] is True
    assert reply.result["vulnerable"] is True
    assert "XSS検証" in reply.human_log


def test_child_rejects_unsupported_instruction() -> None:
    child = ChildAgent(name="data-child", capabilities={"data:summarize"}, memory={4: "text"})

    reply = child.handle_tape("s4x9")

    assert reply.result["ok"] is False
    assert reply.result["error"] == "unsupported_instruction"

