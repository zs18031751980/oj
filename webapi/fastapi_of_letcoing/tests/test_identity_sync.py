from unittest import IsolatedAsyncioTestCase, TestCase
from unittest.mock import patch

import jwt
from peewee import SqliteDatabase

from controllers.auth_controller import (
    _issue_tokens_for_provider_user,
    _user_info_from_provider_token,
)
from interfaces.service_interfaces import IJWTService, ILoggerService, IUserService
from models.auth_models import UserInfo
from models.db_models import User, database_proxy
from services.jwt_service import JWTService
from services.user_service import UserService
from utils.identity_utils import extract_account_status


class FakeConfigService:
    values = {
        'JWT_SECRET_KEY': 'test-secret',
        'JWT_ALGORITHM': 'HS256',
        'JWT_ACCESS_TOKEN_EXPIRE': 3600,
        'JWT_REFRESH_TOKEN_EXPIRE': 7200,
    }

    def get_config(self, key, default=None):
        return self.values.get(key, default)


class FakeLoggerService:
    def info(self, *args):
        return None

    def warning(self, *args):
        return None

    def error(self, *args):
        return None


class FakeRedisService:
    def __init__(self):
        self.values = {}
        self.raw_values = {}

    def set(self, key, value, ttl=None):
        self.values[key] = value
        return True

    def get(self, key, default=None):
        return self.values.get(key, default)

    def set_raw(self, key, value, ttl=None):
        self.raw_values[key] = value
        return True

    def get_raw(self, key, default=None):
        return self.raw_values.get(key, default)

    def exists(self, key):
        return key in self.raw_values

    def is_connected(self):
        return False


class RecordingJWTService:
    def __init__(self):
        self.generated = False

    def generate_tokens(self, user_info):
        self.generated = True
        raise AssertionError('inactive or unsynchronized users must not receive tokens')


class InactiveUserService:
    async def find_or_create_user(self, provider, provider_id, user_info):
        return {
            **user_info,
            'id': 7,
            'provider': provider,
            'provider_id': provider_id,
            'is_active': False,
        }


class FailingUserService:
    async def find_or_create_user(self, provider, provider_id, user_info):
        raise RuntimeError('database unavailable')


class ExtractAccountStatusTests(TestCase):
    def test_reads_boolean_status_claims(self):
        self.assertIs(extract_account_status({'enabled': True}), True)
        self.assertIs(extract_account_status({'is_active': False}), False)

    def test_reads_known_status_strings(self):
        self.assertIs(extract_account_status({'status': 'active'}), True)
        self.assertIs(extract_account_status({'account_status': 'disabled'}), False)

    def test_missing_or_unknown_status_preserves_local_value(self):
        self.assertIsNone(extract_account_status({}))
        self.assertIsNone(extract_account_status({'status': 'pending-review'}))


class ProviderIdentityTests(TestCase):
    def test_provider_claims_include_normalized_account_status(self):
        token = jwt.encode(
            {'sub': '42', 'role': 'minister', 'enabled': False},
            'provider-secret',
        )

        with patch('controllers.auth_controller.inject', return_value=FakeLoggerService()):
            result = _user_info_from_provider_token('iOSClub', 'leader', token)

        self.assertEqual(result['role'], 'manager')
        self.assertIs(result['is_active'], False)

    def test_user_info_response_includes_account_state_and_last_login(self):
        user_info = UserInfo(
            id='42',
            username='leader',
            email='leader@example.com',
            is_active=True,
            last_login='2026-08-11T12:00:00+08:00',
        )

        result = user_info.to_dict()

        self.assertIs(result['is_active'], True)
        self.assertEqual(result['last_login'], '2026-08-11T12:00:00+08:00')

    def test_inactive_provider_user_does_not_receive_local_tokens(self):
        jwt_service = RecordingJWTService()

        def resolve(service_type):
            if service_type is IJWTService:
                return jwt_service
            if service_type is IUserService:
                return InactiveUserService()
            if service_type is ILoggerService:
                return FakeLoggerService()
            raise AssertionError(f'unexpected service: {service_type}')

        with patch('controllers.auth_controller.inject', side_effect=resolve):
            with self.assertRaises(PermissionError):
                _issue_tokens_for_provider_user(
                    'iOSClub',
                    {'id': '42', 'username': 'leader', 'role': 'manager'},
                )

        self.assertFalse(jwt_service.generated)

    def test_sync_failure_does_not_fall_back_to_unsynchronized_tokens(self):
        jwt_service = RecordingJWTService()

        def resolve(service_type):
            if service_type is IJWTService:
                return jwt_service
            if service_type is IUserService:
                return FailingUserService()
            if service_type is ILoggerService:
                return FakeLoggerService()
            raise AssertionError(f'unexpected service: {service_type}')

        with patch('controllers.auth_controller.inject', side_effect=resolve):
            with self.assertRaises(RuntimeError):
                _issue_tokens_for_provider_user(
                    'iOSClub',
                    {'id': '42', 'username': 'leader', 'role': 'manager'},
                )

        self.assertFalse(jwt_service.generated)

    def test_missing_provider_id_does_not_receive_local_tokens(self):
        jwt_service = RecordingJWTService()

        with patch('controllers.auth_controller.inject', return_value=jwt_service):
            with self.assertRaises(ValueError):
                _issue_tokens_for_provider_user(
                    'iOSClub',
                    {'username': 'leader', 'role': 'manager'},
                )

        self.assertFalse(jwt_service.generated)


class JWTUserStateTests(TestCase):
    def test_access_token_fallback_preserves_account_state_and_last_login(self):
        redis_service = FakeRedisService()
        service = JWTService(FakeConfigService(), FakeLoggerService(), redis_service)
        tokens = service.generate_tokens({
            'id': '42',
            'username': 'leader',
            'email': 'leader@example.com',
            'provider': 'iOSClub',
            'role': 'manager',
            'is_active': True,
            'last_login': '2026-08-11T12:00:00+08:00',
        })
        redis_service.values.clear()

        result = service.verify_access_token(tokens.access_token)

        self.assertIsNotNone(result)
        self.assertIs(result['is_active'], True)
        self.assertEqual(result['last_login'], '2026-08-11T12:00:00+08:00')


class UserSyncTests(IsolatedAsyncioTestCase):
    def setUp(self):
        self.database = SqliteDatabase(':memory:')
        database_proxy.initialize(self.database)
        self.database.create_tables([User])
        self.user_service = object.__new__(UserService)

    def tearDown(self):
        self.database.drop_tables([User])
        self.database.close()

    async def test_existing_user_keeps_id_and_manual_role_while_syncing_status(self):
        original = User.create(
            username='leader',
            provider='iOSClub',
            provider_id='42',
            role='manager',
            is_active=True,
        )

        result = await self.user_service.find_or_create_user(
            'iOSClub',
            '42',
            {
                'username': 'leader-new',
                'role': 'member',
                'is_active': False,
            },
        )

        refreshed = User.get_by_id(original.id)
        self.assertEqual(result['id'], original.id)
        self.assertEqual(refreshed.id, original.id)
        self.assertEqual(refreshed.username, 'leader-new')
        self.assertEqual(refreshed.role, 'manager')
        self.assertFalse(refreshed.is_active)
        self.assertIsNotNone(refreshed.last_login)

    async def test_missing_status_preserves_local_value(self):
        original = User.create(
            username='disabled',
            provider='iOSClub',
            provider_id='43',
            role='member',
            is_active=False,
        )

        await self.user_service.find_or_create_user(
            'iOSClub',
            '43',
            {'username': 'disabled', 'role': 'member'},
        )

        self.assertFalse(User.get_by_id(original.id).is_active)

    async def test_higher_provider_role_promotes_existing_user(self):
        original = User.create(
            username='member',
            provider='iOSClub',
            provider_id='44',
            role='member',
        )

        await self.user_service.find_or_create_user(
            'iOSClub',
            '44',
            {'username': 'member', 'role': 'manager'},
        )

        self.assertEqual(User.get_by_id(original.id).role, 'manager')
