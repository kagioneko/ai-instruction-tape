# Google Colab Quickstart

Use this when you want to run the 0.5B AIT compiler experiment without setting
up a local GPU environment.

## Recommended Colab Runtime

- Runtime type: Python 3
- Hardware accelerator: T4 GPU or better

## Notebook

Open the baseline notebook:

```text
experiments/0_5b_tape_compiler/colab_lora_0_5b.ipynb
```

For the mixed auxiliary-task run, open:

```text
experiments/0_5b_tape_compiler/colab_lora_0_5b_mixed.ipynb
```

The notebook does four things:

1. Clones and installs `ai-instruction-tape`.
2. Generates synthetic AIT compiler train/eval JSONL.
3. Fine-tunes a small instruct model with LoRA.
4. Writes predictions and scores them with `evaluate_outputs.py`.

## Default Model

The notebook defaults to:

```text
Qwen/Qwen2.5-0.5B-Instruct
```

This is small enough for a first T4 run. You can change `MODEL_ID` in the first
config cell.

## Expected Runtime

For the mixed notebook default settings:

- train rows: 2,400
- eval rows: 200
- epochs: 3
- train mode: mixed full-AIT plus target/action auxiliary rows

Expect a short exploratory run rather than a polished benchmark. The first goal
is to see whether the model learns valid 4-character protocol emission.

## Result Files

The notebook writes:

```text
experiments/0_5b_tape_compiler/data/train.jsonl
experiments/0_5b_tape_compiler/data/eval.jsonl
experiments/0_5b_tape_compiler/predictions_colab.txt
experiments/0_5b_tape_compiler/ait-0_5b-lora/
```

`data/`, prediction files, and adapter outputs are ignored by git.

The final notebook cell downloads:

```text
predictions_colab.txt
eval.jsonl
```

## Reading Scores

The most important scores are:

- `valid`: the model learned the AIT shape and dictionary.
- `exact`: the model matched the full gold packet.
- `field_*`: which part failed when exact is low.

Interpretation:

- High valid, low exact: the protocol shape is learned; improve data diversity.
- Low valid: reduce output drift, train longer, or make prompts stricter.
- Low target only: add more context-number phrasing examples.
