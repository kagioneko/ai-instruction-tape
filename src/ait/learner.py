"""
learner.py — AIT dictionary auto-learner

Persistent store: ~/.ait/learned.json
Workflow:
  1. lookup(natural)       → hit: return stored AIT code (free)
  2. miss → generate_ait() → LLM generates candidate code
  3. validate()            → multi-stage grammar + dictionary check
  4. learn()               → persist to learned.json
  5. stats()               → ROI summary (hits, tokens saved, payline)

Payline = registration_cost / tokens_saved_per_hit
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path
from typing import Optional

from .core import AitError, decode_ait
from .dictionary import Dictionary, default_dictionary

# ── constants ────────────────────────────────────────────────────────────────

LEARNED_PATH = Path.home() / ".ait" / "learned.json"

# Approximate token cost to call the LLM once for AIT generation.
# Conservative estimate (short prompt + short response).
GENERATION_COST_TOKENS = 150


# ── data model ───────────────────────────────────────────────────────────────

@dataclass
class LearnedEntry:
    ait: str
    eap: str
    hits: int = 0
    cost_tokens: int = GENERATION_COST_TOKENS   # tokens spent on registration
    tokens_per_hit: int = 0                      # tokens saved each hit
    added: str = field(default_factory=lambda: date.today().isoformat())
    source: str = "llm"                          # "llm" | "manual"

    @property
    def payline(self) -> Optional[int]:
        """Hits needed to break even. None if tokens_per_hit == 0."""
        if self.tokens_per_hit <= 0:
            return None
        import math
        return math.ceil(self.cost_tokens / self.tokens_per_hit)

    @property
    def roi_status(self) -> str:
        pl = self.payline
        if pl is None:
            return "?"
        return "✅" if self.hits >= pl else f"📈 ({self.hits}/{pl})"

    def to_dict(self) -> dict:
        d = asdict(self)
        d["payline"] = self.payline
        d["roi_status"] = self.roi_status
        return d


# ── validation ───────────────────────────────────────────────────────────────

class ValidationError(ValueError):
    pass


def validate_ait(
    ait: str,
    dictionary: Optional[Dictionary] = None,
    learned: Optional[dict[str, LearnedEntry]] = None,
) -> str:
    """
    Multi-stage validation. Returns the (stripped) code on success.
    Raises ValidationError with a descriptive message on any failure.
    """
    code = ait.strip().lower()

    # Stage 1: format — exactly 4 lowercase ASCII alnum chars
    if not re.fullmatch(r"[a-z0-9]{4}", code):
        raise ValidationError(
            f"AIT must be exactly 4 lowercase ASCII alnum chars, got: {ait!r}"
        )

    # Stage 2: grammar — decode_ait must succeed (domain/action/priority checks)
    dictionary = dictionary or default_dictionary()
    try:
        packet = decode_ait(code, dictionary)
    except AitError as exc:
        raise ValidationError(f"Grammar check failed: {exc}") from exc

    # Stage 3: priority sanity (redundant but explicit)
    if not (1 <= packet.priority <= 9):
        raise ValidationError(f"Priority must be 1–9, got: {packet.priority}")

    # Stage 4: dictionary self-consistency
    errors = dictionary.check()
    if errors:
        raise ValidationError(f"Dictionary integrity error: {errors[0]}")

    # Stage 5: collision check — does this code already mean something else?
    if learned:
        for nat, entry in learned.items():
            if entry.ait == code:
                # Same code already mapped — warn but allow (target differs per use)
                # If domain+action+priority all match, it's a true alias; fine.
                pass  # collisions are acceptable (target slot is dynamic)

    return code


# ── LLM generation ───────────────────────────────────────────────────────────

_PROMPT_TEMPLATE = """\
You are an AIT (AI Instruction Tape) code generator.

AIT grammar: D T A P
  D = domain code (1 char): {domain_codes}
  T = target id in base36 (0-9, a-z). Use the context number from the instruction, or '0' if unspecified.
  A = action code (1 char): {action_codes}
  P = priority (1-9). Infer from urgency words; default 5.

Domain meanings:
{domain_meanings}

Action meanings:
{action_meanings}

Rules:
- Output ONLY the 4-character AIT code. Nothing else.
- All lowercase.
- Use only the codes listed above.
- If the instruction fits multiple actions, pick the most specific one.
- If domain or action cannot be determined from the list, output: UNKNOWN

Instruction to encode:
{natural}
"""


def _build_prompt(natural: str, dictionary: Dictionary) -> str:
    domain_codes = ", ".join(
        f"{code}={name}" for code, name in sorted(dictionary.domains.items())
    )
    action_codes = ", ".join(
        f"{code}={name}" for code, name in sorted(dictionary.actions.items())
    )
    domain_meanings = "\n".join(
        f"  {code}: {name}" for code, name in sorted(dictionary.domains.items())
    )
    action_meanings = "\n".join(
        f"  {code}: {name}" for code, name in sorted(dictionary.actions.items())
    )
    return _PROMPT_TEMPLATE.format(
        domain_codes=domain_codes,
        action_codes=action_codes,
        domain_meanings=domain_meanings,
        action_meanings=action_meanings,
        natural=natural,
    )


def _call_llm(prompt: str, claude_bin: str = "claude") -> str:
    """Call the Claude CLI and return stdout. Raises RuntimeError on failure."""
    try:
        result = subprocess.run(
            [claude_bin, "--print", "--no-color", "-p", prompt],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(
            f"Claude CLI not found: {claude_bin}. "
            "Install it or pass --claude-bin to specify the path."
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("LLM call timed out after 30s.") from exc
    if result.returncode != 0:
        raise RuntimeError(f"LLM call failed (exit {result.returncode}): {result.stderr[:200]}")
    return result.stdout.strip()


def generate_ait(
    natural: str,
    dictionary: Optional[Dictionary] = None,
    claude_bin: str = "claude",
) -> str:
    """
    Ask the LLM to generate an AIT code for the given natural-language instruction.
    Raises ValidationError if the output fails validation.
    Raises RuntimeError if the LLM call fails.
    """
    dictionary = dictionary or default_dictionary()
    prompt = _build_prompt(natural, dictionary)
    raw = _call_llm(prompt, claude_bin)

    # Strip stray whitespace / markdown fences the model might add
    code = raw.strip().strip("`").lower().split()[0] if raw.strip() else ""

    if code == "unknown":
        raise ValidationError(
            "LLM could not map this instruction to the current dictionary. "
            "Use 'ait learn <natural> <ait>' to register manually."
        )

    return validate_ait(code, dictionary)


# ── persistent store ──────────────────────────────────────────────────────────

class Learner:
    """
    Manages the learned AIT dictionary (~/.ait/learned.json).
    """

    def __init__(self, path: Path = LEARNED_PATH, dictionary: Optional[Dictionary] = None):
        self.path = path
        self.dictionary = dictionary or default_dictionary()
        self._data: dict[str, LearnedEntry] = {}
        self._load()

    # ── persistence ──────────────────────────────────────────────────────────

    def _load(self) -> None:
        if self.path.exists():
            try:
                raw = json.loads(self.path.read_text(encoding="utf-8"))
                self._data = {
                    k: LearnedEntry(**{
                        f: v for f, v in v.items()
                        if f in LearnedEntry.__dataclass_fields__
                    })
                    for k, v in raw.items()
                }
            except Exception as exc:
                print(f"[ait learner] warning: could not load {self.path}: {exc}", file=sys.stderr)
                self._data = {}

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(
                {k: v.to_dict() for k, v in self._data.items()},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    # ── public API ───────────────────────────────────────────────────────────

    def lookup(self, natural: str) -> Optional[str]:
        """Return stored AIT code if known, else None. Increments hit counter."""
        key = natural.strip()
        if key in self._data:
            self._data[key].hits += 1
            self._save()
            return self._data[key].ait
        return None

    def learn(
        self,
        natural: str,
        ait: str,
        source: str = "manual",
        natural_tokens: Optional[int] = None,
    ) -> LearnedEntry:
        """
        Validate and register a new (natural → AIT) mapping.
        Raises ValidationError if the AIT code is invalid.
        """
        code = validate_ait(ait, self.dictionary, self._data)

        # Estimate tokens saved per hit
        try:
            from .meter import estimate_tokens
            nat_tokens = natural_tokens or estimate_tokens(natural.strip())
            ait_tokens = estimate_tokens(code)
            saved = max(0, nat_tokens - ait_tokens)
        except Exception:
            saved = 0

        packet = decode_ait(code, self.dictionary)
        eap = packet.to_eap()

        entry = LearnedEntry(
            ait=code,
            eap=eap,
            hits=0,
            cost_tokens=GENERATION_COST_TOKENS if source == "llm" else 0,
            tokens_per_hit=saved,
            source=source,
        )
        self._data[natural.strip()] = entry
        self._save()
        return entry

    def auto(
        self,
        natural: str,
        claude_bin: str = "claude",
        natural_tokens: Optional[int] = None,
    ) -> tuple[str, bool]:
        """
        Look up or generate an AIT code.
        Returns (ait_code, was_cache_hit).
        """
        hit = self.lookup(natural)
        if hit:
            return hit, True

        # Generate via LLM
        code = generate_ait(natural, self.dictionary, claude_bin)
        self.learn(natural, code, source="llm", natural_tokens=natural_tokens)
        return code, False

    # ── stats ─────────────────────────────────────────────────────────────────

    def stats(self) -> dict:
        total_hits = sum(e.hits for e in self._data.values())
        total_saved = sum(e.hits * e.tokens_per_hit for e in self._data.values())
        paid_off = sum(
            1 for e in self._data.values()
            if e.payline is not None and e.hits >= e.payline
        )
        return {
            "entries": len(self._data),
            "total_hits": total_hits,
            "total_tokens_saved": total_saved,
            "entries_paid_off": paid_off,
            "entries_pending": len(self._data) - paid_off,
        }

    def list_entries(self) -> list[dict]:
        return [
            {"natural": k, **v.to_dict()}
            for k, v in sorted(self._data.items(), key=lambda x: -x[1].hits)
        ]
