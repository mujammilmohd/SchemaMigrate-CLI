"""CLI command routing and role authorization."""
from .migration_engine import apply_all
from .rollback_engine import rollback_last
from .status_manager import list_patches, show_history, show_status


ADMIN_ONLY = {"apply", "rollback"}


def run(args):
    if args.command in ADMIN_ONLY and args.role != "administrator":
        print("Permission denied: administrator access required.")
        return 2

    if args.command == "status":
        show_status(args.patches, args.database)
    elif args.command == "list":
        list_patches(args.patches, args.database)
    elif args.command == "apply":
        return apply_all(args.patches, args.database, dry_run=args.dry_run)
    elif args.command == "rollback":
        return rollback_last(args.patches, args.database)
    elif args.command == "history":
        show_history(args.database)
    return 0
