from unittest import TestCase
from unittest.mock import patch

from flask import Flask
from flask_restx import Api
from peewee import SqliteDatabase

from controllers.announcement_controller import api as announcement_api
from interfaces.service_interfaces import IJWTService
from models.db_models import Announcement, User, database_proxy


class FakeJWTService:
    def verify_access_token(self, token):
        return {'id': int(token)} if token.isdigit() else None

    def refresh_cached_user(self, user_id, user_info):
        return None


class AnnouncementControllerTests(TestCase):
    @classmethod
    def setUpClass(cls):
        app = Flask(__name__)
        app.config['TESTING'] = True
        Api(app).add_namespace(announcement_api, path='/announcement')
        cls.client = app.test_client()

    def setUp(self):
        self.database = SqliteDatabase(':memory:')
        database_proxy.initialize(self.database)
        self.database.create_tables([User, Announcement])
        self.jwt_service = FakeJWTService()
        self.inject_patch = patch(
            'controllers.announcement_controller.inject',
            side_effect=lambda service_type: self.jwt_service
            if service_type is IJWTService
            else None,
        )
        self.inject_patch.start()

        self.member = User.create(username='member', role='member')
        self.manager = User.create(username='manager', role='manager')
        self.published = Announcement.create(
            title='Published',
            content='# Public',
            is_published=True,
        )
        self.draft = Announcement.create(
            title='Draft',
            content='# Private',
            is_published=False,
        )

    def tearDown(self):
        self.inject_patch.stop()
        self.database.drop_tables([Announcement, User])
        self.database.close()

    @staticmethod
    def auth_headers(user):
        return {'Authorization': f'Bearer {user.id}'}

    def test_public_list_and_detail_hide_drafts(self):
        response = self.client.get('/announcement/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [item['id'] for item in response.get_json()],
            [self.published.id],
        )
        self.assertEqual(
            self.client.get(f'/announcement/{self.draft.id}').status_code,
            404,
        )

    def test_only_manager_can_include_unpublished_announcements(self):
        member_response = self.client.get(
            '/announcement/?include_unpublished=true',
            headers=self.auth_headers(self.member),
        )
        manager_response = self.client.get(
            '/announcement/?include_unpublished=true',
            headers=self.auth_headers(self.manager),
        )

        self.assertEqual(member_response.status_code, 403)
        self.assertEqual(manager_response.status_code, 200)
        self.assertEqual(len(manager_response.get_json()), 2)

    def test_member_cannot_write_announcements(self):
        headers = self.auth_headers(self.member)

        self.assertEqual(
            self.client.post(
                '/announcement/',
                json={'title': 'New', 'content': '# Body'},
                headers=headers,
            ).status_code,
            403,
        )
        self.assertEqual(
            self.client.put(
                f'/announcement/{self.published.id}',
                json={'title': 'Changed'},
                headers=headers,
            ).status_code,
            403,
        )
        self.assertEqual(
            self.client.delete(
                f'/announcement/{self.published.id}',
                headers=headers,
            ).status_code,
            403,
        )

    def test_manager_crud_preserves_id_and_validates_content(self):
        headers = self.auth_headers(self.manager)
        create_response = self.client.post(
            '/announcement/',
            json={'title': 'New', 'content': '# Body'},
            headers=headers,
        )
        created = create_response.get_json()

        self.assertEqual(create_response.status_code, 201)
        update_response = self.client.put(
            f'/announcement/{created["id"]}',
            json={'title': 'Updated', 'content': '# Updated'},
            headers=headers,
        )
        self.assertEqual(update_response.status_code, 200)
        self.assertEqual(update_response.get_json()['id'], created['id'])
        self.assertEqual(Announcement.get_by_id(created['id']).title, 'Updated')

        invalid_response = self.client.put(
            f'/announcement/{created["id"]}',
            json={'content': '   '},
            headers=headers,
        )
        self.assertEqual(invalid_response.status_code, 400)

        delete_response = self.client.delete(
            f'/announcement/{created["id"]}',
            headers=headers,
        )
        self.assertEqual(delete_response.status_code, 200)
        self.assertEqual(
            self.client.get(f'/announcement/{created["id"]}').status_code,
            404,
        )
