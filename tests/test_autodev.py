import unittest

from chatsol.autodev import TaskCandidate, choose_next, plan_cycle, rank_tasks, score_task


class AutoDevTests(unittest.TestCase):
    def candidate(self, key: str, **overrides) -> TaskCandidate:
        values = {
            "title": key,
            "impact": 5,
            "urgency": 5,
            "confidence": 0.8,
            "effort": 2,
            "risk": 1,
            "blocked": False,
        }
        values.update(overrides)
        return TaskCandidate(key=key, **values)

    def test_high_impact_task_scores_higher(self):
        low = self.candidate("low", impact=2)
        high = self.candidate("high", impact=9)
        self.assertGreater(score_task(high), score_task(low))

    def test_risk_reduces_score(self):
        safe = self.candidate("safe", risk=0)
        risky = self.candidate("risky", risk=5)
        self.assertGreater(score_task(safe), score_task(risky))

    def test_ranking_is_deterministic_for_equal_tasks(self):
        a = self.candidate("a")
        b = self.candidate("b")
        self.assertEqual([task.key for task in rank_tasks([b, a])], ["a", "b"])

    def test_choose_next_respects_budget(self):
        too_large = self.candidate("large", impact=10, effort=9)
        feasible = self.candidate("small", impact=7, effort=2)
        self.assertEqual(choose_next([too_large, feasible], budget=3).key, "small")

    def test_blocked_task_is_never_selected(self):
        blocked = self.candidate("blocked", impact=10, effort=1, blocked=True)
        ready = self.candidate("ready", impact=4, effort=1)
        self.assertEqual(choose_next([blocked, ready], budget=3).key, "ready")

    def test_cycle_never_contains_blocked_tasks(self):
        blocked = self.candidate("blocked", impact=10, effort=1, blocked=True)
        ready = self.candidate("ready", impact=4, effort=1)
        self.assertEqual([task.key for task in plan_cycle([blocked, ready], budget=5)], ["ready"])

    def test_cycle_stays_inside_budget(self):
        tasks = [
            self.candidate("a", effort=2),
            self.candidate("b", effort=2),
            self.candidate("c", effort=2),
        ]
        plan = plan_cycle(tasks, budget=4)
        self.assertLessEqual(sum(task.effort for task in plan), 4)
        self.assertEqual(len(plan), 2)

    def test_zero_budget_selects_nothing(self):
        task = self.candidate("a", effort=1)
        self.assertIsNone(choose_next([task], budget=0))
        self.assertEqual(plan_cycle([task], budget=0), [])


if __name__ == "__main__":
    unittest.main()
