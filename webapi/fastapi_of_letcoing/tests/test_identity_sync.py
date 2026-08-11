from unittest import IsolatedAsyncioTestCase, TestCase

from peewee import SqliteDatabase

from models.db_models import User, database_proxy
from services.user_service import UserService
from utils.identity_utils import extract_account_status


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
