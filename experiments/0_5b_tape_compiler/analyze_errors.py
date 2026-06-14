from __future__ import annotations

import argparse
import csv
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


def decode_or_error(raw: str):
    if not CODE_RE.fullmatch(raw):
        return None, "format"
    try:
        return decode_ait(raw), ""
    except AitError as exc:
        return None, str(exc)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gold", required=True, help="Gold JSONL file")
    parser.add_argument("--pred", required=True, help="One model output per line")
    parser.add_argument("--out", help="Optional CSV report path")
    parser.add_argument("--limit", type=int, default=30, help="Rows to print")
    args = parser.parse_args()

    gold = load_gold(Path(args.gold))
    preds = load_preds(Path(args.pred))
    if len(gold) != len(preds):
        raise SystemExit(f"row count mismatch: gold={len(gold)} pred={len(preds)}")

    errors = []
    field_counts = {"invalid": 0, "domain": 0, "target": 0, "action": 0, "priority": 0}

    for index, (row, pred) in enumerate(zip(gold, preds), start=1):
        expected_code = row["output"]
        expected = decode_ait(expected_code)
        actual, reason = decode_or_error(pred)

        mismatches = []
        if actual is None:
            field_counts["invalid"] += 1
            mismatches.append(f"invalid:{reason}")
        else:
            for field in ("domain", "target", "action", "priority"):
                if getattr(actual, field) != getattr(expected, field):
                    field_counts[field] += 1
                    mismatches.append(field)

        if pred != expected_code:
            errors.append(
                {
                    "index": index,
                    "input": row["input"],
                    "gold": expected_code,
                    "pred": pred,
                    "mismatches": ",".join(mismatches) if mismatches else "format_or_extra_text",
                    "gold_eap": row.get("meta", {}).get("eap", expected.to_eap()),
                    "pred_eap": actual.to_eap() if actual is not None else "",
                }
            )

    total = len(gold)
    print(f"total: {total}")
    print(f"errors: {len(errors)} ({len(errors) / total:.1%})")
    for field, count in field_counts.items():
        print(f"{field}: {count}")

    if errors:
        print("\nTop errors:")
        for row in errors[: args.limit]:
            print(
                f"{row['index']:>3} gold={row['gold']} pred={row['pred']} "
                f"mismatch={row['mismatches']} input={row['input']}"
            )

    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["index", "input", "gold", "pred", "mismatches", "gold_eap", "pred_eap"],
            )
            writer.writeheader()
            writer.writerows(errors)
        print(f"\nwrote: {out}")


if __name__ == "__main__":
    main()

