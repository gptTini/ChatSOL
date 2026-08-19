import tempfile
from pathlib import Path
import unittest

from chatsol.inspector import inspect_local_repo, signals_from_snapshot


class InspectorTests(unittest.TestCase):
    def test_scans_public_api_docs_and_todos(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "chatsol").mkdir()
            (root / "tests").mkdir()
            (root / "docs").mkdir()
            (root / "chatsol" / "demo.py").write_text(
                "def public_api():\n    return 1\n\n"
                "def _private():\n    return 2\n\n"
                "# TODO improve this\n",
                encoding="utf-8",
            )
            (root / "tests" / "test_demo.py").write_text(
                "import unittest\n\nclass Demo(unittest.TestCase):\n    def test_ok(self): self.assertTrue(True)\n",
                encoding="utf-8",
            )
            (root / "README.md").write_text("# Demo\n", encoding="utf-8")
            snapshot = inspect_local_repo(root)
            self.assertEqual(snapshot.python_files, 2)
            self.assertEqual(snapshot.test_files, 1)
            self.assertEqual(snapshot.todo_count, 1)
            self.assertIn("chatsol.demo.public_api", snapshot.public_apis)
            self.assertIn("chatsol.demo.public_api", snapshot.undocumented_public_apis)
            signals = signals_from_snapshot(snapshot)
            self.assertEqual(signals.undocumented_public_apis, 1)

    def test_documented_simple_name_counts_as_documented(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "chatsol").mkdir()
            (root / "chatsol" / "demo.py").write_text("def public_api():\n    return 1\n", encoding="utf-8")
            (root / "README.md").write_text("Use `public_api`.", encoding="utf-8")
            snapshot = inspect_local_repo(root)
            self.assertEqual(snapshot.undocumented_public_apis, ())


if __name__ == "__main__":
    unittest.main()
