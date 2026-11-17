"""SchemaMigrate CLI entry point."""
import argparse
import json
import sys
from pathlib import Path

from src.cli import run


def build_parser():
    parser = argparse.ArgumentParser(
        prog="SchemaMigrate",
        description="Apply ordered JSON schema patches to a local JSON database.",
        epilog="""Examples:
  python main.py status
  python main.py list
  python main.py apply
  python main.py apply --dry-run
  python main.py rollback
  python main.py --role operator status""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--role", choices=("administrator", "operator"),
        default="administrator",
        help="Demonstration role (default: administrator).",
    )
    parser.add_argument(
        "--patches", default="patches",
        help="Patch directory (default: patches).",
    )
    parser.add_argument(
        "--database", default="database/db.json",
        help="Database JSON path (default: database/db.json).",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status", help="Show current version and applied/pending patches.")
    sub.add_parser("list", help="List all discovered patches.")
    apply_parser = sub.add_parser("apply", help="Apply all pending patches.")
    apply_parser.add_argument("--dry-run", action="store_true",
                              help="Preview pending patches without changing files.")
    sub.add_parser("rollback", help="Roll back the latest applied migration.")
    sub.add_parser("history", help="Show migration history.")
    return parser


def main():
    args = build_parser().parse_args()
    try:
        return run(args)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
