from __future__ import annotations

import argparse
import json

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


if __name__ == "__main__":
    main()

