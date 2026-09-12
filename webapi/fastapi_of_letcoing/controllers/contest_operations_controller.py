"""比赛运维 API；与既有页面解耦，不改变前端 UI。"""
import json
from functools import wraps

from flask import request, g
from middleware.auth_middleware import RateLimitMiddleware
from flask_restx import Namespace, Resource
from peewee import DoesNotExist, IntegrityError

from controllers.contest_controller import _get_current_user
from models import db_models as m
from services import contest_operations as ops

api = Namespace('contest_operations', description='比赛控制、复判、队伍与裁判答疑')


def errors(function):
    @wraps(function)
    def wrapped(*args, **kwargs):
        try:
            if request.method != 'GET':
                actor = _get_current_user()
                if not actor:
                    raise PermissionError('请先登录')
                g.current_user = actor.to_dict()
            result = function(*args, **kwargs)
            if isinstance(result, tuple):
                headers = dict(result[2]) if len(result) > 2 else {}
                headers.update({'Cache-Control': 'private, no-store', 'Vary': 'Authorization'})
                return result[0], result[1], headers
            return result
        except PermissionError as exc:
            return {'error': str(exc)}, 403
        except (DoesNotExist, KeyError):
            return {'error': '资源不存在'}, 404
        except (ValueError, TypeError, IntegrityError) as exc:
            return {'error': str(exc) if isinstance(exc, ValueError) else '请求格式无效或发生冲突'}, 409
    return wrapped


def body():
    value = request.get_json(silent=True)
    if not isinstance(value, dict):
        raise ValueError('需要 JSON 对象')
    return value


@api.route('/<int:contest_id>/thaw')
class Thaw(Resource):
    @errors
    @RateLimitMiddleware.rate_limit(max_requests=20, window_seconds=60)
    def post(self, contest_id):
        data = body()
        contest = ops.thaw_contest(contest_id, _get_current_user(), data.get('reason'))
        return {'thawed_at': contest.thawed_at.isoformat()}, 200


@api.route('/<int:contest_id>/teams')
class Teams(Resource):
    @errors
    @RateLimitMiddleware.rate_limit(max_requests=20, window_seconds=60)
    def post(self, contest_id):
        data = body()
        team = ops.create_team(contest_id, _get_current_user(), data.get('name'), data.get('member_ids'))
        return {'id': team.id, 'name': team.name}, 201


@api.route('/<int:contest_id>/roles')
class Roles(Resource):
    @errors
    @RateLimitMiddleware.rate_limit(max_requests=20, window_seconds=60)
    def post(self, contest_id):
        actor = _get_current_user()
        ops.require(contest_id, actor, 'control')
        data = body()
        if data.get('role') not in {'director', 'jury', 'setter', 'operator', 'none'}:
            raise ValueError('无效比赛角色')
        user = m.User.get_by_id(int(data['user_id']))
        with m.get_database().atomic():
            ops.lock_contest(contest_id)
            ops.require(contest_id, actor, 'control')
            role, _ = m.ContestRole.get_or_create(contest=contest_id, user=user, defaults={'role': data['role']})
            role.role = data['role']; role.save()
            ops.audit(contest_id, actor, 'role.update', data.get('reason'), {'user_id': user.id, 'role': role.role})
        return {'success': True}, 200


@api.route('/<int:contest_id>/rejudges')
class Rejudges(Resource):
    @errors
    @RateLimitMiddleware.rate_limit(max_requests=20, window_seconds=60)
    def post(self, contest_id):
        data = body()
        batch = ops.create_rejudge(contest_id, _get_current_user(), data.get('submission_ids'), data.get('reason'))
        return {'batch_id': batch.id, 'state': batch.state}, 202


@api.route('/<int:contest_id>/rejudges/<int:batch_id>')
class RejudgeReview(Resource):
    @errors
    def get(self, contest_id, batch_id):
        ops.require(contest_id, _get_current_user(), 'rejudge')
        batch = m.RejudgeBatch.get(m.RejudgeBatch.id == batch_id, m.RejudgeBatch.contest == contest_id)
        candidates = list(m.ContestSubmission.select().where(m.ContestSubmission.rejudge_batch == batch))
        originals = {s.id: s for s in m.ContestSubmission.select(m.ContestSubmission.id, m.ContestSubmission.status).where(
            m.ContestSubmission.id.in_([c.rejudge_of for c in candidates]))}
        return {'state': batch.state, 'changes': [{'submission_id': c.rejudge_of,
            'before': originals[c.rejudge_of].status, 'after': c.status} for c in candidates]}, 200

    @errors
    @RateLimitMiddleware.rate_limit(max_requests=20, window_seconds=60)
    def post(self, contest_id, batch_id):
        actor = _get_current_user()
        ops.require(contest_id, actor, 'rejudge')
        m.RejudgeBatch.get(m.RejudgeBatch.id == batch_id, m.RejudgeBatch.contest == contest_id)
        data = body()
        if data.get('action') not in {'apply', 'cancel'}:
            raise ValueError('action 必须为 apply 或 cancel')
        batch = ops.apply_rejudge(batch_id, actor, data.get('reason'), cancel=data['action'] == 'cancel', password=data.get('password'), totp=data.get('totp'))
        return {'state': batch.state}, 200


@api.route('/<int:contest_id>/submissions/<int:submission_id>/override')
class Override(Resource):
    @errors
    @RateLimitMiddleware.rate_limit(max_requests=20, window_seconds=60)
    def post(self, contest_id, submission_id):
        data = body()
        result = ops.override_judgement(contest_id, submission_id, _get_current_user(),
            data.get('verdict'), data.get('reason'), data.get('password'), data.get('totp'))
        return {'submission_id': result.id, 'status': result.status}, 200


@api.route('/<int:contest_id>/clarifications')
class Clarifications(Resource):
    @errors
    def get(self, contest_id):
        actor = _get_current_user()
        jury = ops.allowed(contest_id, actor, 'jury')
        if not jury:
            ops.participant(contest_id, actor)
        rows = m.ContestClarification.select().where(m.ContestClarification.contest == contest_id)
        if not jury:
            rows = rows.where((m.ContestClarification.author == ops.entry_user(contest_id, actor.id)) | m.ContestClarification.broadcast)
        rows = rows.where(m.ContestClarification.id > max(0, int(request.args.get('after', 0))))
        return [{'id': r.id, 'question': r.question, 'answer': r.answer, 'claimed_by': r.claimed_by}
            for r in rows.order_by(m.ContestClarification.id).limit(100)], 200

    @errors
    @RateLimitMiddleware.rate_limit(max_requests=20, window_seconds=60)
    def post(self, contest_id):
        question = ops.ask_clarification(contest_id, _get_current_user(), body().get('question'))
        return {'id': question.id}, 201


@api.route('/<int:contest_id>/clarifications/<int:question_id>')
class ClarificationAnswer(Resource):
    @errors
    @RateLimitMiddleware.rate_limit(max_requests=20, window_seconds=60)
    def post(self, contest_id, question_id):
        actor = _get_current_user()
        ops.require(contest_id, actor, 'jury')
        data = body()
        with m.get_database().atomic():
            ops.lock_contest(contest_id)
            ops.require(contest_id, actor, 'jury')
            question = m.ContestClarification.get(m.ContestClarification.id == question_id,
                m.ContestClarification.contest == contest_id)
            if data.get('action') == 'claim':
                if question.claimed_by and question.claimed_by != actor.id:
                    raise ValueError('已由其他裁判认领')
                question.claimed_by = actor.id; question.save()
            else:
                if type(data.get('broadcast', False)) is not bool:
                    raise ValueError('broadcast 必须为布尔值')
                ops.answer_clarification(question_id, actor, data.get('answer'), data.get('broadcast', False))
        return {'id': question.id}, 200


@api.route('/<int:contest_id>/events')
class Events(Resource):
    @errors
    def get(self, contest_id):
        rows = ops.events_for(contest_id, _get_current_user(), request.args.get('after', 0))
        return {'events': rows, 'next_cursor': rows[-1]['id'] if rows else int(request.args.get('after', 0))}, 200, {'Cache-Control': 'private, no-store'}


@api.route('/<int:contest_id>/audit')
class Audit(Resource):
    @errors
    def get(self, contest_id):
        ops.require(contest_id, _get_current_user(), 'control')
        rows = m.ContestAudit.select().where(m.ContestAudit.contest == contest_id,
            m.ContestAudit.id > max(0, int(request.args.get('after', 0)))).order_by(m.ContestAudit.id).limit(100)
        return [{'id': r.id, 'actor_id': r.actor_id, 'action': r.action, 'reason': r.reason,
                 'data': json.loads(r.payload)} for r in rows], 200, {'Cache-Control': 'private, no-store'}


@api.route('/<int:contest_id>/problems/<int:problem_id>/packages')
class Packages(Resource):
    @errors
    @RateLimitMiddleware.rate_limit(max_requests=20, window_seconds=60)
    def post(self, contest_id, problem_id):
        actor = _get_current_user()
        ops.require(contest_id, actor, 'package')
        m.ContestProblem.get(m.ContestProblem.id == problem_id, m.ContestProblem.contest == contest_id)
        from services.contest_packages import stage_package
        data = body()
        package = stage_package(problem_id, actor, data.get('package'), data.get('reason'))
        return {'digest': package.digest, 'state': package.validation_state}, 202


@api.route('/<int:contest_id>/packages/<string:digest>')
class PackageReview(Resource):
    @errors
    def get(self, contest_id, digest):
        ops.require(contest_id, _get_current_user(), 'package')
        package = m.ContestPackage.select().join(m.ContestProblem).where(m.ContestPackage.digest == digest,
            m.ContestProblem.contest == contest_id).get()
        return {'digest': digest, 'state': package.validation_state, 'error': package.validation_error}, 200

    @errors
    @RateLimitMiddleware.rate_limit(max_requests=20, window_seconds=60)
    def post(self, contest_id, digest):
        actor = _get_current_user()
        ops.require(contest_id, actor, 'control')
        m.ContestPackage.select().join(m.ContestProblem).where(m.ContestPackage.digest == digest,
            m.ContestProblem.contest == contest_id).get()
        from services.contest_packages import activate_package
        activate_package(digest, actor, body().get('reason'))
        return {'digest': digest, 'active': True}, 200


@api.route('/<int:contest_id>/rules')
class Rules(Resource):
    @errors
    @RateLimitMiddleware.rate_limit(max_requests=20, window_seconds=60)
    def post(self, contest_id):
        actor = _get_current_user()
        ops.require(contest_id, actor, 'control')
        data = body()
        languages = data.get('allowed_languages')
        if not isinstance(languages, list) or not languages or any(x not in {'cpp','python','java','go','javascript'} for x in languages):
            raise ValueError('比赛语言无效')
        limit = data.get('active_submission_limit', 3)
        penalty = data.get('penalty_time', 20)
        if type(limit) is not int or not 1 <= limit <= 10 or type(penalty) is not int or not 0 <= penalty <= 120:
            raise ValueError('比赛限制或罚时无效')
        with m.get_database().atomic():
            contest = ops.lock_contest(contest_id)
            ops.require(contest_id, actor, 'control')
            if contest.lifecycle_state not in {'DRAFT', 'READY'}:
                raise ValueError('发布后比赛规则已锁定')
            contest.allowed_languages = json.dumps(sorted(set(languages)))
            contest.active_submission_limit = limit
            contest.penalty_time = penalty
            contest.save()
            ops.audit(contest_id, actor, 'rules.update', data.get('reason'),
                {'allowed_languages': languages, 'active_submission_limit': limit, 'penalty_time': penalty})
        return {'success': True}, 200


@api.route('/<int:contest_id>/health')
class Health(Resource):
    @errors
    def get(self, contest_id):
        actor = _get_current_user()
        if not ops.allowed(contest_id, actor, 'control'):
            ops.require(contest_id, actor, 'health')
        from services.contest_metrics import competition_health
        return competition_health(contest_id), 200, {'Cache-Control': 'private, no-store'}
