"""
Supplementary unit tests for StudyMate - AS91896

Run with:
    python3 -m unittest -v test_main.py

Keep this file in the same folder as main.py.
"""


import hashlib
import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta

import main as app


class TestStudyMatePersistenceAndBoundaries(unittest.TestCase):
    """Test persistence and edge cases that complement StudyMate's built-in tests."""

    def setUp(self):
        """Use an isolated temporary data folder for every test."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_data_dir = app.DATA_DIR
        self.original_users_file = app.USERS_FILE
        self.original_temp_users_file = app.TEMP_USERS_FILE

        app.DATA_DIR = self.temp_dir.name
        app.USERS_FILE = os.path.join(self.temp_dir.name, "users.json")
        app.TEMP_USERS_FILE = os.path.join(self.temp_dir.name, "users.tmp.json")

    def tearDown(self):
        """Restore StudyMate's original file locations after each test."""
        app.DATA_DIR = self.original_data_dir
        app.USERS_FILE = self.original_users_file
        app.TEMP_USERS_FILE = self.original_temp_users_file
        self.temp_dir.cleanup()

    @staticmethod
    def make_user(username="testuser"):
        """Create a User with a deterministic hashed password."""
        password_hash = hashlib.sha256("password".encode()).hexdigest()
        return app.User(username, password_hash)

    def test_save_and_reload_complete_user_data(self):
        """Verify subjects, logs, tasks and settings survive save/reload."""
        user = self.make_user()
        deadline = (datetime.now() + timedelta(days=7)).strftime(app.DATE_FORMAT)
        today = datetime.now().strftime(app.DATE_FORMAT)

        user.add_subject("Maths", 5, "High", deadline, target_grade="A")
        user.log_study_time(today, "Maths", 1.5)
        user.add_task("Revise algebra", "Maths", deadline, "High")
        user.theme = "dark"
        user.work_minutes = 30
        user.break_minutes = 10

        self.assertTrue(app.DataManager.save_users({"testuser": user}))
        loaded = app.DataManager.load_users()

        self.assertIn("testuser", loaded)
        restored = loaded["testuser"]
        self.assertIn("Maths", restored.subjects)
        self.assertEqual(restored.logs[today]["Maths"], 1.5)
        self.assertEqual(restored.tasks[0]["title"], "Revise algebra")
        self.assertEqual(restored.theme, "dark")
        self.assertEqual(restored.work_minutes, 30)
        self.assertEqual(restored.break_minutes, 10)

    def test_missing_users_file_returns_empty_dictionary(self):
        """Verify a first run with no users.json file is handled safely."""
        self.assertFalse(os.path.exists(app.USERS_FILE))
        self.assertEqual(app.DataManager.load_users(), {})

    def test_corrupt_json_returns_empty_dictionary(self):
        """Verify invalid JSON does not crash the loader."""
        with open(app.USERS_FILE, "w", encoding="utf-8") as file_handle:
            file_handle.write("{not valid json")
        self.assertEqual(app.DataManager.load_users(), {})

    def test_two_users_remain_separate_after_reload(self):
        """Verify data from two accounts does not mix after persistence."""
        hui = self.make_user("hui")
        alex = self.make_user("alex")
        hui.add_subject("Maths", 4)
        alex.add_subject("English", 3)

        self.assertTrue(app.DataManager.save_users({"hui": hui, "alex": alex}))
        loaded = app.DataManager.load_users()

        self.assertIn("Maths", loaded["hui"].subjects)
        self.assertNotIn("English", loaded["hui"].subjects)
        self.assertIn("English", loaded["alex"].subjects)
        self.assertNotIn("Maths", loaded["alex"].subjects)

    def test_empty_user_plan_returns_empty_dictionary(self):
        """Verify plan generation handles an empty subject collection."""
        empty_user = self.make_user()
        self.assertEqual(empty_user.generate_plan(3), {})

    def test_optional_deadline_can_be_blank(self):
        """Verify an optional subject deadline may be omitted."""
        user = self.make_user()
        saved_name = user.add_subject("Maths", 5, deadline=None)
        self.assertEqual(saved_name, "Maths")
        self.assertIsNone(user.subjects["Maths"]["deadline"])

    def test_today_is_valid_deadline_boundary(self):
        """Verify today is accepted while only earlier dates are invalid."""
        user = self.make_user()
        today = datetime.now().strftime(app.DATE_FORMAT)
        saved_name = user.add_subject("Maths", 5, deadline=today)
        self.assertEqual(saved_name, "Maths")

    def test_atomic_save_leaves_no_temporary_file(self):
        """Verify a successful save replaces the temporary file cleanly."""
        user = self.make_user()
        user.add_subject("Maths", 5)

        self.assertTrue(app.DataManager.save_users({"testuser": user}))
        self.assertTrue(os.path.exists(app.USERS_FILE))
        self.assertFalse(os.path.exists(app.TEMP_USERS_FILE))

        with open(app.USERS_FILE, "r", encoding="utf-8") as file_handle:
            saved_data = json.load(file_handle)
        self.assertIn("testuser", saved_data)


if __name__ == "__main__":
    unittest.main(verbosity=2)
