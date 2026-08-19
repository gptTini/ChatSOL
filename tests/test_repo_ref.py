import unittest

from chatsol.repo_ref import RepoRef, parse_repo_ref


class RepoRefTests(unittest.TestCase):
    def test_owner_repo(self):
        self.assertEqual(parse_repo_ref("gptTini/ChatSOL"), RepoRef("gptTini", "ChatSOL"))

    def test_https_url(self):
        self.assertEqual(
            parse_repo_ref("https://github.com/gptTini/ChatSOL.git"),
            RepoRef("gptTini", "ChatSOL"),
        )

    def test_surrounding_whitespace(self):
        self.assertEqual(parse_repo_ref("  gptTini/ChatSOL  ").full_name, "gptTini/ChatSOL")

    def test_ssh_url(self):
        self.assertEqual(
            parse_repo_ref("git@github.com:gptTini/ChatSOL.git"),
            RepoRef("gptTini", "ChatSOL"),
        )

    def test_reject_non_github_https_host(self):
        with self.assertRaises(ValueError):
            parse_repo_ref("https://evil.example/gptTini/ChatSOL.git")

    def test_reject_non_github_ssh_host(self):
        with self.assertRaises(ValueError):
            parse_repo_ref("git@evil.example:gptTini/ChatSOL.git")

    def test_reject_extra_path_components(self):
        with self.assertRaises(ValueError):
            parse_repo_ref("https://github.com/gptTini/ChatSOL/issues/1")


if __name__ == "__main__":
    unittest.main()
