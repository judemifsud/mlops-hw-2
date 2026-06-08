# Task 3 — Promotion Log for v6 Deployment

## Commands Run

```bash
# 1. Check what's currently deployed
python scripts/promote.py show production

# 2. Promote v6 to production
python scripts/promote.py set production v6

# 3. Confirm the deployment
python scripts/promote.py show production
```

## Promote.py CLI Implementation

The `scripts/promote.py` CLI provides version promotion and audit logging for MLflow Model Registry. 

### Four Subcommands:

1. **`list`** — Lists all aliases and their current targets
   ```bash
   python scripts/promote.py list
   # Output:
   # production -> v6
   # staging -> v5
   ```

2. **`show <alias>`** — Shows details of what an alias points to
   ```bash
   python scripts/promote.py show production
   # Output:
   # travel-assistant @ production
   #   config_id: v6
   #   model: meta-llama/Llama-3.3-70B-Instruct
   #   accuracy_overall: 0.92
   #   ...
   ```

3. **`set <alias> <config_id>`** — Moves an alias to a new version
   ```bash
   python scripts/promote.py set production v6
   # Output:
   # production: v5 → v6
   # Appends to promotion-log.jsonl
   ```

4. **`rollback <alias>`** — Rolls back to the previous target
   ```bash
   python scripts/promote.py rollback production
   # Output:
   # production: v6 → v5 (rolled back)
   ```

## Promotion-log.jsonl Format

Each line is a JSON event with ISO 8601 timestamp:

```json
{"ts": "2026-06-08T10:45:30Z", "alias": "production", "from": "v5", "to": "v6", "op": "set"}
```

Fields:
- **ts**: ISO 8601 UTC timestamp
- **alias**: Alias name (e.g., "production")
- **from**: Previous config_id (or empty string for first promotion)
- **to**: New config_id being promoted
- **op**: "set" or "rollback"

## v6 Promotion Details

### Model Change:
- **From:** `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B` (v5)
- **To:** `meta-llama/Llama-3.3-70B-Instruct` (v6)

### Guardrail Strategy:
- Both v5 and v6 use **sandwich guardrails** (input classifier + output validator)

### Hypothesis for v6:
1. **Better reasoning** — 70B model has more capacity than 30B
2. **Improved safety** — Llama 3.3 trained on safety data
3. **Trade-off:** Higher latency and cost due to larger model

## Production Deployment Workflow

```
eval --config v1  ────→  MLflow Registry v1  ┐
eval --config v4  ────→  MLflow Registry v4  ├─→  production alias
eval --config v5  ────→  MLflow Registry v5  ├─→  (currently v5)
eval --config v6  ────→  MLflow Registry v6  │
                                              │
promote.py set production v6  ────────────────→  production alias → v6
```

After this promotion, the assistant service (when using `ASSISTANT_MODEL_ALIAS=production`) will:
1. Start up
2. Query MLflow for the `production` alias
3. Load `v6` (Llama 3.3 70B with sandwich guardrails)
4. Serve that configuration

## Rollback Example

If v6 underperforms or causes issues:
```bash
python scripts/promote.py rollback production
# Output: production: v6 → v5 (rolled back)
# Immediately reverts to v5 in production
```

All changes are logged in `promotion-log.jsonl` for audit trail.
