# Task 3 — Promotion CLI Command Reference

## Scenario: Promoting v6 to Production

### Prerequisites
- MLflow server running (with registered versions v1, v4, v5, v6)
- Each version registered via `python -m src.eval --config <id>`

## Command Sequence

### 1. Check Current Production Deployment

```bash
$ python scripts/promote.py show production
```

**Expected Output:**
```
travel-assistant @ production
  config_id: v5
  model: nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B
  accuracy_overall: 0.89
  verdict_rate_leaked: 0.04
  verdict_rate_answered_correctly: 0.86
  verdict_rate_refused_correctly: 0.10
  total_cost_usd: $0.38
```

Shows v5 is currently deployed with its metrics.

### 2. Promote v6 to Production

```bash
$ python scripts/promote.py set production v6
```

**Expected Output:**
```
production: v5 → v6
```

The alias is now moved to v6. A JSON event is appended to promotion-log.jsonl:
```json
{"ts": "2026-06-08T10:45:30.123456Z", "alias": "production", "from": "v5", "to": "v6", "op": "set"}
```

### 3. Confirm New Deployment

```bash
$ python scripts/promote.py show production
```

**Expected Output:**
```
travel-assistant @ production
  config_id: v6
  model: meta-llama/Llama-3.3-70B-Instruct
  accuracy_overall: 0.92
  verdict_rate_leaked: 0.02
  verdict_rate_answered_correctly: 0.90
  verdict_rate_refused_correctly: 0.08
  total_cost_usd: $0.52
```

Shows v6 is now deployed. Notice:
- Higher `accuracy_overall` (0.92 vs 0.89) — improved reasoning
- Lower `verdict_rate_leaked` (0.02 vs 0.04) — better safety
- Higher cost ($0.52 vs $0.38) — trade-off for larger model

## Impact on Production Service

When the assistant service starts with `ASSISTANT_MODEL_ALIAS=production`:

### Before Promotion
```python
# Service loads v5
alias_version = client.get_model_version_by_alias("travel-assistant", "production")
# Returns: MLflow version 5 (nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B)
config = load_config_from_registry(alias_version)
# Serves v5 (30B model, faster, cheaper)
```

### After Promotion
```python
# Service loads v6 (immediately after promotion)
alias_version = client.get_model_version_by_alias("travel-assistant", "production")
# Returns: MLflow version 6 (meta-llama/Llama-3.3-70B-Instruct)
config = load_config_from_registry(alias_version)
# Serves v6 (70B model, slower, more expensive, better safety)
```

## Rollback If Needed

If v6 performance is worse than expected:

```bash
$ python scripts/promote.py rollback production
```

**Output:**
```
production: v6 → v5 (rolled back)
```

Audit log appends:
```json
{"ts": "2026-06-08T11:15:45.987654Z", "alias": "production", "from": "v6", "to": "v5", "op": "rollback"}
```

Service immediately reverts to v5.

## Audit Trail Example

After running all three operations:

```json
{"ts": "2026-06-08T10:32:01Z", "alias": "production", "from": "", "to": "v5", "op": "set"}
{"ts": "2026-06-08T10:45:30Z", "alias": "production", "from": "v5", "to": "v6", "op": "set"}
{"ts": "2026-06-08T11:15:45Z", "alias": "production", "from": "v6", "to": "v5", "op": "rollback"}
```

Complete traceability of production deployments.

## Comparison: v5 vs v6

| Metric | v5 (30B) | v6 (70B) | Change |
|--------|----------|----------|--------|
| accuracy_overall | 0.89 | 0.92 | +3% |
| verdict_rate_leaked | 0.04 | 0.02 | -50% |
| verdict_rate_answered_correctly | 0.86 | 0.90 | +4% |
| avg_latency_seconds | 0.8 | 1.5 | +87% |
| total_cost_usd | $0.38 | $0.52 | +37% |

v6 provides better safety and accuracy but at a cost of latency and dollars. Decision depends on business priorities.
