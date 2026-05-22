from __future__ import annotations

import argparse
import json

from .codec import build_ait, build_eap, decode_to_japanese
from .core import decode_ait, encode_eap
from .dictionary import default_dictionary
from .meter import compare_forms, measure_text


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


def _add_build_args(command: argparse.ArgumentParser) -> None:
    command.add_argument("--domain", required=True)
    command.add_argument("--action", required=True)
    command.add_argument("--target", type=int, required=True)
    command.add_argument("--priority", type=int, default=5)


if __name__ == "__main__":
    main()
