from ait.agents import ChildAgent, ParentAgent


def main() -> None:
    security_child = ChildAgent(
        name="security-child",
        capabilities={"security:xss"},
        memory={
            4: 'render("<script>alert(1)</script>")',
            7: "plain text only",
        },
    )
    data_child = ChildAgent(
        name="data-child",
        capabilities={"data:summarize"},
        memory={
            7: "This is a long context document that should be summarized quickly.",
        },
    )
    parent = ParentAgent(
        children={
            "security": security_child,
            "data": data_child,
        }
    )

    replies = [
        parent.instruct("security", domain="security", action="xss", target=4, priority=9),
        parent.instruct("data", domain="data", action="summarize", target=7, priority=3),
    ]

    for reply in replies:
        print(f"parent -> {reply.child}: {reply.tape}")
        print(f"log: {reply.human_log}")
        print(f"result: {reply.result}")
        print(f"elapsed_ms: {reply.elapsed_ms:.4f}")
        print()


if __name__ == "__main__":
    main()

