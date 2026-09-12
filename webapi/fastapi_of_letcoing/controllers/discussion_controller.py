from datetime import datetime, timezone
from flask import request
from flask_restx import Namespace, Resource, fields
from models.db_models import Discussion, DiscussionReply, DiscussionLike, DiscussionReplyLike, User, get_database
from core.db_robust import ensure_connected
from core.di_container import inject
from interfaces.service_interfaces import IJWTService

api = Namespace('discussions', description='讨论区接口')

discussion_model = api.model('Discussion', {
    'id': fields.Integer(description='讨论ID'),
    'title': fields.String(description='标题'),
    'content': fields.String(description='内容'),
    'author_id': fields.Integer(description='作者ID'),
    'author_name': fields.String(description='作者名'),
    'category': fields.String(description='分类'),
    'tags': fields.String(description='标签'),
    'reply_count': fields.Integer(description='回复数'),
    'like_count': fields.Integer(description='点赞数'),
    'view_count': fields.Integer(description='浏览数'),
    'is_pinned': fields.Boolean(description='是否置顶'),
    'is_liked': fields.Boolean(description='当前用户是否点赞'),
    'created_at': fields.String(description='创建时间'),
})

discussion_input = api.model('DiscussionInput', {
    'title': fields.String(required=True, description='标题'),
    'content': fields.String(required=True, description='内容(Markdown)'),
    'category': fields.String(default='全部', description='分类'),
    'tags': fields.String(description='标签(逗号分隔)'),
})

reply_input = api.model('ReplyInput', {
    'content': fields.String(required=True, description='回复内容'),
})


def _get_current_user():
    """从 JWT 获取当前用户"""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None
    jwt_service = inject(IJWTService)
    user_info = jwt_service.verify_access_token(auth_header[7:])
    if not user_info:
        return None
    try:
        return User.get_by_id(int(user_info.get('id', 0)))
    except Exception:
        return None


def _page():
    from werkzeug.exceptions import BadRequest
    try:
        return min(100, max(1, int(request.args.get('limit', 30)))), max(0, int(request.args.get('offset', 0)))
    except ValueError as exc:
        raise BadRequest('分页参数无效') from exc


def _lock(model, row_id):
    query = model.select().where(model.id == row_id)
    if get_database().__class__.__name__ != 'SqliteDatabase':
        query = query.for_update()
    return query.get()


def _serialize(row, liked=False):
    data = row.to_dict()
    data['author_id'] = data.pop('author', row.author_id)
    data['author_name'] = row.author.username or '匿名'
    data['is_liked'] = liked
    return data


def _liked_ids(model, field, rows, user):
    if not user or not rows:
        return set()
    return {getattr(like, field.name + '_id') for like in model.select(field).where(
        (field.in_([row.id for row in rows])) & (model.user == user.id))}


def _replies(discussion_id, user):
    limit, offset = _page()
    rows = list(DiscussionReply.select(DiscussionReply, User).join(User).where(
        DiscussionReply.discussion == discussion_id).order_by(DiscussionReply.created_at, DiscussionReply.id)
        .limit(limit).offset(offset))
    liked = _liked_ids(DiscussionReplyLike, DiscussionReplyLike.reply, rows, user)
    return [_serialize(row, row.id in liked) for row in rows]


def _content(data):
    from werkzeug.exceptions import BadRequest
    value = data.get('content')
    if not isinstance(value, str) or not value.strip() or len(value.encode()) > 65536:
        raise BadRequest('内容必须为非空字符串且不超过 64 KiB')
    return value.strip()


@api.route('/')
class DiscussionListController(Resource):
    def get(self):
        from peewee import fn, SQL
        limit, offset = _page()
        user = _get_current_user()
        columns = [f for f in Discussion._meta.sorted_fields if f.name != 'content']
        query = Discussion.select(*columns, fn.SUBSTR(Discussion.content, 1, 200).alias('content'), User).join(User)
        category = request.args.get('category', '').strip()
        if category and category != '全部':
            query = query.where(Discussion.category == category)
        if get_database().__class__.__name__ == 'SqliteDatabase':
            decay = fn.MAX(1.0, fn.julianday('now') - fn.julianday(Discussion.created_at))
        else:
            decay = fn.GREATEST(1.0, SQL('EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - "t1"."created_at")) / 86400.0'))
        hotness = (Discussion.reply_count * 2 + Discussion.like_count * 3 + Discussion.view_count * 0.1) / decay
        rows = list(query.order_by(Discussion.is_pinned.desc(), hotness.desc(), Discussion.id.desc()).limit(limit).offset(offset))
        liked = _liked_ids(DiscussionLike, DiscussionLike.discussion, rows, user)
        return [_serialize(row, row.id in liked) for row in rows], 200

    def post(self):
        user = _get_current_user()
        if not user:
            return {'error': '请先登录'}, 401
        data = request.get_json(silent=True) or {}
        title = data.get('title', '')
        if not isinstance(title, str) or not title.strip() or len(title) > 200:
            return {'error': '标题不能为空且不能超过 200 字'}, 400
        row = Discussion.create(author=user, title=title.strip(), content=_content(data),
            category=data.get('category', '全部'), tags=data.get('tags', ''))
        return _serialize(row), 201


@api.route('/<int:discussion_id>')
class DiscussionDetailController(Resource):
    def get(self, discussion_id):
        try:
            row = Discussion.select(Discussion, User).join(User).where(Discussion.id == discussion_id).get()
        except Discussion.DoesNotExist:
            return {'error': '讨论不存在'}, 404
        Discussion.update(view_count=Discussion.view_count + 1).where(Discussion.id == row.id).execute()
        row.view_count += 1
        user = _get_current_user()
        data = _serialize(row, row.id in _liked_ids(DiscussionLike, DiscussionLike.discussion, [row], user))
        data['replies'] = _replies(row.id, user)
        return data, 200

    def delete(self, discussion_id):
        user = _get_current_user()
        if not user:
            return {'error': '请先登录'}, 401
        with get_database().atomic():
            try:
                row = _lock(Discussion, discussion_id)
            except Discussion.DoesNotExist:
                return {'error': '讨论不存在'}, 404
            if row.author_id != user.id and user.role != 'manager':
                return {'error': '无权删除'}, 403
            ids = DiscussionReply.select(DiscussionReply.id).where(DiscussionReply.discussion == row)
            DiscussionReplyLike.delete().where(DiscussionReplyLike.reply.in_(ids)).execute()
            DiscussionReply.delete().where(DiscussionReply.discussion == row).execute()
            DiscussionLike.delete().where(DiscussionLike.discussion == row).execute()
            row.delete_instance()
        return {'success': True}, 200


def _set_like(model, likes, foreign_key, row_id):
    user = _get_current_user()
    if not user:
        return {'error': '请先登录'}, 401
    desired = (request.get_json(silent=True) or {}).get('liked')
    if not isinstance(desired, bool):
        return {'error': 'liked 必须为布尔值'}, 400
    with get_database().atomic():
        try:
            # 所有回复写操作遵循 Discussion → Reply 锁顺序，与删除主帖一致。
            if model is DiscussionReply:
                reply = model.get_or_none(model.id == row_id)
                if not reply:
                    return {'error': '内容不存在'}, 404
                _lock(Discussion, reply.discussion_id)
            row = _lock(model, row_id)
        except (model.DoesNotExist, Discussion.DoesNotExist):
            return {'error': '内容不存在'}, 404
        query = likes.select().where((foreign_key == row.id) & (likes.user == user.id))
        existing = query.first()
        if desired and not existing:
            likes.create(**{foreign_key.name: row.id, 'user': user.id})
            model.update(like_count=model.like_count + 1).where(model.id == row.id).execute()
        elif not desired and existing:
            existing.delete_instance()
            model.update(like_count=model.like_count - 1).where((model.id == row.id) & (model.like_count > 0)).execute()
        count = model.get_by_id(row.id).like_count
    return {'liked': desired, 'like_count': count}, 200


@api.route('/<int:discussion_id>/like')
class DiscussionLikeController(Resource):
    def post(self, discussion_id):
        return _set_like(Discussion, DiscussionLike, DiscussionLike.discussion, discussion_id)


@api.route('/<int:discussion_id>/replies')
class DiscussionReplyListController(Resource):
    def get(self, discussion_id):
        if not Discussion.select().where(Discussion.id == discussion_id).exists():
            return {'error': '讨论不存在'}, 404
        return _replies(discussion_id, _get_current_user()), 200

    def post(self, discussion_id):
        user = _get_current_user()
        if not user:
            return {'error': '请先登录'}, 401
        content = _content(request.get_json(silent=True) or {})
        with get_database().atomic():
            try:
                row = _lock(Discussion, discussion_id)
            except Discussion.DoesNotExist:
                return {'error': '讨论不存在'}, 404
            if row.is_closed:
                return {'error': '讨论已关闭'}, 409
            reply = DiscussionReply.create(discussion=row, author=user, content=content)
            Discussion.update(reply_count=Discussion.reply_count + 1).where(Discussion.id == row.id).execute()
        return _serialize(reply), 201


@api.route('/replies/<int:reply_id>/like')
class DiscussionReplyLikeController(Resource):
    def post(self, reply_id):
        return _set_like(DiscussionReply, DiscussionReplyLike, DiscussionReplyLike.reply, reply_id)


@api.route('/replies/<int:reply_id>')
class DiscussionReplyDetailController(Resource):
    def delete(self, reply_id):
        user = _get_current_user()
        if not user:
            return {'error': '请先登录'}, 401
        with get_database().atomic():
            reply = DiscussionReply.get_or_none(DiscussionReply.id == reply_id)
            if not reply:
                return {'error': '回复不存在'}, 404
            _lock(Discussion, reply.discussion_id)
            if reply.author_id != user.id and user.role != 'manager':
                return {'error': '无权删除'}, 403
            DiscussionReplyLike.delete().where(DiscussionReplyLike.reply == reply_id).execute()
            deleted = DiscussionReply.delete().where(DiscussionReply.id == reply_id).execute()
            if deleted:
                Discussion.update(reply_count=Discussion.reply_count - 1).where(
                    (Discussion.id == reply.discussion_id) & (Discussion.reply_count > 0)).execute()
        return {'success': True}, 200
