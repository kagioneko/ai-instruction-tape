from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter

from .codec import build_ait, decode_to_japanese
from .core import AitPacket, decode_ait


@dataclass(frozen=True)
class AgentReply:
    child: str
    tape: str
    human_log: str
    result: dict[str, object]
    elapsed_ms: float


@dataclass
class ChildAgent:
    name: str
    capabilities: set[str]
    memory: dict[int, str] = field(default_factory=dict)

    def handle_tape(self, tape: str) -> AgentReply:
        started = perf_counter()
        packet = decode_ait(tape)
        action_key = f"{packet.domain}:{packet.action}"
        if action_key not in self.capabilities:
            result: dict[str, object] = {
                "ok": False,
                "error": "unsupported_instruction",
                "action": action_key,
            }
        else:
            result = self._execute(packet)
        elapsed_ms = (perf_counter() - started) * 1000
        return AgentReply(
            child=self.name,
            tape=tape,
            human_log=decode_to_japanese(tape),
            result=result,
            elapsed_ms=elapsed_ms,
        )

    def _execute(self, packet: AitPacket) -> dict[str, object]:
        target_text = self.memory.get(packet.target, "")
        if packet.domain == "security" and packet.action == "xss":
            vulnerable = "<script>" in target_text.lower()
            return {
                "ok": True,
                "target": f"#ctx{packet.target}",
                "vulnerable": vulnerable,
                "finding": "script_tag_detected" if vulnerable else "none",
            }
        if packet.domain == "data" and packet.action == "summarize":
            return {
                "ok": True,
                "target": f"#ctx{packet.target}",
                "summary": target_text[:48],
            }
        return {"ok": True, "target": f"#ctx{packet.target}", "handled": True}


@dataclass
class ParentAgent:
    children: dict[str, ChildAgent]

    def instruct(
        self,
        child_name: str,
        *,
        domain: str,
        action: str,
        target: int,
        priority: int = 5,
    ) -> AgentReply:
        if child_name not in self.children:
            raise KeyError(f"unknown child agent: {child_name}")
        tape = build_ait(domain=domain, action=action, target=target, priority=priority)
        return self.children[child_name].handle_tape(tape)

