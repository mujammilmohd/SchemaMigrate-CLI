"""Patch discovery, filename/version validation, and ordering."""
import json
import re
from pathlib import Path

FILENAME_RE = re.compile(r"^(?P<version>\d+)_[A-Za-z0-9_-]+\.json$")


def get_patch_files(patches_dir):
    directory = Path(patches_dir)
    if not directory.exists():
        return []
    if not directory.is_dir():
        raise ValueError(f"Patch path is not a directory: {directory}")
    found = []
    versions = {}
    for path in directory.glob("*.json"):
        match = FILENAME_RE.match(path.name)
        if not match:
            raise ValueError(
                f"Invalid patch filename '{path.name}'. Expected "
                "'NNN_descriptive_name.json'."
            )
        version = match.group("version")
        if version in versions:
            raise ValueError(
                f"Duplicate patch version {version}: {versions[version]} and {path.name}"
            )
        versions[version] = path.name
        found.append((int(version), version, path))
    return sorted(found, key=lambda item: item[0])


def load_patch(path):
    try:
        patch = json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Unable to read patch file {Path(path).name}: invalid JSON ({exc})") from exc
    if not isinstance(patch, dict):
        raise ValueError(f"Patch {Path(path).name}: root must be a JSON object.")
    return patch
