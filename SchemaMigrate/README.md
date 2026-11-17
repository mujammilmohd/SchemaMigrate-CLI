# SchemaMigrate CLI

A Python 3 command-line tool that applies ordered JSON patch files to a local JSON database, tracks migration history, and rolls back the latest applied patch.

## Features

- Discovers JSON patches in `patches/` and sorts by numeric version prefix.
- Validates patch structure, version consistency, and supported operations.
- Applies pending migrations once, in ascending order.
- Records version, filename, timestamp, and status in `migration_history`.
- Rolls back only the latest successfully applied migration.
- Uses a deep copy and atomic file replacement so a failed patch does not persist partial changes.
- Provides status, list, history, role restrictions, and dry-run preview.
- Uses only the Python standard library.

## Requirements

- Python 3.9 or newer recommended.
- No pip packages are required.

## Quick start

From the project root:

```bash
python main.py status
python main.py list
python main.py apply
python main.py status
python main.py history
python main.py rollback
```

The repository includes a ready-to-run `database/db.json`. To reset the sample database:

**Windows PowerShell**
```powershell
Copy-Item sample-data/initial_db.json database/db.json -Force
```

**macOS/Linux**
```bash
cp sample-data/initial_db.json database/db.json
```

## Commands

| Command | Purpose |
|---|---|
| `python main.py status` | Show current version, applied and pending patches |
| `python main.py list` | List all patches in version order |
| `python main.py apply` | Apply all pending patches |
| `python main.py apply --dry-run` | Preview patches without modifying files |
| `python main.py rollback` | Reverse the latest applied migration |
| `python main.py history` | Show recorded migration history |
| `python main.py --role operator status` | Operator can inspect status |
| `python main.py --role operator apply` | Rejected: admin-only command |

Global options such as `--role`, `--patches`, and `--database` go before the subcommand.

## Patch format

Filename format: `NNN_descriptive_name.json`.

```json
{
  "version": "001",
  "name": "Add email",
  "operations": [
    {
      "type": "add_field",
      "collection": "students",
      "field": "email",
      "default": ""
    }
  ],
  "rollback": [
    {
      "type": "remove_field",
      "collection": "students",
      "field": "email"
    }
  ]
}
```

Every patch must include a numeric string version, a non-empty name, an `operations` list, and a `rollback` list. The version in the JSON must match the filename prefix.

## Supported operations

- `create_collection`: create an empty list collection.
- `drop_collection`: remove an existing list collection.
- `add_field`: add a field to every record in a collection using `default`.
- `remove_field`: remove a field from every record in a collection.

Collections are represented as lists of JSON objects. Unsupported operations are rejected.

## Data and history

`database/db.json` stores the simulated database and a `migration_history` list. Each successful migration records:

- `version`
- `filename`
- `applied_at` (ISO 8601 timestamp)
- `status` (`APPLIED`)

Current version is derived from the latest applied history entry. Rolled-back migrations are removed from the active history in this MVP.

## Atomicity and limitations

- Each patch is applied to a deep copy and saved only after all its operations succeed.
- JSON is written to a temporary file and then replaced.
- If a later patch fails, earlier successful patches remain applied; later patches are not attempted.
- Only the latest applied migration can be rolled back.
- The patch file must remain available to roll back its migration.
- This is a local demonstration tool, not production authentication or a production database migration system.
- No concurrent migration processes, distributed execution, live database connections, branching migration graph, or arbitrary historical rollback.

## Run tests

```bash
python -m unittest discover -s tests -v
```

## Project structure

```text
SchemaMigrate/
├── main.py
├── patches/
├── database/
│   └── db.json
├── sample-data/
│   └── initial_db.json
├── src/
│   ├── cli.py
│   ├── migration_engine.py
│   ├── operations.py
│   ├── patch_manager.py
│   ├── rollback_engine.py
│   ├── status_manager.py
│   ├── storage.py
│   ├── validator.py
│   └── version_manager.py
├── tests/
│   └── test_project.py
├── README.md
└── .gitignore
```

## Suggested demo sequence

1. Run `python main.py status`.
2. Run `python main.py list`.
3. Run `python main.py apply --dry-run`.
4. Run `python main.py apply`.
5. Run `python main.py status` and `python main.py history`.
6. Run `python main.py apply` again to demonstrate duplicate prevention.
7. Run `python main.py rollback`.
8. Run `python -m unittest discover -s tests -v`.

## Team collaboration

Suggested split:
- Student A: patch discovery, validator, apply engine, and related tests.
- Student B: rollback engine, status/history output, README, and integration tests.
- Both: review, run tests, integrate frequently, and make meaningful Git commits.
