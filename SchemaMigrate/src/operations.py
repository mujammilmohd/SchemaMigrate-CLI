"""Supported JSON database operations."""
from copy import deepcopy


def apply_operations(database, operations):
    for operation in operations:
        kind = operation["type"]
        collection = operation["collection"]

        if kind == "create_collection":
            if collection in database:
                raise ValueError(f"Collection '{collection}' already exists.")
            database[collection] = []

        elif kind == "drop_collection":
            if collection not in database:
                raise ValueError(f"Collection '{collection}' does not exist.")
            if not isinstance(database[collection], list):
                raise ValueError(f"'{collection}' is not a collection.")
            del database[collection]

        elif kind == "add_field":
            records = _get_collection(database, collection)
            field = operation["field"]
            if any(field in record for record in records):
                raise ValueError(f"Field '{field}' already exists in '{collection}'.")
            for record in records:
                record[field] = deepcopy(operation["default"])

        elif kind == "remove_field":
            records = _get_collection(database, collection)
            field = operation["field"]
            if any(field not in record for record in records):
                raise ValueError(f"Field '{field}' is missing from one or more '{collection}' records.")
            for record in records:
                del record[field]
        else:
            # Defensive guard; validator should reject this first.
            raise ValueError(f"Unsupported operation '{kind}'.")


def _get_collection(database, name):
    if name not in database:
        raise ValueError(f"Collection '{name}' does not exist.")
    records = database[name]
    if not isinstance(records, list) or any(not isinstance(row, dict) for row in records):
        raise ValueError(f"'{name}' must be a list of JSON objects.")
    return records
