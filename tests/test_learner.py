"""Tests for the AIT learner / auto-dictionary module."""
from __future__ import annotations

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from ait.learner import (
    GENERATION_COST_TOKENS,
    LearnedEntry,
    Learner,
    ValidationError,
    generate_ait,
    validate_ait,
)
from ait.dictionary import default_dictionary


# ── validate_ait ─────────────────────────────────────────────────────────────

class TestValidateAit:
    def test_valid_code(self):
        assert validate_ait("s4x9") == "s4x9"

    def test_strips_whitespace(self):
        assert validate_ait("  s4x9  ") == "s4x9"

    def test_uppercased_is_lowercased(self):
        # validate_ait lowercases before checking
        assert validate_ait("S4X9") == "s4x9"

    def test_too_short(self):
        with pytest.raises(ValidationError, match="4 lowercase"):
            validate_ait("s4x")

    def test_too_long(self):
        with pytest.raises(ValidationError, match="4 lowercase"):
            validate_ait("s4x99")

    def test_unknown_domain(self):
        with pytest.raises(ValidationError, match="Grammar check"):
            validate_ait("z4x9")  # 'z' not a known domain

    def test_unknown_action(self):
        with pytest.raises(ValidationError, match="Grammar check"):
            validate_ait("s4z9")  # 'z' not a known action

    def test_priority_zero_is_invalid(self):
        with pytest.raises(ValidationError):
            validate_ait("s4x0")

    def test_all_valid_domain_codes(self):
        d = default_dictionary()
        for code in d.domains:
            # Use action 'x' (xss), target '0', priority '5'
            result = validate_ait(f"{code}0x5")
            assert len(result) == 4

    def test_all_valid_action_codes(self):
        d = default_dictionary()
        for code in d.actions:
            result = validate_ait(f"s0{code}5")
            assert len(result) == 4


# ── LearnedEntry ─────────────────────────────────────────────────────────────

class TestLearnedEntry:
    def test_payline_calculation(self):
        entry = LearnedEntry(ait="s4x9", eap=">SEC:XSS #ctx4 !9",
                             cost_tokens=150, tokens_per_hit=30)
        assert entry.payline == 5  # ceil(150/30)

    def test_payline_none_when_no_savings(self):
        entry = LearnedEntry(ait="s4x9", eap=">SEC:XSS #ctx4 !9",
                             cost_tokens=150, tokens_per_hit=0)
        assert entry.payline is None

    def test_roi_status_pending(self):
        entry = LearnedEntry(ait="s4x9", eap=">SEC:XSS #ctx4 !9",
                             hits=2, cost_tokens=150, tokens_per_hit=30)
        assert "📈" in entry.roi_status

    def test_roi_status_paid_off(self):
        entry = LearnedEntry(ait="s4x9", eap=">SEC:XSS #ctx4 !9",
                             hits=10, cost_tokens=150, tokens_per_hit=30)
        assert "✅" in entry.roi_status


# ── Learner ───────────────────────────────────────────────────────────────────

@pytest.fixture
def tmp_learner(tmp_path):
    return Learner(path=tmp_path / "learned.json")


class TestLearner:
    def test_lookup_miss(self, tmp_learner):
        assert tmp_learner.lookup("some instruction") is None

    def test_learn_and_lookup(self, tmp_learner):
        tmp_learner.learn("scan context 4 for xss", "s4x9", source="manual")
        result = tmp_learner.lookup("scan context 4 for xss")
        assert result == "s4x9"

    def test_learn_increments_hits(self, tmp_learner):
        tmp_learner.learn("test", "s1x5", source="manual")
        tmp_learner.lookup("test")
        tmp_learner.lookup("test")
        assert tmp_learner._data["test"].hits == 2

    def test_learn_invalid_code_raises(self, tmp_learner):
        with pytest.raises(ValidationError):
            tmp_learner.learn("test", "INVALID", source="manual")

    def test_learn_unknown_domain_raises(self, tmp_learner):
        with pytest.raises(ValidationError):
            tmp_learner.learn("test", "z4x9", source="manual")

    def test_learn_stores_eap(self, tmp_learner):
        tmp_learner.learn("fix ctx7", "r7f8", source="manual")
        entry = tmp_learner._data["fix ctx7"]
        assert "REF" in entry.eap or "r7f8" == entry.ait

    def test_persistence(self, tmp_path):
        learner1 = Learner(path=tmp_path / "l.json")
        learner1.learn("audit ctx1", "s1a9", source="manual")

        learner2 = Learner(path=tmp_path / "l.json")
        assert learner2.lookup("audit ctx1") == "s1a9"

    def test_stats_empty(self, tmp_learner):
        s = tmp_learner.stats()
        assert s["entries"] == 0
        assert s["total_hits"] == 0
        assert s["total_tokens_saved"] == 0

    def test_stats_counts(self, tmp_learner):
        tmp_learner.learn("task a", "s1x9", source="manual")
        tmp_learner.lookup("task a")
        tmp_learner.lookup("task a")
        s = tmp_learner.stats()
        assert s["entries"] == 1
        assert s["total_hits"] == 2

    def test_tokens_saved_calculation(self, tmp_learner):
        # "scan context 1 for xss" is ~5 tokens; "s1x9" is 1 token → saves ~4
        tmp_learner.learn("scan context 1 for xss audit", "s1a9", source="manual")
        entry = tmp_learner._data["scan context 1 for xss audit"]
        assert entry.tokens_per_hit > 0


# ── generate_ait (LLM integration) ───────────────────────────────────────────

class TestGenerateAit:
    def test_valid_llm_response(self):
        with patch("ait.learner._call_llm", return_value="s4x9"):
            result = generate_ait("scan ctx4 for xss at max priority")
        assert result == "s4x9"

    def test_llm_response_with_whitespace_stripped(self):
        with patch("ait.learner._call_llm", return_value="  s4x9  \n"):
            result = generate_ait("scan ctx4 for xss")
        assert result == "s4x9"

    def test_llm_returns_unknown(self):
        with patch("ait.learner._call_llm", return_value="UNKNOWN"):
            with pytest.raises(ValidationError, match="could not map"):
                generate_ait("do the funky chicken")

    def test_llm_returns_invalid_code(self):
        with patch("ait.learner._call_llm", return_value="ZZZZ"):
            with pytest.raises(ValidationError):
                generate_ait("something")

    def test_llm_cli_not_found(self):
        with pytest.raises(RuntimeError, match="not found"):
            generate_ait("test", claude_bin="/nonexistent/claude")

    def test_auto_uses_cache_on_second_call(self, tmp_path):
        learner = Learner(path=tmp_path / "l.json")
        with patch("ait.learner._call_llm", return_value="s4x9") as mock_llm:
            code1, hit1 = learner.auto("scan ctx4 for xss", claude_bin="claude")
            code2, hit2 = learner.auto("scan ctx4 for xss", claude_bin="claude")

        assert code1 == code2 == "s4x9"
        assert not hit1   # first call: miss
        assert hit2       # second call: cache hit
        assert mock_llm.call_count == 1  # LLM called only once!
