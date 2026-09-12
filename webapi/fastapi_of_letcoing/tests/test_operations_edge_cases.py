"""运维输入损坏与资源释放故障不能破坏比赛判题和监控。"""
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from models import db_models as m
from test_acm_upgrade import contest_fixture


@pytest.mark.parametrize('payload', [[], None, 'damaged'])
def test_bad_backup_manifest_preserves_metrics_endpoint(app, db, cache, tmp_path, monkeypatch, payload):
    from services.observability import register_metrics
    path = tmp_path/'manifest.json'
    path.write_text(json.dumps(payload))
    monkeypatch.setenv('BACKUP_MANIFEST_FILE', str(path))
    app.config['METRICS_TOKEN'] = 'isolated-test'
    register_metrics(app)
    with patch('core.di_container.inject', return_value=cache):
        response = app.test_client().get('/metrics', headers={'Authorization': 'Bearer isolated-test'})
    assert response.status_code == 200
    assert 'letcoding_backup_status_up 0' in response.text
    assert 'letcoding_dependency_up{dependency="postgres"} 1' in response.text
    assert 'letcoding_dependency_up{dependency="redis"} 1' in response.text


@pytest.mark.parametrize('damage', ['files', 'command'])
def test_bad_compile_manifest_recompiles_without_directory_leak(tmp_path, monkeypatch, damage):
    from services.compile_cache import prepare_cached
    monkeypatch.setenv('APP_ENV', 'test')
    monkeypatch.setenv('JUDGE_BACKEND', 'local')
    monkeypatch.setenv('ALLOW_UNSAFE_LOCAL_JUDGE', '1')
    monkeypatch.setenv('JUDGE_COMPILE_CACHE', str(tmp_path/'cache'))
    monkeypatch.setenv('JUDGE_WORK_ROOT', str(tmp_path/'jobs'))
    source = '#include <iostream>\nint main(){std::cout << 42;}'
    first, error, _ = prepare_cached(source, 'cpp')
    assert error is None
    first.close()
    manifest = next((tmp_path/'cache').glob('*/manifest.json'))
    data = json.loads(manifest.read_text())
    data[damage] = ['invalid'] if damage == 'files' else [123]
    manifest.write_text(json.dumps(data))
    recovered, error, _ = prepare_cached(source, 'cpp')
    try:
        assert error is None and not recovered.cache_hit
        assert recovered.run('', 1, 128)[0].strip() == '42'
    finally:
        if recovered:
            recovered.close()
    assert not list((tmp_path/'jobs').iterdir())


def test_package_checker_cleanup_failure_releases_other_programs(db, tmp_path, monkeypatch):
    from services.contest_packages import OutputChecker, stage_package, validate_staged_package
    monkeypatch.setenv('APP_ENV', 'test')
    monkeypatch.setenv('JUDGE_BACKEND', 'local')
    monkeypatch.setenv('ALLOW_UNSAFE_LOCAL_JUDGE', '1')
    monkeypatch.setenv('JUDGE_WORK_ROOT', str(tmp_path/'jobs'))
    user, _, problem = contest_fixture()
    user.role = 'manager'
    user.save()
    package = stage_package(problem.id, user, {
        'reference': 'print(42)', 'language': 'python',
        'cases': [{'input_data': '', 'expected_output': '42'}],
        'known_wrong': [{'code': 'print(1)', 'language': 'python'}],
    }, 'cleanup regression')
    with patch.object(OutputChecker, 'close', side_effect=OSError('disk fault')):
        validate_staged_package(package.digest)
    assert m.ContestPackage.get_by_id(package.digest).validation_state == 'INVALID'
    assert not list((tmp_path/'jobs').iterdir())


@pytest.mark.parametrize('image,values', [('sandbox:latest', [100]*5), ('sha256:'+'a'*64, [True]*5)])
def test_calibration_rejects_unreliable_evidence(image, values):
    from deploy.calibrate_judge import compare_calibrations
    reports = [{'image': image, 'cpu_ms': values}, {'image': image, 'cpu_ms': values}]
    with pytest.raises(ValueError):
        compare_calibrations(reports)
