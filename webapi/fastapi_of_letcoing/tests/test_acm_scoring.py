import importlib.util
import unittest
from datetime import datetime, timedelta, timezone


class AcmScoringServiceAvailabilityTests(unittest.TestCase):
    def test_acm_scoring_service_is_available(self):
        self.assertIsNotNone(importlib.util.find_spec('services.contest_scoring'))


from services.contest_scoring import compute_acm_scoreboard


class AcmScoringRulesTests(unittest.TestCase):
    def test_only_pre_ac_non_ce_rejections_contribute_to_penalty(self):
        start = datetime(2026, 1, 1, 9, 0)
        rows = compute_acm_scoreboard(
            entries=[{'entry_id': 1, 'username': 'alice'}],
            problem_indexes=['A', 'B'],
            submissions=[
                {'entry_id': 1, 'problem_index': 'A', 'verdict': 'CE', 'received_at': start + timedelta(minutes=5)},
                {'entry_id': 1, 'problem_index': 'A', 'verdict': 'WA', 'received_at': start + timedelta(minutes=10)},
                {'entry_id': 1, 'problem_index': 'A', 'verdict': 'AC', 'received_at': start + timedelta(minutes=30)},
                {'entry_id': 1, 'problem_index': 'A', 'verdict': 'WA', 'received_at': start + timedelta(minutes=35)},
                {'entry_id': 1, 'problem_index': 'B', 'verdict': 'WA', 'received_at': start + timedelta(minutes=40)},
            ],
            start_at=start,
        )
        self.assertEqual(rows[0]['solved_count'], 1)
        self.assertEqual(rows[0]['penalty'], 50)
        self.assertEqual(rows[0]['problems']['A']['wrong_before_ac'], 1)

    def test_last_accepted_time_breaks_equal_score_ties(self):
        start = datetime(2026, 1, 1, 9, 0)
        rows = compute_acm_scoreboard(
            entries=[{'entry_id': 1}, {'entry_id': 2}],
            problem_indexes=['A'],
            submissions=[
                {'entry_id': 1, 'problem_index': 'A', 'verdict': 'AC', 'received_at': start + timedelta(minutes=20)},
                {'entry_id': 2, 'problem_index': 'A', 'verdict': 'AC', 'received_at': start + timedelta(minutes=10)},
            ],
            start_at=start,
        )
        self.assertEqual([row['entry_id'] for row in rows], [2, 1])

    def test_entry_without_submissions_is_retained(self):
        rows = compute_acm_scoreboard(
            entries=[{'entry_id': 7, 'username': 'idle'}],
            problem_indexes=['A'],
            submissions=[],
            start_at=datetime(2026, 1, 1, 9, 0),
        )
        self.assertEqual(rows[0]['entry_id'], 7)
        self.assertEqual(rows[0]['solved_count'], 0)

    def test_cutoff_excludes_submissions_received_after_freeze(self):
        start = datetime(2026, 1, 1, 9, 0)
        rows = compute_acm_scoreboard(
            entries=[{'entry_id': 1}], problem_indexes=['A'],
            submissions=[
                {'entry_id': 1, 'problem_index': 'A', 'verdict': 'AC', 'received_at': start + timedelta(minutes=61)},
            ], start_at=start, cutoff_at=start + timedelta(minutes=60),
        )
        self.assertEqual(rows[0]['solved_count'], 0)

    def test_mixed_iso_and_database_timestamps_do_not_break_ranking(self):
        start = datetime(2026, 1, 1, 9, 0)
        rows = compute_acm_scoreboard(
            entries=[{'entry_id': 1}, {'entry_id': 2}], problem_indexes=['A'],
            submissions=[
                {'entry_id': 1, 'problem_index': 'A', 'verdict': 'AC', 'received_at': '2026-01-01T09:10:00+08:00'},
                {'entry_id': 2, 'problem_index': 'A', 'verdict': 'AC', 'received_at': start + timedelta(minutes=20)},
            ], start_at=start,
        )
        self.assertEqual([row['entry_id'] for row in rows], [1, 2])


if __name__ == '__main__':
    unittest.main()
