from datetime import datetime, timezone
from flask import request
from flask_restx import Namespace, Resource, fields
from models.db_models import Discussion, DiscussionReply, DiscussionLike, User
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


def _calc_hotness(d):
    """计算热度分数：回复数*2 + 点赞数*3 + 浏览数*0.1，再按时间衰减"""
    now = datetime.now(timezone.utc)
    created = d.created_at
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    age_hours = max((now - created).total_seconds() / 3600, 0.1)
    score = (d.reply_count or 0) * 2 + (d.like_count or 0) * 3 + (d.view_count or 0) * 0.1
    # 时间衰减：24小时内保持较高权重
    decay = max(1.0, age_hours / 24)
    return score / decay


def _discussion_to_dict(d, current_user=None):
    """转换讨论为字典"""
    data = d.to_dict()
    # 将 ForeignKey 字段 author 重命名为 author_id
    if 'author' in data:
        data['author_id'] = data.pop('author')
    if d.author:
        data['author_name'] = d.author.username or '匿名'
    else:
        data['author_name'] = '匿名'
    # 当前用户是否点赞
    data['is_liked'] = False
    if current_user:
        try:
            data['is_liked'] = DiscussionLike.select().where(
                (DiscussionLike.discussion == d) & (DiscussionLike.user == current_user)
            ).exists()
        except Exception:
            pass
    return data


@api.route('/')
class DiscussionListController(Resource):
    @api.doc('list_discussions')
    @api.param('category', '筛选分类')
    def get(self):
        """获取讨论列表（按热度+时间排序）"""
        category = request.args.get('category', '').strip()
        current_user = _get_current_user()

        try:
            query = Discussion.select()
            if category and category != '全部':
                query = query.where(Discussion.category == category)

            discussions = list(query)
            # 置顶帖排最前，其余按热度降序
            pinned = [d for d in discussions if d.is_pinned]
            normal = [d for d in discussions if not d.is_pinned]
            normal.sort(key=lambda d: _calc_hotness(d), reverse=True)
            sorted_discussions = pinned + normal

            return [_discussion_to_dict(d, current_user) for d in sorted_discussions], 200
        except Exception as e:
            return {'error': f'获取讨论列表失败: {str(e)}'}, 500

    @api.expect(discussion_input)
    def post(self):
        """发布讨论"""
        user = _get_current_user()
        if not user:
            return {'error': '请先登录'}, 401

        data = request.get_json(silent=True) or {}
        title = data.get('title', '').strip()
        content = data.get('content', '').strip()
        if not title or not content:
            return {'error': '标题和内容不能为空'}, 400

        discussion = Discussion.create(
            title=title,
            content=content,
            author=user.id,
            category=data.get('category', '全部'),
            tags=data.get('tags', ''),
        )
        return _discussion_to_dict(discussion, user), 201


@api.route('/<int:discussion_id>')
class DiscussionDetailController(Resource):
    def get(self, discussion_id):
        """获取讨论详情（同时增加浏览量）"""
        try:
            d = Discussion.get_by_id(discussion_id)
            # 增加浏览量
            d.view_count = (d.view_count or 0) + 1
            d.save()
            current_user = _get_current_user()
            data = _discussion_to_dict(d, current_user)
            # 获取回复（按时间正序）
            replies = DiscussionReply.select().where(
                DiscussionReply.discussion == d
            ).order_by(DiscussionReply.created_at)
            data['replies'] = []
            for r in replies:
                rd = r.to_dict()
                if 'author' in rd:
                    rd['author_id'] = rd.pop('author')
                if r.author:
                    rd['author_name'] = r.author.username or '匿名'
                else:
                    rd['author_name'] = '匿名'
                # 回复的点赞状态
                rd['is_liked'] = False
                if current_user:
                    from models.db_models import DiscussionReplyLike
                    try:
                        rd['is_liked'] = DiscussionReplyLike.select().where(
                            (DiscussionReplyLike.reply == r) & (DiscussionReplyLike.user == current_user)
                        ).exists()
                    except Exception:
                        pass
                data['replies'].append(rd)
            return data, 200
        except Discussion.DoesNotExist:
            return {'error': '讨论不存在'}, 404

    def delete(self, discussion_id):
        """删除讨论（作者或管理员）"""
        user = _get_current_user()
        if not user:
            return {'error': '请先登录'}, 401

        try:
            d = Discussion.get_by_id(discussion_id)
            if d.author_id != user.id and user.role != 'manager':
                return {'error': '无权删除'}, 403
            d.delete_instance()
            return {'success': True}, 200
        except Discussion.DoesNotExist:
            return {'error': '讨论不存在'}, 404


@api.route('/<int:discussion_id>/like')
class DiscussionLikeController(Resource):
    def post(self, discussion_id):
        """点赞/取消点赞讨论"""
        user = _get_current_user()
        if not user:
            return {'error': '请先登录'}, 401
        try:
            d = Discussion.get_by_id(discussion_id)
        except Discussion.DoesNotExist:
            return {'error': '讨论不存在'}, 404

        existing = DiscussionLike.select().where(
            (DiscussionLike.discussion == d) & (DiscussionLike.user == user)
        ).first()
        if existing:
            existing.delete_instance()
            d.like_count = max(0, (d.like_count or 0) - 1)
            d.save()
            return {'liked': False, 'like_count': d.like_count}, 200
        else:
            DiscussionLike.create(discussion=d, user=user)
            d.like_count = (d.like_count or 0) + 1
            d.save()
            return {'liked': True, 'like_count': d.like_count}, 200


@api.route('/<int:discussion_id>/replies')
class DiscussionReplyListController(Resource):
    @api.expect(reply_input)
    def post(self, discussion_id):
        """发表回复"""
        user = _get_current_user()
        if not user:
            return {'error': '请先登录'}, 401

        try:
            d = Discussion.get_by_id(discussion_id)
        except Discussion.DoesNotExist:
            return {'error': '讨论不存在'}, 404

        if d.is_closed:
            return {'error': '讨论已关闭'}, 400

        data = request.get_json(silent=True) or {}
        content = data.get('content', '').strip()
        if not content:
            return {'error': '回复内容不能为空'}, 400

        reply = DiscussionReply.create(
            discussion=d,
            author=user.id,
            content=content,
        )
        d.reply_count += 1
        d.save()

        rd = reply.to_dict()
        if 'author' in rd:
            rd['author_id'] = rd.pop('author')
        rd['author_name'] = user.username or '匿名'
        rd['is_liked'] = False
        return rd, 201


@api.route('/replies/<int:reply_id>/like')
class DiscussionReplyLikeController(Resource):
    def post(self, reply_id):
        """点赞/取消点赞回复"""
        user = _get_current_user()
        if not user:
            return {'error': '请先登录'}, 401
        try:
            r = DiscussionReply.get_by_id(reply_id)
        except DiscussionReply.DoesNotExist:
            return {'error': '回复不存在'}, 404

        from models.db_models import DiscussionReplyLike
        existing = DiscussionReplyLike.select().where(
            (DiscussionReplyLike.reply == r) & (DiscussionReplyLike.user == user)
        ).first()
        if existing:
            existing.delete_instance()
            r.like_count = max(0, (r.like_count or 0) - 1)
            r.save()
            return {'liked': False, 'like_count': r.like_count}, 200
        else:
            DiscussionReplyLike.create(reply=r, user=user)
            r.like_count = (r.like_count or 0) + 1
            r.save()
            return {'liked': True, 'like_count': r.like_count}, 200


@api.route('/replies/<int:reply_id>')
class DiscussionReplyDetailController(Resource):
    def delete(self, reply_id):
        """删除回复（作者或管理员）"""
        user = _get_current_user()
        if not user:
            return {'error': '请先登录'}, 401

        try:
            r = DiscussionReply.get_by_id(reply_id)
        except DiscussionReply.DoesNotExist:
            return {'error': '回复不存在'}, 404

        if r.author_id != user.id and user.role != 'manager':
            return {'error': '无权删除'}, 403

        discussion = r.discussion
        r.delete_instance()
        if discussion:
            discussion.reply_count = max(0, (discussion.reply_count or 0) - 1)
            discussion.save()
        return {'success': True}, 200
