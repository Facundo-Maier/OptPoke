from app.demo import seed_demo, main
from app.db import connect
from scripts.check_public import violations


def test_demo_examples(monkeypatch, tmp_path):
    monkeypatch.setenv('OPTPOKE_DATA_DIR', str(tmp_path))
    seed_demo()
    with connect() as db:
        assert db.execute('SELECT sum(in_home) FROM goals').fetchone()[0] == 4
        assert db.execute('SELECT source FROM hunts').fetchone()[0] == 'demo'
        assert db.execute('SELECT count(*) FROM bank_tasks').fetchone()[0] == 1


def test_demo_does_not_open_personal_database(monkeypatch, tmp_path):
    personal = tmp_path / 'optpoke.db'
    personal.write_bytes(b'personal sentinel')
    monkeypatch.setenv('OPTPOKE_DATA_DIR', str(tmp_path))
    def run(*args, **kwargs):
        from app.db import database_path
        assert database_path().parent != tmp_path
        with connect() as db:
            assert db.execute('SELECT count(*) FROM hunts').fetchone()[0] == 1
    monkeypatch.setattr('uvicorn.run', run)
    main()
    assert personal.read_bytes() == b'personal sentinel'


def test_demo_runtime_flag(client, monkeypatch):
    monkeypatch.delenv('OPTPOKE_DEMO', raising=False)
    assert client.get('/api/runtime').json() == {'demo': False}
    monkeypatch.setenv('OPTPOKE_DEMO', '1')
    assert client.get('/api/runtime').json() == {'demo': True}


def test_private_files_guard():
    private = ['backups/personal.json', 'progress.xlsx', '.env.production', 'x.db-wal', 'docs/progress.png']
    assert violations(private) == private
    assert violations(['data/catalog.json', 'app/demo.py', 'LICENSE']) == []
