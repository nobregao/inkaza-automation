import unittest

from scripts.calculate_release_version import determine_bump, increment


class ReleaseVersionTest(unittest.TestCase):
    def test_fix_increments_patch(self):
        self.assertEqual(determine_bump("fix: corrige erro"), "patch")
        self.assertEqual(increment((1, 2, 3), "patch"), (1, 2, 4))

    def test_feature_increments_minor(self):
        self.assertEqual(determine_bump("feat(admin): adiciona tela"), "minor")
        self.assertEqual(increment((1, 2, 3), "minor"), (1, 3, 0))

    def test_breaking_change_increments_major(self):
        messages = "fix: ajuste\n\nBREAKING CHANGE: altera banco"
        self.assertEqual(determine_bump(messages), "major")
        self.assertEqual(determine_bump("feat!: altera fluxo"), "major")
        self.assertEqual(increment((1, 2, 3), "major"), (2, 0, 0))

    def test_highest_impact_wins(self):
        self.assertEqual(
            determine_bump("fix: ajuste\n\nfeat: nova função"),
            "minor",
        )

    def test_unrecognized_commits_do_not_generate_bump(self):
        self.assertIsNone(determine_bump("docs: atualiza documentação"))


if __name__ == "__main__":
    unittest.main()
