import unittest

from chatsol.autodev import RepoSignals, plan_from_signals, propose_tasks


class RepoSignalTests(unittest.TestCase):
    def test_clean_repository_proposes_no_work(self):
        self.assertEqual(propose_tasks(RepoSignals()), [])

    def test_security_alert_is_top_priority(self):
        signals = RepoSignals(security_alerts=1, failing_tests=2, todo_count=20)
        plan = plan_from_signals(signals, budget=10)
        self.assertTrue(plan)
        self.assertEqual(plan[0].key, "security-alerts")

    def test_budget_can_skip_expensive_priority_for_feasible_work(self):
        signals = RepoSignals(security_alerts=8, failing_tests=1)
        plan = plan_from_signals(signals, budget=2)
        self.assertEqual([task.key for task in plan], ["repair-failing-tests"])

    def test_generated_keys_are_unique(self):
        signals = RepoSignals(
            security_alerts=1,
            failing_tests=1,
            flaky_tests=1,
            stale_dependencies=1,
            undocumented_public_apis=1,
            todo_count=1,
            coverage_gap=10,
        )
        tasks = propose_tasks(signals)
        self.assertEqual(len({task.key for task in tasks}), len(tasks))

    def test_negative_signal_is_rejected(self):
        with self.assertRaises(ValueError):
            RepoSignals(failing_tests=-1)

    def test_boolean_counter_is_rejected(self):
        with self.assertRaises(ValueError):
            RepoSignals(failing_tests=True)

    def test_coverage_gap_bounds_are_enforced(self):
        with self.assertRaises(ValueError):
            RepoSignals(coverage_gap=-0.1)
        with self.assertRaises(ValueError):
            RepoSignals(coverage_gap=100.1)

    def test_generated_effort_is_bounded(self):
        signals = RepoSignals(
            security_alerts=100,
            failing_tests=100,
            flaky_tests=100,
            stale_dependencies=100,
            undocumented_public_apis=100,
            todo_count=100,
            coverage_gap=100,
        )
        tasks = propose_tasks(signals)
        self.assertTrue(tasks)
        self.assertTrue(all(0 < task.effort <= 8 for task in tasks))


if __name__ == "__main__":
    unittest.main()
