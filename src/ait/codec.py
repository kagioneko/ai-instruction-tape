from __future__ import annotations

from .core import AitPacket, decode_ait


DOMAIN_TO_EAP = {
    "security": "SEC",
    "data": "DAT",
    "refactor": "REF",
    "prediction": "PRED",
    "gravity": "SGE",
    "neurostate": "NST",
    "observability": "OBS",
}

ACTION_TO_EAP = {
    "xss": "XSS",
    "summarize": "SUM",
    "fix": "FIX",
    "audit": "AUDIT",
    "branch": "BRANCH",
    "query": "QUERY",
    "update": "UPDATE",
    "validate": "VALIDATE",
}

DOMAIN_JA = {
    "security": "セキュリティ",
    "data": "データ",
    "refactor": "リファクタリング",
    "prediction": "予測",
    "gravity": "意味的重力",
    "neurostate": "NeuroState",
    "observability": "観測",
}

ACTION_JA = {
    "xss": "XSS検証",
    "summarize": "要約",
    "fix": "修正",
    "audit": "監査",
    "branch": "分岐",
    "query": "問い合わせ",
    "update": "更新",
    "validate": "検証",
}

PRIORITY_JA = {
    1: "最速",
    2: "低",
    3: "低",
    4: "通常",
    5: "通常",
    6: "やや高",
    7: "高",
    8: "かなり高",
    9: "最高",
}


def build_eap(
    *,
    domain: str,
    action: str,
    target: int,
    priority: int = 5,
    direction: str = ">",
) -> str:
    packet = AitPacket(
        domain=domain.lower(),
        target=target,
        action=action.lower(),
        priority=priority,
    )
    domain_code = DOMAIN_TO_EAP.get(packet.domain, packet.domain.upper())
    action_code = ACTION_TO_EAP.get(packet.action, packet.action.upper())
    return f"{direction}{domain_code}:{action_code} #ctx{packet.target} !{packet.priority}"


def build_ait(
    *,
    domain: str,
    action: str,
    target: int,
    priority: int = 5,
) -> str:
    return AitPacket(
        domain=domain.lower(),
        target=target,
        action=action.lower(),
        priority=priority,
    ).encode()


def decode_to_japanese(raw: str) -> str:
    packet = decode_ait(raw) if _looks_like_ait(raw) else _parse_eap_packet(raw)
    domain = DOMAIN_JA.get(packet.domain, packet.domain)
    action = ACTION_JA.get(packet.action, packet.action)
    priority = PRIORITY_JA.get(packet.priority, str(packet.priority))
    return f"コンテキスト{packet.target}に対して、{domain}領域の{action}を実行します。優先度は{priority}です。"


def _looks_like_ait(raw: str) -> bool:
    return len(raw) == 4 and raw.isascii() and raw.isalnum() and raw.islower()


def _parse_eap_packet(raw: str) -> AitPacket:
    from .core import parse_eap

    return parse_eap(raw)

