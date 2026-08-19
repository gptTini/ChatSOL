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


if __name__ == "__main__":
    unittest.main()
