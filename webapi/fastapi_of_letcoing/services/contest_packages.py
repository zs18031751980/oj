"""内容寻址题包和确定性检查器。题包包含秘密，只在裁判/Worker 边界使用。"""
import hashlib
import json
import math
import os

from models.db_models import ContestPackage, ContestTestcase


def canonical(data):
    return json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False)


def validate_checker(config):
    if not isinstance(config, dict) or config.get('checker', 'text') not in {'text', 'exact', 'tokens', 'float', 'custom'}:
        raise ValueError('Unsupported checker')
    if config.get('checker') == 'custom':
        if config.get('language') not in {'python', 'cpp'} or not isinstance(config.get('code'), str) or not 1 <= len(config['code'].encode()) <= 65536:
            raise ValueError('Invalid checker program')
    for key in ('absolute_tolerance', 'relative_tolerance'):
        value = float(config.get(key, 1e-6))
        if not math.isfinite(value) or not 0 <= value <= .01:
            raise ValueError('Invalid tolerance')


class OutputChecker:
    def __init__(self, config):
        validate_checker(config)
        self.config, self.program = config, None
        if config.get('checker') == 'custom':
            from controllers.contest_problem_controller import _prepare_program
            self.program, error, _ = _prepare_program(config['code'], config['language'])
            if error or self.program is None:
                raise RuntimeError('检查器编译失败')

    def check(self, actual, expected, input_data=''):
        if self.program is None:
            return check_output(actual, expected, self.config, input_data)
        _, error, _, _ = self.program.run(canonical({'input': input_data, 'actual': actual, 'expected': expected}), 2, 256)
        status = self.program.last_metrics.get('exit_code')
        if status == 0 and error is None:
            return True
        if status == 1:
            return False
        raise RuntimeError('检查器执行失败')

    def close(self):
        if self.program:
            self.program.close()


def check_output(actual, expected, config, input_data=''):
    if config.get('checker') == 'custom':
        checker = OutputChecker(config)
        try:
            return checker.check(actual, expected, input_data)
        finally:
            checker.close()
    mode = config.get('checker', 'text')
    if mode == 'text':
        from controllers.contest_problem_controller import normalize_judge_output
        return normalize_judge_output(actual) == normalize_judge_output(expected)
    if mode == 'exact':
        return actual == expected
    a, b = actual.split(), expected.split()
    if len(a) != len(b):
        return False
    if mode == 'tokens':
        return a == b
    if mode != 'float':
        raise ValueError('Unsupported checker')
    absolute = float(config.get('absolute_tolerance', 1e-6))
    relative = float(config.get('relative_tolerance', 1e-6))
    if not all(math.isfinite(v) and 0 <= v <= .01 for v in (absolute, relative)):
        raise ValueError('Invalid tolerance')
    for x, y in zip(a, b):
        try:
            x, y = float(x), float(y)
        except ValueError:
            return False
        if not math.isfinite(x) or not math.isfinite(y) or abs(x-y) > max(absolute, relative*abs(y)):
            return False
    return True


def publish_package(problem, actor_id=None):
    cases = [{'input_data': tc.input_data, 'expected_output': tc.expected_output,
              'is_sample': tc.is_sample} for tc in ContestTestcase.select().where(
                  ContestTestcase.contest_problem == problem).order_by(ContestTestcase.sort_order, ContestTestcase.id)]
    if not cases:
        raise ValueError('题包没有测试数据')
    checker = json.loads(problem.checker_config)
    validate_checker(checker)
    payload = canonical({'problem_id': problem.id, 'time_limit': problem.time_limit,
        'memory_limit': problem.memory_limit, 'checker_config': checker, 'cases': cases,
        'language': problem.language, 'reference': problem.correct_answer,
        'runtime_image': os.environ.get('JUDGE_SANDBOX_IMAGE', 'letcoding-sandbox:local'),
        'rules_version': problem.contest.rules_version, 'language_limits': {}})
    digest = hashlib.sha256(payload.encode()).hexdigest()
    ContestPackage.insert(digest=digest, problem=problem, payload=payload, actor_id=actor_id).on_conflict_ignore().execute()
    return ContestPackage.get_by_id(digest)


def load_package(digest):
    payload = ContestPackage.get_by_id(digest).payload
    if hashlib.sha256(payload.encode()).hexdigest() != digest:
        raise ValueError('Package digest mismatch')
    return json.loads(payload)


def stage_package(problem_id, actor, data, reason):
    """校验结构并排队，API 请求不执行参考代码/检查器。"""
    from models import db_models as m
    from services.contest_operations import require, audit, lock_contest, text_field
    problem = m.ContestProblem.get_by_id(problem_id)
    require(problem.contest_id, actor, 'package')
    if not isinstance(data, dict):
        raise ValueError('无效题包')
    cases = data.get('cases')
    if not isinstance(cases, list) or not 1 <= len(cases) <= 1000:
        raise ValueError('题包需要 1 至 1000 个测试点')
    normalized = []
    for case in cases:
        if not isinstance(case, dict) or not all(isinstance(case.get(k), str) for k in ('input_data', 'expected_output')):
            raise ValueError('测试数据必须为字符串')
        normalized.append({k: case[k] for k in ('input_data', 'expected_output')} | {'is_sample': case.get('is_sample') is True})
    if all(case['is_sample'] for case in normalized):
        raise ValueError('缺少隐藏测试')
    config = data.get('checker_config', {'checker': 'text'})
    validate_checker(config)
    for spec in [data.get('validator')] + data.get('known_wrong', []):
        if spec is not None:
            validate_checker({'checker': 'custom', **spec})
    language = data.get('language', problem.language)
    if language not in {'cpp', 'python', 'java', 'go', 'javascript'}:
        raise ValueError('无效参考语言')
    time_limit, memory_limit = data.get('time_limit', problem.time_limit), data.get('memory_limit', problem.memory_limit)
    if type(time_limit) is not int or not 1 <= time_limit <= 30000 or type(memory_limit) is not int or not 16 <= memory_limit <= 2048:
        raise ValueError('判题资源限制无效')
    payload = canonical({'problem_id': problem.id, 'reference': text_field(data.get('reference', problem.correct_answer), 131072),
        'language': language, 'cases': normalized, 'checker_config': config,
        'time_limit': time_limit, 'memory_limit': memory_limit,
        'validator': data.get('validator'), 'known_wrong': data.get('known_wrong', []),
        'language_limits': data.get('language_limits', {}),
        'runtime_image': os.environ.get('JUDGE_SANDBOX_IMAGE', 'letcoding-sandbox:local'),
        'rules_version': problem.contest.rules_version})
    parsed = json.loads(payload)
    for runtime_language in ('cpp', 'python', 'java', 'go', 'javascript'):
        runtime_limits(parsed, runtime_language)
    if len(payload.encode()) > 8 * 1024 * 1024:
        raise ValueError('题包超过 8 MiB')
    digest = hashlib.sha256(payload.encode()).hexdigest()
    with m.get_database().atomic():
        lock_contest(problem.contest_id)
        m.ContestPackage.insert(digest=digest, problem=problem, payload=payload,
            actor_id=actor.id, validation_state='PENDING').on_conflict_ignore().execute()
        audit(problem.contest_id, actor, 'package.stage', reason, {'digest': digest})
    return m.ContestPackage.get_by_id(digest)


def validate_staged_package(digest):
    """只在验证 Worker 或显式运维命令运行。标准程序通过且错误程序被拒绝。"""
    from controllers.contest_problem_controller import _prepare_program
    package = ContestPackage.get_by_id(digest)
    if package.validation_state not in {'PENDING', 'RUNNING'}:
        return
    package.validation_state = 'RUNNING'; package.save()
    programs = []
    checker = None
    try:
        data = load_package(digest)
        if os.environ.get('APP_ENV') == 'production' and data['runtime_image'] != os.environ.get('JUDGE_SANDBOX_IMAGE'):
            raise ValueError('验证镜像与题包不一致')
        checker = OutputChecker(data['checker_config'])
        def prepare(spec):
            program, error, _ = _prepare_program(spec['code'], spec['language'])
            if error or program is None:
                raise ValueError('题包程序编译失败')
            programs.append(program)
            return program
        reference = prepare({'code': data['reference'], 'language': data['language']})
        validator = prepare(data['validator']) if data.get('validator') else None
        for case in data['cases']:
            if validator:
                _, error, _, _ = validator.run(case['input_data'], 2, 256)
                if error or validator.last_metrics['exit_code'] != 0:
                    raise ValueError('输入验证器拒绝测试数据')
            actual, error, _, _ = reference.run(case['input_data'], *runtime_limits(data, data['language']))
            if error or not checker.check(actual or '', case['expected_output'], case['input_data']):
                raise ValueError('标准程序未通过全部测试')
        for spec in data.get('known_wrong', []):
            wrong = prepare(spec)
            rejected = False
            for case in data['cases']:
                actual, error, _, _ = wrong.run(case['input_data'], *runtime_limits(data, spec['language']))
                if error or not checker.check(actual or '', case['expected_output'], case['input_data']):
                    rejected = True; break
            if not rejected:
                raise ValueError('已知错误程序未被拒绝')
        package.validation_state, package.validation_error = 'VALID', None
    except Exception as exc:
        package.validation_state, package.validation_error = 'INVALID', str(exc)[:500]
    finally:
        if checker:
            checker.close()
        for program in programs:
            program.close()
    package.save(only=[ContestPackage.validation_state, ContestPackage.validation_error])


def activate_package(digest, actor, reason):
    from models import db_models as m
    from services.contest_operations import require, lock_contest, audit
    package = m.ContestPackage.get_by_id(digest)
    require(package.problem.contest_id, actor, 'control')
    with m.get_database().atomic():
        lock_contest(package.problem.contest_id)
        package = m.ContestPackage.get_by_id(digest)
        if package.validation_state != 'VALID':
            raise ValueError('题包尚未验证通过')
        data = load_package(digest)
        m.ContestProblem.update(package_digest=digest, time_limit=data['time_limit'], memory_limit=data['memory_limit'],
            checker_config=canonical(data['checker_config']), correct_answer=data['reference'], language=data['language']).where(m.ContestProblem.id == package.problem_id).execute()
        audit(package.problem.contest_id, actor, 'package.activate', reason, {'digest': digest})
        from services.contest_operations import emit
        emit(package.problem.contest_id, 'problem_revision', {'problem_id': package.problem_id,
            'time_limit': data['time_limit'], 'memory_limit': data['memory_limit']}, 'public')
    return package


def dispatch_package_validation(cache):
    from datetime import datetime, timedelta
    for package in ContestPackage.select().where(ContestPackage.validation_state.in_(['PENDING', 'RUNNING'])).limit(50):
        if package.validation_state == 'RUNNING' and package.updated_at > datetime.now()-timedelta(minutes=5):
            continue
        # Receipt recovery handles worker death; the DB row keeps intent if Redis disappears.
        key = f'judge:enqueued:testcase_gen_queue:package:{package.digest}'
        if package.validation_state == 'RUNNING' and cache._client.exists(key):
            continue
        cache.enqueue_with_state(f'package:{package.digest}', {'status': 'pending'}, 3600,
            'testcase_gen_queue', {'job_id': 'package:'+package.digest, 'package_digest': package.digest})


def runtime_limits(package, language):
    profiles = package.get('language_limits', {})
    if not isinstance(profiles, dict):
        raise ValueError('语言资源配置无效')
    profile = profiles.get(language, {})
    if not isinstance(profile, dict):
        raise ValueError('语言资源配置无效')
    factor, extra = float(profile.get('cpu_factor', 1)), profile.get('memory_extra_mb', 0)
    if not math.isfinite(factor) or not .1 <= factor <= 5 or type(extra) is not int or not 0 <= extra <= 512:
        raise ValueError('语言资源配置超出范围')
    cpu, memory = package['time_limit']/1000*factor, package['memory_limit']+extra
    if not 0 < cpu <= 150 or not 16 <= memory <= 2048:
        raise ValueError('实际资源预算超出范围')
    return cpu, memory
