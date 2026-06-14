from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from ait.core import AitError, decode_ait


CODE_RE = re.compile(r"^[a-z0-9]{4}$")


def load_gold(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def load_preds(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def packet_or_none(raw: str):
    if not CODE_RE.fullmatch(raw):
        return None
    try:
        return decode_ait(raw)
    except AitError:
        return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gold", required=True, help="Gold JSONL file")
    parser.add_argument("--pred", required=True, help="One model output per line")
    args = parser.parse_args()

    gold = load_gold(Path(args.gold))
    preds = load_preds(Path(args.pred))
    if len(gold) != len(preds):
        raise SystemExit(f"row count mismatch: gold={len(gold)} pred={len(preds)}")

    counts = {
        "total": len(gold),
        "valid": 0,
        "exact": 0,
        "field_domain": 0,
        "field_target": 0,
        "field_action": 0,
        "field_priority": 0,
    }

    for row, pred in zip(gold, preds):
        expected = row["output"]
        expected_packet = decode_ait(expected)
        pred_packet = packet_or_none(pred)
        if pred_packet is None:
            continue
        counts["valid"] += 1
        if pred == expected:
            counts["exact"] += 1
        if pred_packet.domain == expected_packet.domain:
            counts["field_domain"] += 1
        if pred_packet.target == expected_packet.target:
            counts["field_target"] += 1
        if pred_packet.action == expected_packet.action:
            counts["field_action"] += 1
        if pred_packet.priority == expected_packet.priority:
            counts["field_priority"] += 1

    total = counts["total"] or 1
    for key, value in counts.items():
        if key == "total":
            print(f"{key}: {value}")
        else:
            print(f"{key}: {value}/{total} ({value / total:.1%})")


if __name__ == "__main__":
    main()

