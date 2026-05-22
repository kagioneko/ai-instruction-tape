from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Optional

from .base36 import decode_base36, encode_base36
from .dictionary import Dictionary, default_dictionary


class AitError(ValueError):
    pass


EAP_RE = re.compile(
    r"^\s*(?P<dir>[><=])(?P<domain>[A-Z0-9]{2,16}):(?P<action>[A-Z0-9_]{2,24})"
    r"\s+#ctx(?P<target>[0-9a-z]+)"
    r"(?:\s+!(?P<priority>[1-9]))?"
    r"(?:\s+\|.*)?\s*$",
    re.IGNORECASE,
)


DOMAIN_ALIASES = {
    "sec": "security",
    "security": "security",
    "dat": "data",
    "data": "data",
    "sys": "refactor",
    "ref": "refactor",
    "refactor": "refactor",
    "pred": "prediction",
    "prediction": "prediction",
    "sge": "gravity",
    "gravity": "gravity",
    "nst": "neurostate",
    "neuro": "neurostate",
    "neurostate": "neurostate",
    "obs": "observability",
    "observability": "observability",
}

ACTION_ALIASES = {
    "xss": "xss",
    "sum": "summarize",
    "summarize": "summarize",
    "fix": "fix",
    "audit": "audit",
    "branch": "branch",
    "query": "query",
    "update": "update",
    "validate": "validate",
    "val": "validate",
}


@dataclass(frozen=True)
class AitPacket:
    domain: str
    target: int
    action: str
    priority: int

    def encode(self, dictionary: Optional[Dictionary] = None) -> str:
        dictionary = dictionary or default_dictionary()
        try:
            domain_code = dictionary.domain_code(self.domain)
            action_code = dictionary.action_code(self.action)
        except KeyError as exc:
            raise AitError(f"unknown dictionary value: {exc.args[0]}") from exc
        return f"{domain_code}{encode_base36(self.target)}{action_code}{self.priority}"

    def to_eap(self) -> str:
        domain = {
            "security": "SEC",
            "data": "DAT",
            "refactor": "REF",
            "prediction": "PRED",
            "gravity": "SGE",
            "neurostate": "NST",
            "observability": "OBS",
        }.get(self.domain, self.domain.upper())
        action = {
            "xss": "XSS",
            "summarize": "SUM",
            "fix": "FIX",
            "audit": "AUDIT",
            "branch": "BRANCH",
            "query": "QUERY",
            "update": "UPDATE",
            "validate": "VALIDATE",
        }.get(self.action, self.action.upper())
        return f">{domain}:{action} #ctx{self.target} !{self.priority}"


def encode_eap(eap: str, dictionary: Optional[Dictionary] = None) -> str:
    return parse_eap(eap).encode(dictionary)


def decode_ait(raw: str, dictionary: Optional[Dictionary] = None) -> AitPacket:
    dictionary = dictionary or default_dictionary()
    if not re.fullmatch(r"[a-z0-9]{4}", raw):
        raise AitError("AIT packet must be exactly four lowercase ASCII alnum chars")
    domain_code, target_code, action_code, priority_code = raw
    if domain_code not in dictionary.domains:
        raise AitError(f"unknown domain code: {domain_code}")
    if action_code not in dictionary.actions:
        raise AitError(f"unknown action code: {action_code}")
    if priority_code not in "123456789":
        raise AitError("priority must be 1-9")
    return AitPacket(
        domain=dictionary.domains[domain_code],
        target=decode_base36(target_code),
        action=dictionary.actions[action_code],
        priority=int(priority_code),
    )


def parse_eap(eap: str) -> AitPacket:
    match = EAP_RE.match(eap)
    if not match:
        raise AitError(f"unsupported EAP packet: {eap}")
    groups = match.groupdict()
    domain = _normalize(DOMAIN_ALIASES, groups["domain"], "domain")
    action = _normalize(ACTION_ALIASES, groups["action"], "action")
    target_raw = groups["target"].lower()
    target = int(target_raw, 10) if target_raw.isdigit() else int(target_raw, 36)
    priority = int(groups["priority"] or 5)
    return AitPacket(domain=domain, target=target, action=action, priority=priority)


def _normalize(table: dict[str, str], value: str, label: str) -> str:
    key = value.lower()
    if key not in table:
        raise AitError(f"unknown {label}: {value}")
    return table[key]
