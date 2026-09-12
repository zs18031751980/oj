"""基于 PostgreSQL 会话的 JWT；缓存故障不会绕过撤销和账号状态。"""
import hashlib
import base64
import json
from cryptography.fernet import Fernet, InvalidToken
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
from peewee import OperationalError, InterfaceError

from core.db_robust import DatabaseUnavailableError
from core.di_container import Injectable
from interfaces.service_interfaces import IConfigService, ILoggerService, IRedisService, IJWTService
from models.auth_models import JWTToken, UserInfo
from models.db_models import AuthSession, User, get_database


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def token_hash(value):
    return hashlib.sha256(value.encode()).hexdigest()


class JWTService(Injectable, IJWTService):
    def __init__(self, config_service: IConfigService, logger_service: ILoggerService,
                 redis_service: IRedisService):
        self._config_service = config_service
        self._logger_service = logger_service
        self._redis_service = redis_service
        self._secret_key = config_service.get_config('JWT_SECRET_KEY', '')
        if len(self._secret_key.encode()) < 32:
            raise ValueError('JWT_SECRET_KEY 必须至少为 32 字节的随机密钥')
        self._algorithm = 'HS256'
        self._access_token_expire = int(config_service.get_config('JWT_ACCESS_TOKEN_EXPIRE', 900))
        self._refresh_token_expire = int(config_service.get_config('JWT_REFRESH_TOKEN_EXPIRE', 604800))
        self._issuer = config_service.get_config('JWT_ISSUER', 'letcoding')
        self._audience = config_service.get_config('JWT_AUDIENCE', 'letcoding-api')

    def _pair(self, user_id, sid, expires_at):
        now = datetime.now(timezone.utc)
        common = {'user_id': user_id, 'sid': sid, 'iss': self._issuer,
                  'aud': self._audience, 'iat': now}
        access = jwt.encode({**common, 'jti': uuid4().hex, 'type': 'access',
                             'exp': min(now + timedelta(seconds=self._access_token_expire),
                                        expires_at.replace(tzinfo=timezone.utc))},
                            self._secret_key, algorithm=self._algorithm)
        refresh = jwt.encode({**common, 'jti': uuid4().hex, 'type': 'refresh',
                              'exp': expires_at.replace(tzinfo=timezone.utc)},
                             self._secret_key, algorithm=self._algorithm)
        return JWTToken(access, refresh, self._access_token_expire)

    def _decode(self, token, kind):
        payload = jwt.decode(token, self._secret_key, algorithms=[self._algorithm],
                             issuer=self._issuer, audience=self._audience,
                             options={'require': ['exp', 'iat', 'sid', 'jti', 'user_id', 'type']})
        if payload['type'] != kind:
            raise jwt.InvalidTokenError('invalid token type')
        return payload

    @staticmethod
    def _session(payload):
        return (AuthSession.select(AuthSession, User).join(User).where(
            (AuthSession.id == payload['sid']) & (AuthSession.user == payload['user_id'])
            & (AuthSession.revoked == False) & (AuthSession.expires_at > utcnow())
            & (User.is_active == True)).first())

    def generate_tokens(self, user_info):
        user = User.get_by_id(int(user_info['id']))
        if not user.is_active:
            raise PermissionError('账号已停用')
        sid, expires = uuid4().hex, utcnow() + timedelta(seconds=self._refresh_token_expire)
        pair = self._pair(user.id, sid, expires)
        AuthSession.create(id=sid, user=user.id, refresh_hash=token_hash(pair.refresh_token), expires_at=expires)
        return pair

    def verify_access_token(self, token):
        try:
            session = self._session(self._decode(token, 'access'))
            if session is None:
                return None
            data = session.user.to_dict()
            # 兼容现有 UserInfo DTO；不向客户端暴露会话或内部字段。
            return {key: data[key] for key in UserInfo.__dataclass_fields__ if key in data}
        except (jwt.InvalidTokenError, ValueError, TypeError, KeyError):
            return None
        except (OperationalError, InterfaceError) as exc:
            raise DatabaseUnavailableError() from exc

    def refresh_access_token(self, refresh_token):
        try:
            payload = self._decode(refresh_token, 'refresh')
            session = self._session(payload)
            if session is None:
                return None
            pair = self._pair(session.user_id, session.id, session.expires_at)
            changed = AuthSession.update(refresh_hash=token_hash(pair.refresh_token)).where(
                (AuthSession.id == session.id) & (AuthSession.revoked == False)
                & (AuthSession.refresh_hash == token_hash(refresh_token))
                & (AuthSession.expires_at > utcnow())).execute()
            if changed != 1:
                # 已消费令牌重放，撤销整个会话（并发刷新由客户端合并）。
                AuthSession.update(revoked=True).where(AuthSession.id == session.id).execute()
                return None
            return pair
        except (jwt.InvalidTokenError, ValueError, TypeError, KeyError):
            return None
        except (OperationalError, InterfaceError) as exc:
            raise DatabaseUnavailableError() from exc

    def refresh_browser_session(self, token, request_id):
        """同一请求允许 30 秒内恢复丢失响应；不同请求重放仍撤销会话。

        恢复材料经独立派生密钥加密，数据库不会保存明文刷新凭证。
        PostgreSQL 行锁使不同进程的刷新和恢复具有同一顺序。
        """
        if not request_id or len(request_id) > 128:
            return None
        try:
            payload = self._decode(token, 'refresh')
            cipher = Fernet(base64.urlsafe_b64encode(hashlib.sha256(
                ('browser-refresh-recovery:' + self._secret_key).encode()).digest()))
            with get_database().atomic():
                query = AuthSession.select().where(AuthSession.id == payload['sid'])
                if get_database().__class__.__name__ != 'SqliteDatabase':
                    query = query.for_update()
                session = query.first()
                if (not session or session.revoked or session.user_id != payload['user_id']
                        or session.expires_at <= utcnow() or not session.user.is_active):
                    return None
                digest = token_hash(token)
                if (session.refresh_request_id == request_id and session.refresh_retry_until
                        and session.refresh_retry_until > utcnow()
                        and digest in (session.refresh_hash, session.previous_refresh_hash)):
                    saved = json.loads(cipher.decrypt(session.refresh_retry_ciphertext.encode(), ttl=30))
                    return JWTToken(saved['access_token'], saved['refresh_token'], saved['expires_in'])
                if digest != session.refresh_hash:
                    session.revoked = True
                    session.save(only=[AuthSession.revoked])
                    return None
                pair = self._pair(session.user_id, session.id, session.expires_at)
                session.previous_refresh_hash = digest
                session.refresh_hash = token_hash(pair.refresh_token)
                session.refresh_request_id = request_id
                session.refresh_retry_until = utcnow() + timedelta(seconds=30)
                session.refresh_retry_ciphertext = cipher.encrypt(json.dumps(pair.to_dict()).encode()).decode()
                session.save(only=[AuthSession.previous_refresh_hash, AuthSession.refresh_hash,
                    AuthSession.refresh_request_id, AuthSession.refresh_retry_until, AuthSession.refresh_retry_ciphertext])
                return pair
        except (jwt.InvalidTokenError, InvalidToken, ValueError, TypeError, KeyError):
            return None

    def revoke_refresh_cookie(self, token):
        try:
            payload = self._decode(token, 'refresh')
            AuthSession.update(revoked=True).where(
                (AuthSession.id == payload['sid']) & (AuthSession.user == payload['user_id'])).execute()
        except jwt.InvalidTokenError:
            pass

    def revoke_token(self, token):
        try:
            payload = self._decode(token, 'access')
            return bool(AuthSession.update(revoked=True).where(
                (AuthSession.id == payload['sid']) & (AuthSession.user == payload['user_id'])).execute())
        except jwt.InvalidTokenError:
            return False
        except (OperationalError, InterfaceError) as exc:
            raise DatabaseUnavailableError() from exc

    def refresh_cached_user(self, user_id, user_info):
        # 仅为旧调用方保留资料缓存，认证始终读取持久化状态。
        self._redis_service.delete(f'user:{user_id}')
