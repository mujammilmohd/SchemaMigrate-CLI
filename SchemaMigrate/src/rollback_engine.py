"""Rollback the latest successfully applied migration."""
from copy import deepcopy

from .operations import apply_operations
from .patch_manager import get_patch_files, load_patch
from .storage import load_database, save_database
from .validator import validate_patch
from .version_manager import remove_latest_migration


def rollback_last(patches_dir, database_path):
    database = load_database(database_path)
    applied = [item for item in database.get("migration_history", [])
               if item.get("status") == "APPLIED"]
    if not applied:
        print("No migration available to roll back.")
        return 0

    latest = max(applied, key=lambda item: int(item["version"]))
    patch_path = next(
        (path for _, version, path in get_patch_files(patches_dir)
         if version == latest["version"]), None
    )
    if patch_path is None:
        raise ValueError(
            f"Cannot roll back {latest['version']}: patch file "
            f"'{latest['filename']}' is missing."
        )

    patch = load_patch(patch_path)
    validate_patch(patch, latest["version"], patch_path.name)
    working = deepcopy(database)
    apply_operations(working, patch["rollback"])
    removed = remove_latest_migration(working)
    if removed is None:
        raise ValueError("Migration history changed; nothing to roll back.")
    save_database(database_path, working)
    print(f"[✓] Rolled back {latest['filename']}.")
    print(f"Current Version: {working.get('schema_version') or 'None'}")
    return 0
