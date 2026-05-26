from __future__ import annotations

import argparse
import json
import sys

from .codec import build_ait, build_eap, decode_to_japanese
from .core import decode_ait, encode_eap
from .dictionary import default_dictionary
from .learner import Learner, ValidationError, validate_ait
from .meter import compare_forms, estimate_tokens, measure_text


def main() -> None:
    parser = argparse.ArgumentParser(description="AI Instruction Tape tools.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    encode_cmd = subparsers.add_parser("encode", help="Encode EAP assembly to AIT.")
    encode_cmd.add_argument("eap")

    decode_cmd = subparsers.add_parser("decode", help="Decode AIT to EAP assembly.")
    decode_cmd.add_argument("ait")

    decode_ja_cmd = subparsers.add_parser("decode-ja", help="Decode AIT/EAP to Japanese without LLM.")
    decode_ja_cmd.add_argument("packet")

    build_eap_cmd = subparsers.add_parser("build-eap", help="Build EAP from structured parameters.")
    _add_build_args(build_eap_cmd)
    build_eap_cmd.add_argument("--direction", default=">", choices=[">", "<", "="])

    build_ait_cmd = subparsers.add_parser("build-ait", help="Build AIT from structured parameters.")
    _add_build_args(build_ait_cmd)

    meter_cmd = subparsers.add_parser("meter", help="Compare natural/EAP/AIT size.")
    meter_cmd.add_argument("--eap", required=True)
    meter_cmd.add_argument("--natural")

    raw_meter_cmd = subparsers.add_parser("measure", help="Measure raw text.")
    raw_meter_cmd.add_argument("text")
    raw_meter_cmd.add_argument("--label", default="text")

    subparsers.add_parser("check", help="Check default dictionary ambiguity.")

    # ── auto: lookup or LLM-generate ─────────────────────────────────────────
    auto_cmd = subparsers.add_parser(
        "auto",
        help="Look up or auto-generate AIT for a natural-language instruction.",
    )
    auto_cmd.add_argument("natural", help="Natural-language instruction to encode.")
    auto_cmd.add_argument(
        "--claude-bin", default="claude", metavar="PATH",
        help="Path to the Claude CLI binary (default: 'claude').",
    )
    auto_cmd.add_argument(
        "--json", action="store_true", dest="as_json",
        help="Output full entry as JSON.",
    )

    # ── learn: manual registration ────────────────────────────────────────────
    learn_cmd = subparsers.add_parser(
        "learn",
        help="Manually register a natural → AIT mapping.",
    )
    learn_cmd.add_argument("natural", help="Natural-language instruction.")
    learn_cmd.add_argument("ait_code", metavar="ait", help="AIT code to register.")

    # ── stats: ROI summary ────────────────────────────────────────────────────
    stats_cmd = subparsers.add_parser(
        "stats",
        help="Show learned dictionary statistics and ROI.",
    )
    stats_cmd.add_argument(
        "--list", action="store_true", dest="list_entries",
        help="Also list all learned entries.",
    )

    # ── validate: standalone code check ──────────────────────────────────────
    validate_cmd = subparsers.add_parser(
        "validate",
        help="Validate an AIT code without registering it.",
    )
    validate_cmd.add_argument("ait_code", metavar="ait", help="AIT code to validate.")

    args = parser.parse_args()

    if args.command == "encode":
        print(encode_eap(args.eap))
    elif args.command == "decode":
        print(decode_ait(args.ait).to_eap())
    elif args.command == "decode-ja":
        print(decode_to_japanese(args.packet))
    elif args.command == "build-eap":
        print(
            build_eap(
                domain=args.domain,
                action=args.action,
                target=args.target,
                priority=args.priority,
                direction=args.direction,
            )
        )
    elif args.command == "build-ait":
        print(
            build_ait(
                domain=args.domain,
                action=args.action,
                target=args.target,
                priority=args.priority,
            )
        )
    elif args.command == "meter":
        results = compare_forms(eap=args.eap, natural=args.natural)
        print(json.dumps([result.to_dict() for result in results], ensure_ascii=False, indent=2))
    elif args.command == "measure":
        print(json.dumps(measure_text(args.text, args.label).to_dict(), ensure_ascii=False, indent=2))
    elif args.command == "check":
        errors = default_dictionary().check()
        if errors:
            print(json.dumps(errors, ensure_ascii=False, indent=2))
            raise SystemExit(1)
        print("ok")

    elif args.command == "auto":
        learner = Learner()
        try:
            code, was_hit = learner.auto(args.natural, claude_bin=args.claude_bin)
        except ValidationError as exc:
            print(f"[error] {exc}", file=sys.stderr)
            raise SystemExit(1)
        except RuntimeError as exc:
            print(f"[error] LLM call failed: {exc}", file=sys.stderr)
            raise SystemExit(1)

        if args.as_json:
            entry = learner._data.get(args.natural.strip())
            out = {
                "ait": code,
                "cache_hit": was_hit,
                **(entry.to_dict() if entry else {}),
            }
            print(json.dumps(out, ensure_ascii=False, indent=2))
        else:
            label = "cache hit ✅" if was_hit else "generated + registered 🆕"
            print(f"{code}  [{label}]")

    elif args.command == "learn":
        learner = Learner()
        nat_tokens = estimate_tokens(args.natural.strip())
        try:
            entry = learner.learn(
                args.natural,
                args.ait_code,
                source="manual",
                natural_tokens=nat_tokens,
            )
        except ValidationError as exc:
            print(f"[error] {exc}", file=sys.stderr)
            raise SystemExit(1)
        print(f"✅ registered: {args.natural!r} → {entry.ait}  (eap: {entry.eap})")
        if entry.tokens_per_hit > 0:
            print(f"   saves {entry.tokens_per_hit} tokens/hit  |  payline: {entry.payline} hits")

    elif args.command == "stats":
        learner = Learner()
        s = learner.stats()
        print("=== AIT Learned Dictionary Stats ===")
        print(f"  Entries       : {s['entries']}")
        print(f"  Total hits    : {s['total_hits']}")
        print(f"  Tokens saved  : {s['total_tokens_saved']:,}")
        print(f"  Paid off      : {s['entries_paid_off']} ✅  /  pending: {s['entries_pending']} 📈")
        if args.list_entries:
            print()
            entries = learner.list_entries()
            if not entries:
                print("  (no entries yet)")
            else:
                for e in entries:
                    print(
                        f"  {e['ait']}  {e['roi_status']:12s} hits={e['hits']:3d}"
                        f"  save={e['tokens_per_hit']}tok/hit"
                        f"  [{e['source']}]  {e['natural'][:60]}"
                    )

    elif args.command == "validate":
        try:
            code = validate_ait(args.ait_code)
            from .core import decode_ait as _decode
            packet = _decode(code)
            print(f"✅ valid: {code}")
            print(f"   domain={packet.domain}  target={packet.target}"
                  f"  action={packet.action}  priority={packet.priority}")
        except ValidationError as exc:
            print(f"❌ invalid: {exc}", file=sys.stderr)
            raise SystemExit(1)


def _add_build_args(command: argparse.ArgumentParser) -> None:
    command.add_argument("--domain", required=True)
    command.add_argument("--action", required=True)
    command.add_argument("--target", type=int, required=True)
    command.add_argument("--priority", type=int, default=5)


if __name__ == "__main__":
    main()
