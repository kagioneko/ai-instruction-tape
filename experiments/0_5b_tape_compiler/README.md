# 0.5B Tape Compiler Experiment

This experiment tests whether a very small model can act as an AIT compiler:

```text
natural instruction -> 4-character AIT packet
```

The target is not deep reasoning. The target is stable protocol emission.

## Why 0.5B May Work

AIT v0 is a fixed-position ASCII packet:

```text
D T A P
```

- `D`: domain code
- `T`: target id in base36
- `A`: action code
- `P`: priority 1-9

That gives the model a tiny output space and lets evaluation be deterministic.

## Files

- `generate_dataset.py` creates JSONL training/eval examples.
- `evaluate_outputs.py` scores model outputs with the real AIT parser.
- `analyze_errors.py` prints and exports exact-match failures.
- `sample_eval.jsonl` is a small hand-checkable eval set.
- `COLAB.md` explains the Google Colab path.
- `colab_lora_0_5b.ipynb` runs dataset generation, LoRA fine-tuning, and scoring.

Generated datasets should go in `data/` and are ignored by git.

## Google Colab

For a GPU notebook run, open:

```text
experiments/0_5b_tape_compiler/colab_lora_0_5b.ipynb
```

See `COLAB.md` for the quickstart and score interpretation.

## Suggested First Run

```bash
set PYTHONPATH=src
python experiments/0_5b_tape_compiler/generate_dataset.py --out experiments/0_5b_tape_compiler/data/train.jsonl --count 500
python experiments/0_5b_tape_compiler/generate_dataset.py --out experiments/0_5b_tape_compiler/data/eval.jsonl --count 100 --seed 7
```

Each JSONL row uses an instruction-tuning shape:

```json
{"instruction":"Encode the natural-language instruction as AIT v0. Output only the 4-character code.","input":"scan context 4 for xss urgently","output":"s4x9","meta":{"eap":">SEC:XSS #ctx4 !9"}}
```

## Evaluation Contract

The model must output exactly one valid AIT code.

Good:

```text
s4x9
```

Bad:

```text
The AIT code is s4x9.
```

Score outputs with:

```bash
set PYTHONPATH=src
python experiments/0_5b_tape_compiler/evaluate_outputs.py --gold experiments/0_5b_tape_compiler/data/eval.jsonl --pred predictions.txt
```

`predictions.txt` should contain one model output per line.

Analyze failures with:

```bash
set PYTHONPATH=src
python experiments/0_5b_tape_compiler/analyze_errors.py --gold experiments/0_5b_tape_compiler/data/eval.jsonl --pred predictions.txt --out experiments/0_5b_tape_compiler/error_report.csv
```

## Metrics

- `exact`: output exactly matches the gold AIT packet
- `valid`: output parses as AIT v0
- `field_*`: domain, target, action, priority agreement

Useful early thresholds:

- 95%+ valid means the small model learned the protocol shape.
- 80%+ exact means the natural-language mapping is already useful.
- Low exact but high valid means the grammar is learned, but examples or labels need work.

## Fine-Tune Shape

Start with LoRA or QLoRA on a 0.5B instruct model. Keep the task narrow:

```text
system: You are an AIT v0 compiler. Output only one 4-character lowercase ASCII code.
user: scan context 4 for xss urgently
assistant: s4x9
```

Do not train it to explain AIT at first. Explanation increases output drift.
