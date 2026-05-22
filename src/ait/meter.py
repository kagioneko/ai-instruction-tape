from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Optional

from .core import encode_eap


@dataclass(frozen=True)
class Measurement:
    label: str
    text: str
    chars: int
    utf8_bytes: int
    heuristic_tokens: int

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def measure_text(text: str, label: str) -> Measurement:
    return Measurement(
        label=label,
        text=text,
        chars=len(text),
        utf8_bytes=len(text.encode("utf-8")),
        heuristic_tokens=estimate_tokens(text),
    )


def compare_forms(*, eap: str, natural: Optional[str] = None) -> list[Measurement]:
    forms: list[tuple[str, str]] = []
    if natural is not None:
        forms.append(("natural", natural))
    forms.append(("eap", eap))
    forms.append(("ait", encode_eap(eap)))
    return [measure_text(text, label) for label, text in forms]


def estimate_tokens(text: str) -> int:
    tokens = 0
    for chunk in re.findall(r"[A-Za-z0-9_]+|[^\sA-Za-z0-9_]", text):
        if re.fullmatch(r"[A-Za-z0-9_]+", chunk):
            tokens += max(1, (len(chunk) + 3) // 4)
        else:
            tokens += 1 if ord(chunk) <= 0xFFFF else 2
    return tokens

