"""Safe JSON persistence helpers."""
import json
import os
import tempfile
from pathlib import Path


def load_database(path):
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"Database file not found: {path}. Copy sample-data/initial_db.json "
            "to database/db.json or run the setup instructions in README.md."
        )
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Database JSON is invalid: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("Database root must be a JSON object.")
    data.setdefault("schema_version", None)
    data.setdefault("migration_history", [])
    if not isinstance(data["migration_history"], list):
        raise ValueError("'migration_history' must be a list.")
    return data


def save_database(path, data):
    """Write atomically: write temp file, then replace the target."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp",
                                     dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=4, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    except Exception:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise
