# Next Run Notes

Last updated: 2026-06-15

## Current Best Result

Best useful run so far is the strengthened baseline/full-AIT style, not mixed or
curriculum.

Reference score:

```text
valid: 200/200 (100.0%)
exact: 175/200 (87.5%)
field_domain: 200/200 (100.0%)
field_target: 183/200 (91.5%)
field_action: 186/200 (93.0%)
field_priority: 200/200 (100.0%)
```

## Failed Branches

### Mixed auxiliary task run

Problem: target/action auxiliary rows caused one-character outputs during full
AIT evaluation.

Observed pattern:

```text
gold=pex1 pred=x
gold=nsb5 pred=b
gold=dea1 pred=e
```

Conclusion: mixing `natural -> target` and `natural -> action` directly into the
same fine-tune confuses output length for a 0.5B model.

### Curriculum run

Problem: output returned to mostly valid 4-character AIT, but target/priority
mapping degraded badly.

Reference score:

```text
valid: 194/200 (97.0%)
exact: 82/200 (41.0%)
field_target: 118/200 (59.0%)
field_action: 149/200 (74.5%)
field_priority: 146/200 (73.0%)
```

Conclusion: the mixed warm-up still damages the representation, and the full-AIT
cleanup stage does not recover enough.

## Next Recommendation

Return to full-AIT-only training and increase data volume.

Use the baseline notebook:

```text
experiments/0_5b_tape_compiler/colab_lora_0_5b.ipynb
```

Try:

```python
TRAIN_ROWS = 5000
EVAL_ROWS = 200
EPOCHS = 3
```

Keep eval as full AIT only.

Do not use mixed or curriculum for the next run.

## What To Watch

Primary metrics:

```text
exact
field_target
field_action
```

Goal:

```text
valid >= 99%
exact >= 90%
field_target >= 95%
field_action >= 95%
```

## After Download

Download from Colab:

```python
from google.colab import files

files.download("/content/ai-instruction-tape/experiments/0_5b_tape_compiler/predictions_colab.txt")
files.download("/content/ai-instruction-tape/experiments/0_5b_tape_compiler/data/eval.jsonl")
```

Then run local scoring:

```powershell
$env:PYTHONPATH='src'
python experiments/0_5b_tape_compiler/evaluate_outputs.py --gold <eval.jsonl> --pred <predictions_colab.txt>
python experiments/0_5b_tape_compiler/analyze_errors.py --gold <eval.jsonl> --pred <predictions_colab.txt> --out experiments/0_5b_tape_compiler/error_report_next.csv
```

