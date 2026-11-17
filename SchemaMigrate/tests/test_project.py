import json
import tempfile
import unittest
from pathlib import Path

from src.migration_engine import apply_all
from src.rollback_engine import rollback_last
from src.storage import load_database


class SchemaMigrateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.patches = self.root / "patches"
        self.patches.mkdir()
        self.db = self.root / "db.json"
        self.db.write_text(json.dumps({
            "schema_version": None,
            "students": [{"id": 1, "name": "A"}],
            "migration_history": []
        }), encoding="utf-8")
        self.patch = {
            "version": "001",
            "name": "Add email",
            "operations": [{"type": "add_field", "collection": "students",
                            "field": "email", "default": ""}],
            "rollback": [{"type": "remove_field", "collection": "students",
                          "field": "email"}]
        }
        (self.patches / "001_add_email.json").write_text(
            json.dumps(self.patch), encoding="utf-8"
        )

    def tearDown(self):
        self.temp.cleanup()

    def test_apply_and_rollback(self):
        self.assertEqual(apply_all(self.patches, self.db), 0)
        data = load_database(self.db)
        self.assertEqual(data["schema_version"], "001")
        self.assertEqual(data["students"][0]["email"], "")
        self.assertEqual(len(data["migration_history"]), 1)
        self.assertEqual(rollback_last(self.patches, self.db), 0)
        data = load_database(self.db)
        self.assertIsNone(data["schema_version"])
        self.assertNotIn("email", data["students"][0])
        self.assertEqual(data["migration_history"], [])

    def test_failed_patch_does_not_save_partial_changes(self):
        bad = dict(self.patch)
        bad["operations"] = [
            {"type": "add_field", "collection": "students", "field": "email", "default": ""},
            {"type": "unknown_operation", "collection": "students"}
        ]
        (self.patches / "001_add_email.json").write_text(json.dumps(bad), encoding="utf-8")
        before = self.db.read_text(encoding="utf-8")
        with self.assertRaises(ValueError):
            apply_all(self.patches, self.db)
        self.assertEqual(self.db.read_text(encoding="utf-8"), before)

    def test_apply_twice_does_not_duplicate(self):
        apply_all(self.patches, self.db)
        apply_all(self.patches, self.db)
        data = load_database(self.db)
        self.assertEqual(len(data["migration_history"]), 1)


if __name__ == "__main__":
    unittest.main()
