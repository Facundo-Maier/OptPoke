"""Regression tests for shiny locks, catalog migration and old backups."""

import json

from app.db import LOCKED_SHINIES, connect, initialize, seed_locked_shinies


def test_curated_locks_are_visible_in_filter(client):
    result = client.get('/api/goals?kind=shiny&status=locked&limit=250')
    assert result.status_code == 200
    data = result.json()
    assert data['total'] == 30
    keys = {g['form_key'] for g in data['items']}
    assert {'victini', 'hoopa', 'cosmog', 'vivillon-19', 'ursaluna-1'} <= keys
    assert 'bulbasaur' not in keys
    assert 'vivillon-18' not in keys  # Fancy can be shiny
    assert client.get('/api/overview').json()['shiny']['locked'] == data['total']


def test_only_shiny_forms_can_be_auto_locked(client):
    assert client.get('/api/goals?kind=normal&status=locked').json()['total'] == 0
    # Minior Core and Alcremie sweet variants missing from the LITE shiny
    # catalog are not evidence of shiny locks.
    assert client.get('/api/goals?kind=shiny&search=Minior&status=locked').json()['total'] == 0
    assert client.get('/api/goals?kind=shiny&search=Alcremie&status=locked').json()['total'] == 0


def test_initialize_never_overwrites_personal_changes(client):
    victim = client.get('/api/goals?kind=shiny&search=Victini').json()['items'][0]
    assert client.patch(f"/api/goals/{victim['id']}", json={'obtainability': 'obtainable'}).status_code == 200
    initialize()
    updated = client.get('/api/goals?kind=shiny&search=Victini').json()['items'][0]
    assert updated['obtainability'] == 'obtainable'
    # Explicitly clearing the lock must not be reset on later starts, either.
    assert client.patch(f"/api/goals/{victim['id']}", json={'obtainability': 'unverified'}).status_code == 200
    initialize()
    again = client.get('/api/goals?kind=shiny&search=Victini').json()['items'][0]
    assert again['obtainability'] == 'unverified'


def test_migrate_v011_and_restore_old_backup(client):
    locks = json.loads(LOCKED_SHINIES.read_text(encoding='utf-8'))
    with connect() as db:
        db.execute("DELETE FROM import_history WHERE digest=?", (f"shiny-locks:{locks['version']}",))
        db.execute("UPDATE goals SET obtainability='unverified' WHERE form_key IN ('victini','cosmog') AND shiny=1")
    # Startup upgrades an old database without losing other goal progress.
    with connect() as db:
        db.execute("UPDATE goals SET in_home=1 WHERE form_key='bulbasaur' AND shiny=1")
    initialize()
    with connect() as db:
        assert db.execute("SELECT obtainability FROM goals WHERE form_key='victini' AND shiny=1").fetchone()[0] == 'locked'
        assert db.execute("SELECT in_home FROM goals WHERE form_key='bulbasaur' AND shiny=1").fetchone()[0] == 1

    # A backup made before v0.1.2 would not include this migration marker.
    old_backup = client.get('/api/backup').json()
    old_backup['data']['import_history'] = [row for row in old_backup['data']['import_history']
                                            if row['digest'] != f"shiny-locks:{locks['version']}"]
    for goal in old_backup['data']['goals']:
        if goal['form_key'] in ('victini', 'cosmog') and goal['shiny'] == 1:
            goal['obtainability'] = 'unverified'
    assert client.post('/api/backup', json=old_backup).status_code == 200
    with connect() as db:
        assert db.execute("SELECT obtainability FROM goals WHERE form_key='cosmog' AND shiny=1").fetchone()[0] == 'locked'
        assert db.execute("SELECT in_home FROM goals WHERE form_key='bulbasaur' AND shiny=1").fetchone()[0] == 1
