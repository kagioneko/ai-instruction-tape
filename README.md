# AI Instruction Tape (AIT)

> A tiny instruction tape for AI-agent packets.

AIT is the machine-ish layer below EAP.

```text
Natural language:
  過去ログ4番のXSSを超ガチで見て

EAP assembly:
  >SEC:XSS #ctx4 !9

AIT instruction tape:
  s4x9
```

The goal is not visual flair. The goal is short, tokenizer-friendly ASCII.

## Layering

```text
Natural language  human readable, verbose
EAP               assembly-like structured packet
AIT               compact fixed-position instruction tape
```

## AIT v0 Grammar

```text
packet := domain target action priority
```

Each field is one ASCII character:

```text
D T A P
```

- `D`: domain code
- `T`: target id in base36 (`0-9a-z`)
- `A`: action code
- `P`: priority (`1-9`)

Example:

```text
s4x9
```

Means:

```text
security / ctx4 / xss / priority9
```

## Default Dictionary

Domains:

```text
s security
d data
r refactor
p prediction
g gravity
n neurostate
o observability
```

Actions:

```text
x xss
m summarize
f fix
a audit
b branch
q query
u update
v validate
```

## Install

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
```

## CLI

Encode EAP to AIT:

```bash
ait encode '>SEC:XSS #ctx4 !9'
# s4x9
```

Decode AIT to EAP:

```bash
ait decode s4x9
# >SEC:XSS #ctx4 !9
```

Decode AIT/EAP to Japanese without any LLM:

```bash
ait decode-ja s4x9
# コンテキスト4に対して、セキュリティ領域のXSS検証を実行します。優先度は最高です。
```

Build EAP/AIT directly from UI-style parameters:

```bash
ait build-eap --domain security --action xss --target 4 --priority 9
# >SEC:XSS #ctx4 !9

ait build-ait --domain security --action xss --target 4 --priority 9
# s4x9
```

Measure compactness:

```bash
ait meter --natural "過去ログ4番のXSSを超ガチで見て" --eap '>SEC:XSS #ctx4 !9'
```

Check dictionary ambiguity:

```bash
ait check
```

## Multi-Agent Tape Example

Parent agents can instruct child agents with four-character AIT packets. No LLM
is needed for routing, decoding, or logging.

```bash
python examples/multi_agent_tape.py
```

Example output:

```text
parent -> security-child: s4x9
log: コンテキスト4に対して、セキュリティ領域のXSS検証を実行します。優先度は最高です。
result: {'ok': True, 'target': '#ctx4', 'vulnerable': True, 'finding': 'script_tag_detected'}
```

## Token Cost Benchmark

AIT is measured against Natural Language (JA/EN), EAP Unicode, and EAP ASCII
across 14 tasks and 5 categories (cl100k_base tokenizer).

| Format | Avg tokens/task | vs JA |
|--------|---------------:|------:|
| Natural Lang (JA) | 33.5 | — |
| Natural Lang (EN) | 16.4 | −51% |
| EAP Unicode | 24.7 | −26% |
| EAP ASCII | 12.8 | −62% |
| **AIT** | **5.4** | **−84%** |

At 1,000 agentic loops: **469,000 tokens (JA) → 76,000 tokens (AIT)**.

![AIT Benchmark v3](benchmarks/ait_benchmark_v3.png)

→ Full results and reproduction steps: [`benchmarks/results_v3.md`](benchmarks/results_v3.md)

## Design Notes

AIT only works if both sides share the dictionary. This is a feature, not a bug.
Like machine code, compactness comes from prior agreement.

For debug logs, use EAP. For compact transport, use AIT.

AIT intentionally does not call LLM APIs for encode/decode. Human-readable
Japanese logs are produced by static Python dictionaries, and command encoding
is built from structured parameters rather than free-form natural language.

## License

MIT
