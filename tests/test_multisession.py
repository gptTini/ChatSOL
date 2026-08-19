import unittest

from chatsol.sessions import (
    ROLE_SPECS,
    SessionReport,
    SessionRole,
    WorkItem,
    build_execution_plan,
    default_feature_workstream,
    integration_ready,
    packets_for_plan,
    write_scopes_conflict,
)


class MultiSessionTests(unittest.TestCase):
    def item(self, key, role=SessionRole.IMPLEMENTER, **kwargs):
        values = {
            "title": key,
            "write_paths": (f"src/{key}.py",),
        }
        values.update(kwargs)
        return WorkItem(key=key, role=role, **values)

    def test_independent_items_share_wave(self):
        plan = build_execution_plan([self.item("a"), self.item("b")], max_parallel=4)
        self.assertEqual(len(plan.waves), 1)
        self.assertEqual({a.item.key for a in plan.waves[0]}, {"a", "b"})

    def test_write_conflicts_are_split(self):
        a = self.item("a", write_paths=("src/core",))
        b = self.item("b", write_paths=("src/core/file.py",))
        self.assertTrue(write_scopes_conflict(a, b))
        plan = build_execution_plan([a, b], max_parallel=4)
        self.assertEqual(len(plan.waves), 2)

    def test_dependencies_force_later_wave(self):
        a = self.item("a")
        b = self.item("b", depends_on=("a",))
        plan = build_execution_plan([a, b], max_parallel=4)
        self.assertEqual([[x.item.key for x in w] for w in plan.waves], [["a"], ["b"]])

    def test_max_parallel_is_respected(self):
        plan = build_execution_plan([self.item(str(i)) for i in range(5)], max_parallel=2)
        self.assertTrue(all(len(w) <= 2 for w in plan.waves))
        self.assertEqual(sum(map(len, plan.waves)), 5)

    def test_duplicate_key_rejected(self):
        with self.assertRaises(ValueError):
            build_execution_plan([self.item("a"), self.item("a")])

    def test_missing_dependency_rejected(self):
        with self.assertRaises(ValueError):
            build_execution_plan([self.item("a", depends_on=("missing",))])

    def test_cycle_rejected(self):
        a = self.item("a", depends_on=("b",))
        b = self.item("b", depends_on=("a",))
        with self.assertRaises(ValueError):
            build_execution_plan([a, b])

    def test_read_only_role_cannot_claim_write_scope(self):
        with self.assertRaises(ValueError):
            WorkItem(
                key="scan",
                title="scan",
                role=SessionRole.SCOUT,
                write_paths=("src",),
            )

    def test_packet_contains_branch_scope_and_gate(self):
        plan = build_execution_plan([self.item("core-feature")])
        packet = packets_for_plan(plan, base_branch="develop")[0]
        self.assertEqual(packet["base_branch"], "develop")
        self.assertIn("write_paths", packet)
        self.assertIn("completion_gate", packet)
        self.assertTrue(str(packet["branch"]).startswith("session/implementer-"))

    def test_default_feature_workstream_parallelizes_middle_stage(self):
        items = default_feature_workstream(
            "planner",
            code_paths=("chatsol/planner.py",),
            test_paths=("tests/test_planner.py",),
            doc_paths=("docs/planner.md",),
        )
        plan = build_execution_plan(items, max_parallel=4)
        keys = [[a.item.key for a in wave] for wave in plan.waves]
        self.assertEqual(len(keys), 4)
        self.assertEqual(len(keys[1]), 3)
        self.assertEqual({a.item.role for a in plan.waves[1]}, {
            SessionRole.IMPLEMENTER, SessionRole.TESTER, SessionRole.DOCS
        })
        self.assertEqual(plan.waves[2][0].item.role, SessionRole.REVIEWER)
        self.assertEqual(plan.waves[3][0].item.role, SessionRole.INTEGRATOR)

    def test_integration_requires_every_report_green(self):
        plan = build_execution_plan([self.item("a"), self.item("b")])
        reports = [
            SessionReport(plan.assignments[0].session_id, "passed", "abc"),
            SessionReport(plan.assignments[1].session_id, "failed", "def"),
        ]
        self.assertFalse(integration_ready(plan, reports))
        reports[1] = SessionReport(plan.assignments[1].session_id, "passed", "def")
        self.assertTrue(integration_ready(plan, reports))

    def test_passed_report_cannot_have_blocker(self):
        with self.assertRaises(ValueError):
            SessionReport("x", "passed", "abc", blockers=("conflict",))

    def test_role_specs_cover_every_role(self):
        self.assertEqual(set(ROLE_SPECS), set(SessionRole))

    def test_read_only_session_can_pass_without_commit(self):
        scout = WorkItem(
            key="scan",
            title="scan",
            role=SessionRole.SCOUT,
            read_paths=("src",),
        )
        plan = build_execution_plan([scout])
        report = SessionReport(plan.assignments[0].session_id, "passed")
        self.assertTrue(integration_ready(plan, [report]))

    def test_case_variant_keys_do_not_collide_session_ids(self):
        plan = build_execution_plan([self.item("A"), self.item("a")], max_parallel=2)
        ids = [assignment.session_id for assignment in plan.assignments]
        self.assertEqual(len(ids), len(set(ids)))

    def test_invalid_branch_prefix_is_rejected(self):
        with self.assertRaises(ValueError):
            build_execution_plan([self.item("a")], branch_prefix="bad prefix")


if __name__ == "__main__":
    unittest.main()
