"""比赛公平性与本地判题器的关键回归测试。"""

import shutil
import unittest
from datetime import datetime, timedelta

from controllers.contest_controller import SUPPORTED_CONTEST_MODES, _safe_submission_result
from controllers.contest_problem_controller import _exec_command, _prepare_program, normalize_judge_output
from services.redis_service import RedisService
from services.judge_state import ACCEPTED, CLAIMED, QUEUED, RUNNING, can_transition
from services.contest_scoring import compute_acm_scoreboard


class ContestSecurityTests(unittest.TestCase):
    def test_only_two_scoring_modes_are_supported(self):
        self.assertEqual(SUPPORTED_CONTEST_MODES, {'ACM', 'OI'})

    def test_submission_response_never_contains_hidden_test_data(self):
        result = _safe_submission_result({
            'status': 'WA',
            'details': [{
                'passed': False,
                'status': 'WA',
                'time_used': 3,
                'expected': 'private answer',
                'actual': 'private output',
                'stderr': 'private input context',
            }],
        })
        self.assertEqual(result['details'], [{
            'passed': False, 'status': 'WA', 'time_used': 3,
        }])

    def test_output_comparison_only_ignores_conventional_trailing_whitespace(self):
        self.assertEqual(normalize_judge_output('1 2 \r\n\r\n'), '1 2')
        self.assertNotEqual(normalize_judge_output('1 2'), normalize_judge_output('12'))
        self.assertNotEqual(normalize_judge_output('1\n2'), normalize_judge_output('1 2'))

    def test_submission_state_machine_rejects_terminal_overwrite(self):
        self.assertTrue(can_transition(QUEUED, CLAIMED))
        self.assertTrue(can_transition(RUNNING, ACCEPTED) is False)
        self.assertFalse(can_transition(ACCEPTED, RUNNING))


class AcmScoreboardTests(unittest.TestCase):
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
            penalty_minutes=20,
        )
        self.assertEqual(rows[0]['solved_count'], 1)
        self.assertEqual(rows[0]['penalty'], 50)
        self.assertEqual(rows[0]['problems']['A']['wrong_before_ac'], 1)
        self.assertEqual(rows[0]['problems']['B']['wrong_before_ac'], 1)

    def test_last_accepted_time_breaks_equal_solve_and_penalty_ties(self):
        start = datetime(2026, 1, 1, 9, 0)
        rows = compute_acm_scoreboard(
            entries=[{'entry_id': 1, 'username': 'later'}, {'entry_id': 2, 'username': 'earlier'}],
            problem_indexes=['A'],
            submissions=[
                {'entry_id': 1, 'problem_index': 'A', 'verdict': 'AC', 'received_at': start + timedelta(minutes=20)},
                {'entry_id': 2, 'problem_index': 'A', 'verdict': 'AC', 'received_at': start + timedelta(minutes=10)},
            ],
            start_at=start,
            penalty_minutes=20,
        )
        self.assertEqual([row['entry_id'] for row in rows], [2, 1])
        self.assertEqual([row['rank'] for row in rows], [1, 2])

    def test_registered_entry_without_submissions_is_retained(self):
        rows = compute_acm_scoreboard(
            entries=[{'entry_id': 7, 'username': 'idle'}],
            problem_indexes=['A'],
            submissions=[],
            start_at=datetime(2026, 1, 1, 9, 0),
            penalty_minutes=20,
        )
        self.assertEqual(rows[0]['entry_id'], 7)
        self.assertEqual(rows[0]['solved_count'], 0)
        self.assertEqual(rows[0]['rank'], 1)


@unittest.skipUnless(shutil.which('javac') and shutil.which('java'), 'requires a Java toolchain')
class PreparedProgramTests(unittest.TestCase):
    def setUp(self):
        from unittest.mock import patch
        self.environment = patch.dict('os.environ', {
            'APP_ENV': 'test', 'JUDGE_BACKEND': 'local', 'ALLOW_UNSAFE_LOCAL_JUDGE': '1'})
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def test_java_main_is_compiled_once_with_a_correct_source_filename(self):
        code = (
            'public class Main { '
            'public static void main(String[] args) { System.out.println("42"); }'
            '}'
        )
        program, error, stderr = _prepare_program(code, 'java')
        self.assertIsNone(error, stderr)
        self.assertIsNotNone(program)
        try:
            first = program.run('', timeout=2, memory_limit=256)
            second = program.run('', timeout=2, memory_limit=256)
            self.assertEqual(first[0].strip(), '42')
            self.assertEqual(second[0].strip(), '42')
            self.assertIsNone(first[1])
            self.assertIsNone(second[1])
        finally:
            program.close()

    def test_each_test_point_honors_its_own_timeout(self):
        program, error, stderr = _prepare_program('while True: pass', 'python')
        self.assertIsNone(error, stderr)
        try:
            _, status, elapsed, _ = program.run('', timeout=0.1, memory_limit=128)
            self.assertEqual(status, 'TLE')
            self.assertLess(elapsed, 1000)
        finally:
            program.close()

    def test_output_limit_kills_process_group(self):
        result = _exec_command(
            ['python3', '-c', 'print("x" * 100000)'],
            '', timeout=2, memory_mb=128, output_limit=1024,
        )
        self.assertTrue(result[5])


if __name__ == '__main__':
    unittest.main()
