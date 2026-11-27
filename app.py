from flask import Flask, render_template, request, jsonify
from pathlib import Path
from copy import deepcopy
from datetime import datetime, timezone
import json
import re

BASE_DIR = Path(__file__).resolve().parent
DATABASE_DIR = BASE_DIR / "database"
PATCH_DIR = BASE_DIR / "patches"
DB_PATH = DATABASE_DIR / "db.json"

app = Flask(__name__)
SUPPORTED_OPERATIONS = {"create_collection", "drop_collection", "add_field", "remove_field"}


def ensure_project_files():
    DATABASE_DIR.mkdir(exist_ok=True)
    PATCH_DIR.mkdir(exist_ok=True)
    if not DB_PATH.exists():
        DB_PATH.write_text(json.dumps({
            "schema_version": None,
            "migration_history": [],
            "students": [
                {"id": 1, "name": "Aarav"},
                {"id": 2, "name": "Sara"}
            ]
        }, indent=4), encoding="utf-8")
    if not any(PATCH_DIR.glob("*.json")):
        samples = [
            {
                "version": "001",
                "name": "Add student email",
                "operations": [{"type": "add_field", "collection": "students", "field": "email", "default": "student@example.com"}],
                "rollback": [{"type": "remove_field", "collection": "students", "field": "email"}]
            },
            {
                "version": "002",
                "name": "Add student status",
                "operations": [{"type": "add_field", "collection": "students", "field": "status", "default": "active"}],
                "rollback": [{"type": "remove_field", "collection": "students", "field": "status"}]
            },
            {
                "version": "003",
                "name": "Create courses collection",
                "operations": [{"type": "create_collection", "collection": "courses"}],
                "rollback": [{"type": "drop_collection", "collection": "courses"}]
            }
        ]
        for item in samples:
            path = PATCH_DIR / f'{item["version"]}_{item["name"].lower().replace(" ", "_")}.json'
            path.write_text(json.dumps(item, indent=4), encoding="utf-8")


def read_db():
    ensure_project_files()
    try:
        data = json.loads(DB_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Database JSON is invalid: {exc}")
    if not isinstance(data, dict):
        raise ValueError("Database root must be a JSON object.")
    data.setdefault("schema_version", None)
    data.setdefault("migration_history", [])
    return data


def write_db(data):
    DATABASE_DIR.mkdir(exist_ok=True)
    temp_path = DB_PATH.with_suffix(".tmp")
    temp_path.write_text(json.dumps(data, indent=4), encoding="utf-8")
    temp_path.replace(DB_PATH)


def validate_patch(patch, version, filename):
    if not isinstance(patch, dict):
        raise ValueError(f"{filename}: patch must be a JSON object.")
    if str(patch.get("version")) != version:
        raise ValueError(f"{filename}: version must match its filename.")
    if not patch.get("name"):
        raise ValueError(f"{filename}: name is required.")
    for key in ("operations", "rollback"):
        if not isinstance(patch.get(key), list) or not patch[key]:
            raise ValueError(f"{filename}: {key} must be a non-empty list.")
        for operation in patch[key]:
            if not isinstance(operation, dict):
                raise ValueError(f"{filename}: each operation must be an object.")
            kind = operation.get("type")
            collection = operation.get("collection")
            if kind not in SUPPORTED_OPERATIONS or not collection:
                raise ValueError(f"{filename}: unsupported operation or missing collection.")
            if kind in {"add_field", "remove_field"} and not operation.get("field"):
                raise ValueError(f"{filename}: field is required for {kind}.")


def get_patches():
    ensure_project_files()
    patches = []
    seen_versions = set()
    for path in PATCH_DIR.glob("*.json"):
        match = re.fullmatch(r"(\d{3,})_([A-Za-z0-9_-]+)\.json", path.name)
        if not match:
            raise ValueError(f"Invalid patch filename: {path.name}. Use 001_name.json.")
        version = match.group(1)
        if version in seen_versions:
            raise ValueError(f"Duplicate patch version: {version}.")
        seen_versions.add(version)
        try:
            patch = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path.name} contains invalid JSON: {exc}")
        validate_patch(patch, version, path.name)
        patches.append({
            "version": version,
            "filename": path.name,
            "name": patch["name"],
            "operations": patch["operations"],
            "rollback": patch["rollback"]
        })
    return sorted(patches, key=lambda item: int(item["version"]))


def applied_versions(db):
    return {
        str(item.get("version"))
        for item in db.get("migration_history", [])
        if item.get("status", "APPLIED") == "APPLIED"
    }


def apply_operations(db, operations):
    for op in operations:
        kind = op["type"]
        collection = op["collection"]
        if kind == "create_collection":
            if collection in db:
                raise ValueError(f"Collection '{collection}' already exists.")
            db[collection] = []
        elif kind == "drop_collection":
            if collection not in db or not isinstance(db[collection], list):
                raise ValueError(f"Collection '{collection}' does not exist.")
            del db[collection]
        elif kind in {"add_field", "remove_field"}:
            rows = db.get(collection)
            if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
                raise ValueError(f"'{collection}' must be a list of JSON objects.")
            field = op["field"]
            if kind == "add_field":
                if any(field in row for row in rows):
                    raise ValueError(f"Field '{field}' already exists in at least one record.")
                for row in rows:
                    row[field] = deepcopy(op.get("default"))
            else:
                if any(field not in row for row in rows):
                    raise ValueError(f"Field '{field}' is missing from at least one record.")
                for row in rows:
                    del row[field]


def dashboard_data():
    db = read_db()
    patches = get_patches()
    applied = applied_versions(db)
    history = list(reversed(db.get("migration_history", [])))
    collections = []
    for name, value in db.items():
        if isinstance(value, list):
            collections.append({
                "name": name,
                "records": len(value),
                "fields": sorted({key for row in value if isinstance(row, dict) for key in row})
            })
    return {
        "current_version": db.get("schema_version") or "Not set",
        "applied_count": len(applied),
        "total_patches": len(patches),
        "pending_count": sum(p["version"] not in applied for p in patches),
        "applied": [p for p in patches if p["version"] in applied],
        "pending": [p for p in patches if p["version"] not in applied],
        "patches": [dict(p, status="APPLIED" if p["version"] in applied else "PENDING") for p in patches],
        "history": history,
        "collections": collections,
        "database": db
    }


def require_admin(payload):
    if not isinstance(payload, dict) or payload.get("role") != "administrator":
        return jsonify({"error": "Administrator access is required for this action."}), 403
    return None


@app.get("/")
def home():
    ensure_project_files()
    return render_template("index.html")


@app.get("/api/dashboard")
def api_dashboard():
    try:
        data = dashboard_data()
        data.pop("database", None)
        return jsonify(data)
    except Exception as exc:
        app.logger.exception("Dashboard loading failed")
        return jsonify({"error": str(exc)}), 500


@app.get("/api/database")
def api_database():
    try:
        return jsonify(read_db())
    except Exception as exc:
        app.logger.exception("Database loading failed")
        return jsonify({"error": str(exc)}), 500


@app.get("/api/patches")
def api_patches():
    try:
        return jsonify(dashboard_data()["patches"])
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.get("/api/history")
def api_history():
    try:
        return jsonify(dashboard_data()["history"])
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.post("/api/apply")
def api_apply():
    payload = request.get_json(silent=True) or {}
    denied = require_admin(payload)
    if denied:
        return denied
    try:
        db = read_db()
        patches = get_patches()
        applied = applied_versions(db)
        pending = [patch for patch in patches if patch["version"] not in applied]
        if payload.get("dry_run"):
            # Validate the complete sequence against a copy without saving.
            preview = deepcopy(db)
            for patch in pending:
                apply_operations(preview, patch["operations"])
            return jsonify({
                "message": f"Dry run successful. {len(pending)} migration(s) are ready.",
                "dry_run": True,
                "items": [{"version": p["version"], "name": p["name"], "operations": p["operations"]} for p in pending]
            })
        logs = []
        working = deepcopy(db)
        for patch in pending:
            apply_operations(working, patch["operations"])
            working.setdefault("migration_history", []).append({
                "version": patch["version"],
                "filename": patch["filename"],
                "name": patch["name"],
                "applied_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
                "status": "APPLIED"
            })
            working["schema_version"] = patch["version"]
            logs.append(f'Applied {patch["version"]} — {patch["name"]}')
        if pending:
            write_db(working)
        return jsonify({
            "message": f"Successfully applied {len(logs)} migration(s)." if logs else "Database is already up to date.",
            "logs": logs
        })
    except Exception as exc:
        app.logger.exception("Applying migrations failed")
        return jsonify({"error": str(exc)}), 400


@app.post("/api/rollback")
def api_rollback():
    payload = request.get_json(silent=True) or {}
    denied = require_admin(payload)
    if denied:
        return denied
    try:
        db = read_db()
        patches = get_patches()
        history = db.get("migration_history", [])
        if not history:
            return jsonify({"error": "There is no migration to roll back."}), 400
        latest = history[-1]
        patch = next((p for p in patches if p["version"] == str(latest["version"])), None)
        if patch is None:
            return jsonify({"error": "The patch file for the latest migration was not found."}), 400
        working = deepcopy(db)
        apply_operations(working, patch["rollback"])
        working["migration_history"] = history[:-1]
        working["schema_version"] = working["migration_history"][-1]["version"] if working["migration_history"] else None
        write_db(working)
        return jsonify({"message": f'Rolled back {patch["version"]} — {patch["name"]}.'})
    except Exception as exc:
        app.logger.exception("Rollback failed")
        return jsonify({"error": str(exc)}), 400


@app.post("/api/patches")
def api_create_patch():
    payload = request.get_json(silent=True) or {}
    denied = require_admin(payload)
    if denied:
        return denied
    try:
        version = str(payload.get("version", "")).strip()
        name = str(payload.get("name", "")).strip()
        operations = payload.get("operations")
        rollback = payload.get("rollback")
        if not re.fullmatch(r"\d{3,}", version):
            return jsonify({"error": "Version must contain at least 3 digits, such as 004."}), 400
        if not name or not isinstance(operations, list) or not isinstance(rollback, list):
            return jsonify({"error": "Name, operations and rollback are required."}), 400
        slug = re.sub(r"[^A-Za-z0-9_-]+", "_", name.lower()).strip("_") or "migration"
        filename = f"{version}_{slug}.json"
        path = PATCH_DIR / filename
        if path.exists() or any(p["version"] == version for p in get_patches()):
            return jsonify({"error": "That migration version already exists."}), 409
        patch = {"version": version, "name": name, "operations": operations, "rollback": rollback}
        validate_patch(patch, version, filename)
        path.write_text(json.dumps(patch, indent=4), encoding="utf-8")
        return jsonify({"message": f"Created {filename}.", "filename": filename}), 201
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400

@app.delete("/api/patches/<version>")
def api_delete_patch(version):
    payload = request.get_json(silent=True) or {}

    denied = require_admin(payload)
    if denied:
        return denied

    try:
        # Validate version format
        if not re.fullmatch(r"\d{3,}", version):
            return jsonify({"error": "Invalid migration version."}), 400

        db = read_db()
        patches = get_patches()

        # Find the requested patch
        patch = next(
            (p for p in patches if p["version"] == version),
            None
        )

        if patch is None:
            return jsonify({"error": "Migration patch not found."}), 404

        # Never delete an applied migration
        if version in applied_versions(db):
            return jsonify({
                "error": "Applied migrations cannot be deleted. Roll back first."
            }), 409

        # Delete the patch file
        patch_path = PATCH_DIR / patch["filename"]
        patch_path.unlink()

        return jsonify({
            "message": f'Migration {version} deleted successfully.'
        })

    except Exception as exc:
        app.logger.exception("Deleting migration failed")
        return jsonify({"error": str(exc)}), 400

@app.errorhandler(404)
def not_found(_error):
    if request.path.startswith("/api/"):
        return jsonify({"error": f"API route not found: {request.path}"}), 404
    return "Page not found", 404


@app.errorhandler(500)
def server_error(_error):
    if request.path.startswith("/api/"):
        return jsonify({"error": "An unexpected server error occurred. Check the Flask terminal."}), 500
    return "An unexpected server error occurred.", 500


if __name__ == "__main__":
    ensure_project_files()
    app.run(debug=True, port=5000)
