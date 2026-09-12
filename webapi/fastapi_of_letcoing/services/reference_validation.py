"""参考代码只在 Worker 沙箱执行；版本栅栏阻止旧校验覆盖新题目。"""
from models.db_models import ReferenceValidationJob, ContestProblem, ContestTestcase, get_database


def dispatch_pending_validations(redis):
    for job in ReferenceValidationJob.select().where(ReferenceValidationJob.state == 'PENDING').limit(20):
        sent = redis.enqueue_with_state(f'testcase_gen:{job.problem_id}', {'status': 'pending'},
            3600, 'testcase_gen_queue', {'kind': 'reference_validation', 'job_id': job.id})
        if sent:
            ReferenceValidationJob.update(state='DISPATCHED').where(ReferenceValidationJob.id == job.id).execute()


def process_validation(task):
    from controllers.contest_problem_controller import _verify_reference_answer
    job = ReferenceValidationJob.get_or_none(ReferenceValidationJob.id == task.get('job_id'))
    if not job or job.state == 'DONE':
        return True
    problem = ContestProblem.get_by_id(job.problem_id)
    status, error = 'VALID', None
    if job.version == problem.validation_version:
        cases = [dict(input_data=tc.input_data, expected_output=tc.expected_output)
                 for tc in ContestTestcase.select().where(ContestTestcase.contest_problem == problem).order_by(ContestTestcase.sort_order)]
        try:
            if not cases:
                raise ValueError('没有可用测试数据')
            _verify_reference_answer(problem.correct_answer, problem.language, cases,
                                     problem.time_limit, problem.memory_limit)
        except ValueError as exc:
            status, error = 'INVALID', str(exc)[:1000]
        # 沙箱/数据库故障直接抛出，保留投递供恢复；不会把基础设施错误当作错误答案。
        with get_database().atomic():
            ContestProblem.update(validation_status=status, validation_error=error).where(
                (ContestProblem.id == problem.id) & (ContestProblem.validation_version == job.version)).execute()
            ReferenceValidationJob.update(state='DONE').where(ReferenceValidationJob.id == job.id).execute()
    else:
        ReferenceValidationJob.update(state='DONE').where(ReferenceValidationJob.id == job.id).execute()
    return True
