"""列表返回保持兼容，同时约束查询数量及分页可见性。"""
from datetime import datetime, timedelta

from flask_restx import Api
from playhouse.test_utils import count_queries

from models import db_models as m


def test_contest_list_batches_counts_and_pages_without_changing_legacy_shape(app, db):
    from controllers.contest_controller import api
    rest = Api(app); rest.add_namespace(api, path='/contests')
    user = m.User.create(username='counter')
    for i in range(12):
        contest = m.Contest.create(title=f'contest-{i}', created_by=user, is_public=True, lifecycle_state='RUNNING',
            start_time=datetime.now()-timedelta(days=1), end_time=datetime.now()+timedelta(days=1))
        m.ContestParticipant.create(contest=contest, user=user)
    m.Contest.create(title='private', is_public=False, lifecycle_state='RUNNING')
    client = app.test_client()
    with count_queries() as counter:
        response = client.get('/contests/')
    assert response.status_code == 200 and len(response.json) == 12
    assert all(row['participants_count'] == 1 for row in response.json)
    assert counter.count <= 3, f'list executed {counter.count} queries'
    page = client.get('/contests/?page=2&page_size=5&status=ongoing')
    assert page.status_code == 200 and len(page.json) == 5
    assert page.headers['X-Total-Count'] == '12'
    assert not ({r['id'] for r in page.json} & {r['id'] for r in client.get('/contests/?page=1&page_size=5').json})
    assert client.get('/contests/?page=0').status_code == 400
    assert client.get('/contests/?page_size=100000').status_code == 400


def test_problem_pagination_preserves_total_and_filters_public_ended_only(app, db):
    from controllers.problem_controller import api
    rest = Api(app); rest.add_namespace(api, path='/problems')
    for state, public in [('RUNNING', True), ('DRAFT', True), ('RUNNING', False)]:
        contest = m.Contest.create(title='fixture', lifecycle_state=state, is_public=public,
            end_time=datetime.now()-timedelta(days=1))
        for i in range(3):
            m.ContestProblem.create(contest=contest, title=f'needle-{state}-{i}', description='fixture', correct_answer='print(42)', problem_index=str(i))
    client = app.test_client()
    response = client.get('/problems?q=needle&page=1&page_size=2')
    assert response.status_code == 200
    assert response.json['total'] == 3 and len(response.json['data']) == 2
    assert all('RUNNING' in row['title'] for row in response.json['data'])
    second = client.get('/problems?q=needle&page=2&page_size=2').json
    assert second['total'] == 3 and len(second['data']) == 1
    assert client.get('/problems?page=bad').status_code == 400


def test_catalog_cache_revalidates_visibility_before_returning_not_modified(app, db):
    from controllers.problem_controller import api
    rest = Api(app); rest.add_namespace(api, path='/problems')
    contest = m.Contest.create(title='temporary-public', lifecycle_state='FINALIZED', is_public=True)
    m.ContestProblem.create(contest=contest, title='published-needle', problem_index='A',
                           description='fixture', correct_answer='print(42)')
    client = app.test_client()
    response = client.get('/problems?q=published-needle')
    assert response.status_code == 200 and response.json['total'] == 1
    etag = response.headers['ETag']
    assert client.get('/problems?q=published-needle', headers={'If-None-Match': etag}).status_code == 304
    contest.is_public = False; contest.save()
    hidden = client.get('/problems?q=published-needle', headers={'If-None-Match': etag})
    assert hidden.status_code == 200 and hidden.json['total'] == 0
    assert 'no-cache' in hidden.headers['Cache-Control']


from test_postgres import postgres


def test_paginated_catalog_queries_execute_on_postgres(app, postgres):
    from controllers.contest_controller import api as contests
    from controllers.problem_controller import api as problems
    m.run_schema_migrations()
    rest = Api(app)
    rest.add_namespace(contests, path='/contests')
    rest.add_namespace(problems, path='/problems')
    user = m.User.create(username='postgres-catalog')
    for index in range(12):
        contest = m.Contest.create(title=f'Published {index}', lifecycle_state='FINALIZED', is_public=True)
        m.ContestParticipant.create(contest=contest, user=user)
        m.ContestProblem.create(contest=contest, title=f'pg-needle-{index}', problem_index='A',
                               description='fixture', correct_answer='print(42)')
    client = app.test_client()
    with count_queries() as counter:
        response = client.get('/contests/')
    assert response.status_code == 200 and len(response.json) == 12
    assert all(row['participants_count'] == 1 for row in response.json)
    assert counter.count <= 3
    print(f'PostgreSQL contest catalog: rows=12 SQL={counter.count}')
    page = client.get('/contests/?page=2&page_size=5&status=past')
    assert page.status_code == 200 and len(page.json) == 5
    assert page.headers['X-Total-Count'] == '12'
    summary = client.get('/problems?q=pg-needle&page=2&page_size=5')
    assert summary.status_code == 200
    assert summary.json['total'] == 12 and len(summary.json['data']) == 5
