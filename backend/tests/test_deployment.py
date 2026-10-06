from pathlib import Path
from types import SimpleNamespace
import tomllib
import pytest
from app.website import events
from app.website.config import PROJECT


def test_linux_requirements_match_existing_lock():
    lock=tomllib.loads((PROJECT/'backend/uv.lock').read_text())
    packages={p['name']:p for p in lock['package']}
    for filename in ['requirements-linux.txt','requirements-linux-test.txt']:
        for line in (PROJECT/'backend'/filename).read_text().splitlines():
            if not line or line.startswith(('#','-r')):continue
            name,version=line.split('==')
            assert packages[name]['version']==version
            assert any('py3-none-any' in w['url'] or ('manylinux' in w['url'] and 'x86_64' in w['url'] and
                       ('cp312' in w['url'] or 'abi3' in w['url'])) for w in packages[name]['wheels'])


@pytest.mark.parametrize('key',['','test-key-not-a-secret'])
def test_linux_youtube_key_without_dpapi(monkeypatch,key):
    env={'YOUTUBE_API_KEY':key}
    monkeypatch.setattr(events,'os',SimpleNamespace(name='posix',getenv=env.get,environ=env))
    assert events.YouTubeProvider.local_key()==key


def test_deployment_safety_contract():
    unit=(PROJECT/'deploy/loderunner.service').read_text()
    assert '--host 127.0.0.1' in unit and '--workers 1' in unit
    assert '--reload' not in unit and 'User=loderunner' in unit
    assert 'ReadWritePaths=/var/lib/loderunner' in unit
    assert 'Restart=on-failure' in unit
    nginx=(PROJECT/'deploy/nginx-loderunner.conf').read_text()
    assert 'proxy_pass http://127.0.0.1:8011;' in nginx
    assert 'proxy_set_header X-Forwarded-For $remote_addr;' in nginx
    assert 'alias ' not in '\n'.join(l for l in nginx.splitlines() if not l.strip().startswith('#'))
    for p in (PROJECT/'deploy').iterdir():
        assert b'\r\n' not in p.read_bytes(),p
    assert 'YOUTUBE_API_KEY=\n' in (PROJECT/'deploy/loderunner.env.example').read_text()
