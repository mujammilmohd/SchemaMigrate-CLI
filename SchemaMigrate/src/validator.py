"""Patch schema and operation validation."""
REQUIRED_PATCH_KEYS = {"version", "name", "operations", "rollback"}
SUPPORTED = {"create_collection", "drop_collection", "add_field", "remove_field"}


def validate_patch(patch, expected_version, filename):
    for key in REQUIRED_PATCH_KEYS:
        if key not in patch:
            raise ValueError(f"{filename}: required field '{key}' is missing.")
    if not isinstance(patch["version"], str) or not patch["version"].isdigit():
        raise ValueError(f"{filename}: 'version' must be a numeric string.")
    if patch["version"] != expected_version:
        raise ValueError(
            f"{filename}: version '{patch['version']}' does not match filename version "
            f"'{expected_version}'."
        )
    if not isinstance(patch["name"], str) or not patch["name"].strip():
        raise ValueError(f"{filename}: 'name' must be a non-empty string.")
    for section in ("operations", "rollback"):
        if not isinstance(patch[section], list):
            raise ValueError(f"{filename}: '{section}' must be a list.")
        for index, operation in enumerate(patch[section]):
            _validate_operation(operation, filename, section, index)


def _validate_operation(operation, filename, section, index):
    where = f"{filename}: {section}[{index}]"
    if not isinstance(operation, dict):
        raise ValueError(f"{where} must be an object.")
    op_type = operation.get("type")
    if op_type not in SUPPORTED:
        raise ValueError(f"{where}: unsupported operation '{op_type}'.")
    if not isinstance(operation.get("collection"), str) or not operation["collection"]:
        raise ValueError(f"{where}: 'collection' must be a non-empty string.")
    if op_type in {"add_field", "remove_field"}:
        if not isinstance(operation.get("field"), str) or not operation["field"]:
            raise ValueError(f"{where}: 'field' must be a non-empty string.")
    if op_type == "add_field" and "default" not in operation:
        raise ValueError(f"{where}: add_field requires a 'default' value.")
