from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Dictionary:
    domains: dict[str, str]
    actions: dict[str, str]

    def domain_code(self, name: str) -> str:
        normalized = name.lower()
        for code, value in self.domains.items():
            if value == normalized:
                return code
        raise KeyError(name)

    def action_code(self, name: str) -> str:
        normalized = name.lower()
        for code, value in self.actions.items():
            if value == normalized:
                return code
        raise KeyError(name)

    def check(self) -> list[str]:
        errors: list[str] = []
        errors.extend(_check_table("domain", self.domains))
        errors.extend(_check_table("action", self.actions))
        overlap = set(self.domains) & set(self.actions)
        if overlap:
            errors.append(f"domain/action code overlap: {', '.join(sorted(overlap))}")
        return errors


def default_dictionary() -> Dictionary:
    return Dictionary(
        domains={
            "s": "security",
            "d": "data",
            "r": "refactor",
            "p": "prediction",
            "g": "gravity",
            "n": "neurostate",
            "o": "observability",
        },
        actions={
            "x": "xss",
            "m": "summarize",
            "f": "fix",
            "a": "audit",
            "b": "branch",
            "q": "query",
            "u": "update",
            "v": "validate",
        },
    )


def _check_table(label: str, table: dict[str, str]) -> list[str]:
    errors = []
    seen_values: dict[str, str] = {}
    for code, value in table.items():
        if len(code) != 1 or not code.isascii() or not code.isalnum():
            errors.append(f"{label} code must be one ASCII alnum: {code}")
        if value in seen_values:
            errors.append(f"{label} value collision: {value}")
        seen_values[value] = code
    return errors

