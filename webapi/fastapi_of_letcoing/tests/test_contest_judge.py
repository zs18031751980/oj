"""比赛公平性与本地判题器的关键回归测试。"""

import shutil
import unittest

IMPORT_ERROR = None
try:
    from controllers.contest_controller import SUPPORTED_CONTEST_MODES, _safe_submission_result
    from controllers.contest_problem_controller import _exec_command, _prepare_program, normalize_judge_output
    from services.redis_service import RedisService
    from services.judge_state import ACCEPTED, CLAIMED, QUEUED, RUNNING, can_transition
except ModuleNotFoundError as exc:
    # 让刚拉取源码但尚未安装 requirements 的开发环境得到明确的跳过结果，
    # 而不是把环境问题误报成业务回归。
    IMPORT_ERROR = exc


@unittest.skipIf(IMPORT_ERROR is not None, 'requires backend dependencies')
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


class _NoopLogger:
    def error(self, *args):
        raise AssertionError(args)


class _ListClient:
    def __init__(self):
        self.lists = {}

    def lpush(self, key, *values):
        values_list = self.lists.setdefault(key, [])
        for value in values:
            values_list.insert(0, value)
        return len(values_list)

    def rpoplpush(self, source, destination):
        values = self.lists.setdefault(source, [])
        if not values:
            return None
        value = values.pop()
        self.lists.setdefault(destination, []).insert(0, value)
        return value

    def lrem(self, key, count, value):
        values = self.lists.setdefault(key, [])
        try:
            values.remove(value)
            return 1
        except ValueError:
            return 0


@unittest.skipIf(IMPORT_ERROR is not None, 'requires backend dependencies')
class ReliableQueueTests(unittest.TestCase):
    def test_claim_ack_and_recovery_never_drop_or_duplicate_a_task(self):
        service = object.__new__(RedisService)
        service._client = _ListClient()
        service._connected = True
        service._logger_service = _NoopLogger()
        service.list_push('q', {'id': 1}, {'id': 2})

        first = service.list_claim('q', 'q:processing')
        second = service.list_claim('q', 'q:processing')
        self.assertEqual({first['payload']['id'], second['payload']['id']}, {1, 2})
        self.assertTrue(service.list_ack('q:processing', first['receipt']))
        self.assertEqual(service.list_recover('q:processing', 'q'), 1)

        recovered = service.list_claim('q', 'q:processing')
        self.assertEqual(recovered['payload']['id'], second['payload']['id'])
        self.assertTrue(service.list_ack('q:processing', recovered['receipt']))


@unittest.skipIf(IMPORT_ERROR is not None, 'requires backend dependencies')
@unittest.skipUnless(shutil.which('javac') and shutil.which('java'), 'requires a Java toolchain')
class PreparedProgramTests(unittest.TestCase):
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
