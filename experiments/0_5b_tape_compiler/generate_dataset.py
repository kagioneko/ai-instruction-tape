from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

from ait.codec import build_ait, build_eap
from ait.dictionary import default_dictionary


INSTRUCTION = (
    "Encode the natural-language instruction as AIT v0. "
    "Output only the 4-character code."
)

DOMAIN_PHRASES = {
    "security": ["security", "sec", "vulnerability", "attack surface"],
    "data": ["data", "dataset", "records", "table"],
    "refactor": ["code", "module", "implementation", "function"],
    "prediction": ["prediction", "forecast", "branch estimate", "future path"],
    "gravity": ["gravity", "semantic gravity", "attractor", "pull"],
    "neurostate": ["neurostate", "mood state", "stress state", "cognitive state"],
    "observability": ["observability", "logs", "timeline", "metrics"],
}

ACTION_PHRASES = {
    "xss": ["check xss", "scan for xss", "test xss", "find xss", "probe xss", "xss scan"],
    "summarize": ["summarize", "make a summary", "compress", "brief", "condense", "outline"],
    "fix": ["fix", "repair", "patch", "correct", "resolve bug", "apply fix"],
    "audit": ["audit", "review", "inspect", "check", "manual review", "read through"],
    "branch": ["branch", "split path", "make branch", "fork plan", "create branch", "branch off"],
    "query": ["query", "look up", "search", "ask", "retrieve", "find info"],
    "update": ["update", "refresh", "change", "rewrite", "revise", "modify"],
    "validate": ["validate", "verify", "confirm", "test", "check validity", "run validation"],
}

URGENCY = {
    1: ["whenever", "low priority", "not urgent"],
    2: ["later", "minor", "low urgency"],
    3: ["soonish", "normal-low", "when possible"],
    4: ["normal", "regular", "standard"],
    5: ["default priority", "normally", ""],
    6: ["important", "fairly soon", "medium-high"],
    7: ["high priority", "soon", "please prioritize"],
    8: ["urgent", "asap", "quickly"],
    9: ["critical", "right now", "highest priority"],
}

TEMPLATES = [
    "{action} in {domain} context {target} {urgency}",
    "for ctx{target}, {action} the {domain} area {urgency}",
    "{urgency} please {action} {domain} item {target}",
    "context #{target}: {domain} {action} {urgency}",
    "take {domain} ctx {target} and {action} it {urgency}",
    "{action} {domain} target {target} {urgency}",
    "{domain} #{target} needs {action} {urgency}",
    "{urgency} run {action} on {domain} ctx-{target}",
    "{action} the {domain} entry numbered {target} {urgency}",
    "{domain} slot {target}: {action} {urgency}",
    "ログ{target}番の{domain}を{action} {urgency}",
    "{target}番の{domain}コンテキストを{action} {urgency}",
]


def make_example(rng: random.Random) -> dict:
    dictionary = default_dictionary()
    domain = rng.choice(list(dictionary.domains.values()))
    action = rng.choice(list(dictionary.actions.values()))
    target = rng.randint(0, 35)
    priority = rng.randint(1, 9)

    natural = rng.choice(TEMPLATES).format(
        domain=rng.choice(DOMAIN_PHRASES[domain]),
        action=rng.choice(ACTION_PHRASES[action]),
        target=target,
        urgency=rng.choice(URGENCY[priority]),
    )
    natural = " ".join(natural.split())

    ait = build_ait(domain=domain, action=action, target=target, priority=priority)
    eap = build_eap(domain=domain, action=action, target=target, priority=priority)
    return {
        "instruction": INSTRUCTION,
        "input": natural,
        "output": ait,
        "meta": {
            "eap": eap,
            "domain": domain,
            "action": action,
            "target": target,
            "priority": priority,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, help="Output JSONL path")
    parser.add_argument("--count", type=int, default=500)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    rng = random.Random(args.seed)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        for _ in range(args.count):
            f.write(json.dumps(make_example(rng), ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
