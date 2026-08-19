import tempfile
from pathlib import Path
import unittest

from chatsol.autopilot import decide_autonomous_cycle
from chatsol.sessions import SessionRole


class AutopilotTests(unittest.TestCase):
    def test_undocumented_api_creates_docs_workstream(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "chatsol").mkdir()
            (root / "tests").mkdir()
            (root / "chatsol" / "demo.py").write_text("def public_api():\n    return 1\n", encoding="utf-8")
            (root / "README.md").write_text("# Demo\n", encoding="utf-8")
            decision = decide_autonomous_cycle(root, budget=4)
            self.assertIsNotNone(decision.selected)
            self.assertEqual(decision.selected.key, "document-public-api")
            roles = [a.item.role for a in decision.execution_plan.assignments]
            self.assertEqual(
                roles,
                [SessionRole.SCOUT, SessionRole.DOCS, SessionRole.REVIEWER, SessionRole.INTEGRATOR],
            )

    def test_clean_repo_can_choose_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "chatsol").mkdir()
            (root / "README.md").write_text("# Empty\n", encoding="utf-8")
            decision = decide_autonomous_cycle(root, budget=4)
            self.assertIsNone(decision.selected)
            self.assertIsNone(decision.execution_plan)

    def test_large_task_is_sliced_instead_of_starving(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "chatsol").mkdir()
            lines = []
            for index in range(24):
                lines.append(f"def api_{index}():\n    return {index}\n")
            (root / "chatsol" / "many.py").write_text("\n".join(lines), encoding="utf-8")
            (root / "README.md").write_text("# Many APIs\n", encoding="utf-8")
            decision = decide_autonomous_cycle(root, budget=4)
            self.assertIsNotNone(decision.selected)
            self.assertEqual(decision.selected.key, "document-public-api")
            self.assertEqual(decision.selected.effort, 4)
            self.assertTrue(decision.selected.title.startswith("Bounded slice:"))
            self.assertIsNotNone(decision.execution_plan)


if __name__ == "__main__":
    unittest.main()
