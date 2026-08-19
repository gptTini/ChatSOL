import contextlib
import io
import json
import unittest

from chatsol.session_cli import main


class SessionCliTests(unittest.TestCase):
    def test_feature_command_outputs_parallel_wave(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = main([
                "feature",
                "--key", "demo",
                "--code", "chatsol/demo.py",
                "--tests", "tests/test_demo.py",
                "--docs", "docs/demo.md",
            ])
        self.assertEqual(code, 0)
        payload = json.loads(out.getvalue())
        self.assertEqual(len(payload["waves"]), 4)
        self.assertEqual(len(payload["waves"][1]), 3)
        self.assertEqual(len(payload["packets"]), 6)


if __name__ == "__main__":
    unittest.main()
