"""Read-only status and history views."""
from .patch_manager import get_patch_files
from .storage import load_database
from .version_manager import applied_versions, current_version


def show_status(patches_dir, database_path):
    database = load_database(database_path)
    patches = get_patch_files(patches_dir)
    applied = applied_versions(database)
    print("=" * 44)
    print("             SCHEMAMIGRATE CLI")
    print("=" * 44)
    print(f"Current Version: {current_version(database) or 'None'}")
    print("\nApplied Migrations:")
    any_applied = False
    for _, version, path in patches:
        if version in applied:
            print(f"  [✓] {version}  {path.name}")
            any_applied = True
    if not any_applied:
        print("  (none)")
    print("\nPending Migrations:")
    pending = [(v, p) for _, v, p in patches if v not in applied]
    if not pending:
        print("  (none)")
    for version, path in pending:
        print(f"  [ ] {version}  {path.name}")
    print("=" * 44)


def list_patches(patches_dir, database_path):
    database = load_database(database_path)
    applied = applied_versions(database)
    patches = get_patch_files(patches_dir)
    if not patches:
        print("No migration patches found.")
        return
    for _, version, path in patches:
        state = "APPLIED" if version in applied else "PENDING"
        print(f"{version}  {state:7}  {path.name}")


def show_history(database_path):
    database = load_database(database_path)
    history = database.get("migration_history", [])
    if not history:
        print("Migration history is empty.")
        return
    print("Migration History:")
    for item in history:
        print(f"  {item.get('version')}  {item.get('status')}  "
              f"{item.get('filename')}  {item.get('applied_at')}")
