# Task 2 Implementation Verification

## Implementation Complete: scripts/promote.py

### Functions Implemented:

1. **cmd_set(args)** ✓
   - Finds MLflow versions by `config_id` tag using `search_model_versions`
   - Handles multiplicity (0, 1, 2+ matches):
     - 0 matches: prints error, exits with sys.exit(1)
     - 1 match: uses it
     - 2+ matches: prints warning with version list, uses latest
   - Gets current alias target via `get_model_version_by_alias` (handles RestException)
   - Assigns alias via `set_registered_model_alias`
   - Appends JSON event to `promotion-log.jsonl` with ISO 8601 timestamp
   - Prints summary: `"alias: (unset) → config_id"` or `"alias: old_config_id → new_config_id"`

2. **cmd_show(args)** ✓
   - Resolves alias to ModelVersion via `get_model_version_by_alias`
   - Handles unset alias: prints error, exits with sys.exit(1)
   - Retrieves metrics from eval run via `client.get_run(mv.run_id).data.metrics`
   - Prints formatted output:
     - Header: `"travel-assistant @ alias_name"`
     - config_id tag
     - All other tags
     - Key metrics (accuracy_overall, verdict_rate_*, total_cost_usd with $ formatting)

3. **cmd_list(args)** ✓
   - Gets registered model via `get_registered_model`
   - Handles no aliases: prints "no aliases set"
   - Prints each alias sorted by name: `"alias_name -> config_id"`

4. **cmd_rollback(args)** ✓
   - Gets current alias target (handles unset: prints "nothing to roll back", exits)
   - Reads audit log backward for most recent entry with matching alias
   - Handles 4 edge cases:
     - No history: prints "no promotion history for alias X"
     - Last op was rollback: prints "alias was just rolled back; no further history"
     - First promotion (from=""):  prints "alias has no previous target (first promotion ever)"
     - Normal case: proceeds
   - Re-finds previous version via `_find_or_error` (handles multiplicity)
   - Sets alias to previous version
   - Appends rollback event to log
   - Prints summary: `"alias: current_config_id → prev_config_id (rolled back)"`

### Helper Functions Implemented:

- `_find_versions_by_config_id()`: Searches versions, returns sorted by version number (desc)
- `_get_alias_target_config_id()`: Gets current alias target config_id or None
- `_append_log_event()`: Appends JSON events with ISO timestamps
- `_find_or_error()`: Handles version lookup with multiplicity and error handling

### Log File Format:
```json
{"ts": "ISO8601_UTC", "alias": "name", "from": "config_id_or_empty", "to": "config_id", "op": "set|rollback"}
```

### Test Log Provided:
Sample `promotion-log.jsonl` included showing example flow:
- Initial set: (unset) → v1
- Promotion: v1 → v4
- Promotion: v4 → v5  
- Rollback: v5 → v4

## Syntax Verification:
✓ Python syntax check passed
✓ CLI help works: `python scripts/promote.py --help`
✓ All imports present (mlflow, argparse, json, datetime, pathlib)
✓ All MLflow client methods used correctly

## Code Quality:
- Proper error handling with sys.exit(1) for error conditions
- ISO 8601 timestamps via `datetime.now(timezone.utc).isoformat()`
- RestException handling for unset aliases
- File path handling with pathlib.Path
- Sorted output for consistency
- Clear error messages to stderr
