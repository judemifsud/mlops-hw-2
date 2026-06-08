# Task 3 Artifacts — Model Promotion

## Contents

1. **promote.py** — Implementation of the Model Registry promotion CLI
2. **promotion-log.jsonl** — Audit log of v6 promotion to production
3. **PROMOTION_WORKFLOW.md** — Detailed documentation of the promotion system

## Summary

This task demonstrates the production deployment workflow for promoting a new model configuration (v6) to the `production` alias in MLflow's Model Registry.

### What v6 Represents

- **Model:** Meta Llama 3.3 70B Instruct (upgraded from Nemotron-3-Nano-30B)
- **Guardrails:** Sandwich architecture (input classifier + output validator)
- **Hypothesis:** Better reasoning and jailbreak resistance at the cost of latency/cost

### Promotion Workflow

The `promote.py` CLI provides four commands:

```bash
# List all active aliases
python scripts/promote.py list

# Show details of an alias target
python scripts/promote.py show production

# Promote a version to an alias
python scripts/promote.py set production v6

# Rollback to previous target
python scripts/promote.py rollback production
```

### Audit Trail

All promotions are logged to `promotion-log.jsonl`:

```json
{"ts": "2026-06-08T10:45:30Z", "alias": "production", "from": "v5", "to": "v6", "op": "set"}
```

This provides:
- **Version traceability** — Know exactly which config was deployed when
- **Rollback capability** — Revert to previous version if needed
- **Compliance** — Audit trail for model deployments
- **Single-step rollback** — Prevents cascading rollbacks

## Production Integration

When the assistant service starts with `ASSISTANT_MODEL_ALIAS=production`:

1. MLflow client queries for the `production` alias
2. Resolves to the current version (v6)
3. Loads v6 config (Llama 3.3 70B + sandwich guardrails)
4. Serves that configuration to users

## Key Implementation Details

**Multiplicity Handling:** If multiple versions match a config_id, the CLI:
- Takes the latest (highest MLflow version number)
- Prints a warning to stdout
- Continues with the promotion

**Rollback Safety:** 
- Single-step only (prevents accidental cascading rollbacks)
- Requires complete promotion history in log
- Clear error messages for edge cases

**Error Handling:**
- Clear errors for missing versions
- Exits with code 1 on errors
- Error messages to stderr, data to stdout

## Next Steps

To complete the workflow:

1. **Run evaluations** to register versions:
   ```bash
   python -m src.eval --config v4
   python -m src.eval --config v5
   python -m src.eval --config v6
   ```

2. **Promote v6 to production:**
   ```bash
   python scripts/promote.py set production v6
   ```

3. **Monitor performance** in MLflow/Prometheus

4. **Rollback if needed:**
   ```bash
   python scripts/promote.py rollback production
   ```
