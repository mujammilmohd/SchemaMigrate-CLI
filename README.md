# SchemaMigrate


A beginner-friendly Flask website for managing JSON database schema migrations.

## Features

- First-visit guided tutorial (can be reopened from the sidebar).
- Dashboard with current schema version, applied/pending counts, migration pipeline and activity.
- Migration library with search and status.
- Create migration patches using JSON forward and rollback operations.
- Dry-run validation that does not save changes.
- Apply pending migrations.
- Roll back the latest migration.
- Migration history and JSON database inspector.
- Operator and Administrator interface roles.
- JSON API responses for API errors, so frontend requests can display useful errors instead of failing silently.

## Requirements

- Python 3.9+
- Flask (installed from requirements.txt)

## Run on Windows (VS Code)

1. Extract this ZIP.
2. Open the extracted `SchemaMigrate_Clean` folder in VS Code.
3. Open Terminal → New Terminal.
4. Create a virtual environment:

   ```powershell
   py -m venv venv
   ```

5. Activate it:

   ```powershell
   .\venv\Scripts\activate
   ```

6. Install Flask:

   ```powershell
   python -m pip install -r requirements.txt
   ```

7. Start the website:

   ```powershell
   python app.py
   ```

8. Open <http://127.0.0.1:5000> in your browser.

Keep the terminal open while using the website. Press Ctrl+C to stop the server.

## First-time demo data

The app creates `database/db.json` and three example migration patches inside `patches/` when those folders are empty. The example patches add an email field, add a status field and create a courses collection.

To reset the demo from scratch:
1. Stop Flask.
2. Replace `database/db.json` with the original starter database from this ZIP, or remove the generated demo database and restart.
3. If you have applied migrations, do not delete or alter patch files without understanding the history.

## How to use

1. Complete the welcome tutorial.
2. Go to Migrations and review the pending patch files.
3. Select Administrator in the top-right role selector.
4. Click Run dry-run. This validates the full pending sequence without writing to the database.
5. If validation succeeds, click Apply pending and confirm.
6. Visit History to verify the applied migrations.
7. Visit Database to inspect `database/db.json`.
8. Use Roll back latest on History to reverse the most recent migration using its rollback instructions.

## Patch format

Patch files are named `001_some_change.json` and contain:

```json
{
  "version": "001",
  "name": "Add student email",
  "operations": [
    {
      "type": "add_field",
      "collection": "students",
      "field": "email",
      "default": "student@example.com"
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

Supported operation types:
- `create_collection` — create an empty collection.
- `drop_collection` — remove a collection.
- `add_field` — add a field to every object in a collection.
- `remove_field` — remove a field from every object in a collection.

## Important notes

- This is a local development dashboard, not a production-hosted service.
- The role selector is a learning/demo control, not secure authentication. Anyone with access to the local app can select Administrator.
- Make backups before applying or rolling back migrations.
- The dashboard manages its own JSON migration engine and demo data. If you want it to use a separate existing CLI project, the backend paths and engine functions must be integrated with that project's actual source files.
