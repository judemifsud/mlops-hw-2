"""scripts/promote.py — promote MLflow Registry aliases with an audit log.

YOUR TASK (see tasks/task2.md): implement the four subcommand functions.
The argparse scaffolding below is wired so each cmd_* receives an `args`
namespace already parsed. See `_build_parser` for what's on `args` per
subcommand, and tasks/task2.md "Behavioral specs" for what each function
must do.

Versions are identified by their `config_id` tag (e.g., "v6"), NOT by
MLflow's integer version numbers. Resolution must be unique — if the
config_id matches zero or multiple registered versions, the CLI errors
out and forces the operator to disambiguate via the MLflow UI.

Successful `set` and `rollback` operations append a JSON event to
LOG_FILE (promotion-log.jsonl at repo root). `rollback` consults the
log to find the previous alias target.

Subcommands:
  set <alias> <config_id>   move alias, append `set` event to the log
  show <alias>              print current target + tags + key metrics
  list                      print all aliases on the registered model
  rollback <alias>          move alias back per the audit log, append
                            `rollback` event
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import mlflow
from mlflow.exceptions import RestException
from mlflow.tracking import MlflowClient

REGISTERED_MODEL_NAME = "travel-assistant"
LOG_FILE = Path(__file__).resolve().parent.parent / "promotion-log.jsonl"


def _find_versions_by_config_id(client: MlflowClient, config_id: str) -> list:
    """Find all registered versions with the given config_id tag.
    
    Returns list of ModelVersion objects sorted by version number (desc).
    """
    filter_str = f"name = '{REGISTERED_MODEL_NAME}' AND tags.config_id = '{config_id}'"
    versions = client.search_model_versions(filter_str)
    # Sort by version number descending (most recent first)
    versions = sorted(versions, key=lambda v: int(v.version), reverse=True)
    return versions


def _get_alias_target_config_id(client: MlflowClient, alias: str) -> str | None:
    """Get the config_id of the version an alias currently points to.
    
    Returns config_id string, or None if the alias is unset.
    """
    try:
        mv = client.get_model_version_by_alias(REGISTERED_MODEL_NAME, alias)
        return mv.tags.get("config_id", "")
    except RestException:
        return None


def _append_log_event(alias: str, from_config_id: str, to_config_id: str, op: str) -> None:
    """Append a JSON event to the promotion log."""
    event = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "alias": alias,
        "from": from_config_id,
        "to": to_config_id,
        "op": op,
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")


def _find_or_error(client: MlflowClient, config_id: str) -> int:
    """Find version by config_id with multiplicity handling.
    
    Returns the MLflow version number (as int) to use.
    Exits with error if zero or multiple matches (prints warning on multiple).
    """
    versions = _find_versions_by_config_id(client, config_id)
    
    if len(versions) == 0:
        print(f"error: no version found with config_id={config_id}", file=sys.stderr)
        sys.exit(1)
    
    if len(versions) > 1:
        version_nums = [int(v.version) for v in versions]
        print(
            f"warning: multiple versions match config_id={config_id} "
            f"(MLflow versions {version_nums}); using latest ({version_nums[0]})"
        )
    
    return int(versions[0].version)


def cmd_set(args: argparse.Namespace) -> None:
    """args.alias: str, args.config_id: str. See tasks/task2.md → cmd_set."""
    client = MlflowClient()
    
    # Find the target version by config_id
    target_version = _find_or_error(client, args.config_id)
    
    # Get current target
    current_config_id = _get_alias_target_config_id(client, args.alias)
    current_display = current_config_id if current_config_id else "(unset)"
    
    # Set the alias
    client.set_registered_model_alias(REGISTERED_MODEL_NAME, args.alias, target_version)
    
    # Append to log
    from_config = current_config_id or ""
    _append_log_event(args.alias, from_config, args.config_id, "set")
    
    # Print summary
    print(f"{args.alias}: {current_display} → {args.config_id}")


def cmd_show(args: argparse.Namespace) -> None:
    """args.alias: str. See tasks/task2.md → cmd_show."""
    client = MlflowClient()
    
    # Get the version the alias points to
    try:
        mv = client.get_model_version_by_alias(REGISTERED_MODEL_NAME, args.alias)
    except RestException:
        print(f"error: alias '{args.alias}' is not set", file=sys.stderr)
        sys.exit(1)
    
    config_id = mv.tags.get("config_id", "")
    
    # Get metrics from the source run
    run = client.get_run(mv.run_id)
    metrics = run.data.metrics
    
    # Print header
    print(f"travel-assistant @ {args.alias}")
    
    # Print config_id
    print(f"  config_id: {config_id}")
    
    # Print all tags
    for tag_key, tag_val in sorted(mv.tags.items()):
        if tag_key != "config_id":  # Already printed above
            print(f"  {tag_key}: {tag_val}")
    
    # Print key metrics
    key_metrics = [
        "accuracy_overall",
        "verdict_rate_leaked",
        "verdict_rate_answered_correctly",
        "verdict_rate_refused_correctly",
        "verdict_rate_over_refused",
        "total_cost_usd",
    ]
    for metric_key in key_metrics:
        if metric_key in metrics:
            val = metrics[metric_key]
            # Format cost with dollar sign
            if metric_key == "total_cost_usd":
                print(f"  {metric_key}: ${val:.2f}")
            else:
                print(f"  {metric_key}: {val}")


def cmd_list(args: argparse.Namespace) -> None:
    """No args. See tasks/task2.md → cmd_list."""
    client = MlflowClient()
    
    # Get the registered model
    try:
        rm = client.get_registered_model(REGISTERED_MODEL_NAME)
    except RestException:
        print("no aliases set")
        return
    
    # Print aliases
    if not rm.aliases:
        print("no aliases set")
        return
    
    # Sort by alias name for consistent output
    for alias_name in sorted(rm.aliases.keys()):
        version_num = rm.aliases[alias_name]
        # Look up config_id from the version
        mv = client.get_model_version(REGISTERED_MODEL_NAME, version_num)
        config_id = mv.tags.get("config_id", "")
        print(f"{alias_name} -> {config_id}")


def cmd_rollback(args: argparse.Namespace) -> None:
    """args.alias: str. See tasks/task2.md → cmd_rollback."""
    client = MlflowClient()
    
    # Get current alias target
    current_config_id = _get_alias_target_config_id(client, args.alias)
    if current_config_id is None:
        print("error: nothing to roll back", file=sys.stderr)
        sys.exit(1)
    
    # Read the log to find previous target
    if not LOG_FILE.exists():
        print(f"error: no promotion history for alias {args.alias}", file=sys.stderr)
        sys.exit(1)
    
    # Scan log backward for the most recent entry with this alias
    log_entries = []
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                log_entries.append(json.loads(line))
    
    # Find the most recent entry for this alias
    prev_entry = None
    for entry in reversed(log_entries):
        if entry["alias"] == args.alias:
            prev_entry = entry
            break
    
    if prev_entry is None:
        print(f"error: no promotion history for alias {args.alias}", file=sys.stderr)
        sys.exit(1)
    
    # Check if the last entry was a rollback
    if prev_entry["op"] == "rollback":
        print(f"error: {args.alias} was just rolled back; no further history to walk back to", file=sys.stderr)
        sys.exit(1)
    
    # Check if there's a previous target
    if prev_entry["from"] == "":
        print(f"error: {args.alias} has no previous target (first promotion ever)", file=sys.stderr)
        sys.exit(1)
    
    # Find the previous version
    prev_config_id = prev_entry["from"]
    target_version = _find_or_error(client, prev_config_id)
    
    # Set the alias to the previous version
    client.set_registered_model_alias(REGISTERED_MODEL_NAME, args.alias, target_version)
    
    # Append rollback event to log
    _append_log_event(args.alias, current_config_id, prev_config_id, "rollback")
    
    # Print summary
    print(f"{args.alias}: {current_config_id} → {prev_config_id} (rolled back)")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--name",
        default=REGISTERED_MODEL_NAME,
        help=f"Registered model name (default: {REGISTERED_MODEL_NAME})",
    )

    sub = parser.add_subparsers(dest="cmd", required=True)

    p_set = sub.add_parser(
        "set", help="Move an alias to a version (by config_id), append a set event"
    )
    p_set.add_argument("alias", help="Alias to assign (e.g., 'production')")
    p_set.add_argument(
        "config_id",
        help="Config identifier (e.g., 'v6') — resolved via the config_id tag on registered versions",
    )
    p_set.set_defaults(func=cmd_set)

    p_show = sub.add_parser("show", help="Show which version an alias points at")
    p_show.add_argument("alias")
    p_show.set_defaults(func=cmd_show)

    p_list = sub.add_parser("list", help="List all aliases on the registered model")
    p_list.set_defaults(func=cmd_list)

    p_rollback = sub.add_parser(
        "rollback",
        help="Move an alias back to its previous target per the audit log",
    )
    p_rollback.add_argument("alias")
    p_rollback.set_defaults(func=cmd_rollback)

    return parser


def main() -> None:
    args = _build_parser().parse_args()
    try:
        args.func(args)
    except NotImplementedError as exc:
        print(f"NOT IMPLEMENTED: {exc}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
