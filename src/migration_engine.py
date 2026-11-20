"""Atomic apply engine."""
from copy import deepcopy

from .operations import apply_operations
from .patch_manager import get_patch_files, load_patch
from .storage import load_database, save_database
from .validator import validate_patch
from .version_manager import applied_versions, record_migration


def apply_all(patches_dir, database_path, dry_run=False):
    database = load_database(database_path)
    patch_files = get_patch_files(patches_dir)
    if not patch_files:
        print("No migration patches found.")
        return 0

    already_applied = applied_versions(database)
    pending = [(version_num, version, path) for version_num, version, path in patch_files
               if version not in already_applied]
    if not pending:
        print("Database is already up to date.")
        return 0

    if dry_run:
        print("DRY RUN — no files will be changed.")
        for _, version, path in pending:
            patch = load_patch(path)
            validate_patch(patch, version, path.name)
            print(f"  Would apply {version}: {path.name}")
            for operation in patch["operations"]:
                print(f"    - {operation['type']} ({operation['collection']})")
        return 0

    applied_count = 0
    for _, version, path in pending:
        print(f"[...] Applying {path.name}")
        patch = load_patch(path)
        validate_patch(patch, version, path.name)
        # Work on an isolated copy. A failure cannot partially alter persisted data.
        working = deepcopy(database)
        apply_operations(working, patch["operations"])
        record_migration(working, version, path.name)
        save_database(database_path, working)
        database = working
        applied_count += 1
        print(f"[✓] Migration {version} applied successfully.")
    print(f"Current Version: {database.get('schema_version') or 'None'}")
    print(f"Applied {applied_count} migration(s).")
    return 0
