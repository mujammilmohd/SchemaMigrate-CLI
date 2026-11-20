"""Migration history helpers."""
from datetime import datetime, timezone


def applied_versions(database):
    return {
        item["version"] for item in database.get("migration_history", [])
        if item.get("status") == "APPLIED"
    }


def current_version(database):
    versions = [
        item["version"] for item in database.get("migration_history", [])
        if item.get("status") == "APPLIED"
    ]
    return max(versions, key=int) if versions else None


def record_migration(database, version, filename):
    database.setdefault("migration_history", []).append({
        "version": version,
        "filename": filename,
        "applied_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "status": "APPLIED",
    })
    database["schema_version"] = version


def remove_latest_migration(database):
    history = database.get("migration_history", [])
    applied = [item for item in history if item.get("status") == "APPLIED"]
    if not applied:
        return None
    latest = max(applied, key=lambda item: int(item["version"]))
    history.remove(latest)
    database["schema_version"] = current_version(database)
    return latest
