import pytest
from app import austin_import
from app.db import connect, initialize
from test_austin_separate import rows_for_forms


def goal(client, kind='shiny'):
    return client.get(f'/api/goals?kind={kind}&search=Alakazam').json()['items'][0]


def test_evolution_api_backup_and_completion(client):
    g = goal(client)
    url = f"/api/goals/{g['id']}"
    assert client.patch(url, json={'pending_evolution': True}).json()['in_home'] == 0
    assert client.get('/api/goals?status=pending_evolution').json()['total'] == 1
    assert goal(client, 'normal')['pending_evolution'] == 0
    saved = client.get('/api/backup').json()
    assert client.patch(url, json={'in_home': 1}).json()['pending_evolution'] == 0
    assert client.post('/api/backup', json=saved).status_code == 200
    assert goal(client)['pending_evolution'] == 1
    initialize()
    assert goal(client)['pending_evolution'] == 1
    for item in saved['data']['goals']:
        item.pop('pending_evolution')
        item.pop('ot_exception')
    assert client.post('/api/backup', json=saved).status_code == 200
    assert goal(client)['pending_evolution'] == 0


@pytest.mark.parametrize('mode,home,expected_home,expected_evo', [
    ('merge', 0, 0, 1), ('merge', 1, 0, 1), ('replace', 1, 0, 1),
])
def test_evo_import_overrides_previous_home_on_target(client, monkeypatch, mode, home, expected_home, expected_evo):
    rows = rows_for_forms(150, shiny=True)
    row = next(r for r in rows if r['V'] == 'alakazam')
    row['J'] = 'EVO'
    monkeypatch.setattr(austin_import, 'list_sheet_names', lambda _: {'S-LivingFormLITE'})
    monkeypatch.setattr(austin_import, 'read_sheets', lambda *_: {'S-LivingFormLITE': rows})
    g = goal(client)
    client.patch(f"/api/goals/{g['id']}", json={'in_home': home})
    plan = austin_import.build_austin_plan(b'fictional', mode, 'shiny')
    assert goal(client)['in_home'] == home  # Preview is read-only.
    assert goal(client)['pending_evolution'] == 0
    austin_import.apply_austin_plan(plan)
    assert (goal(client)['in_home'], goal(client)['pending_evolution']) == (expected_home, expected_evo)
    assert goal(client, 'normal')['pending_evolution'] == 0
    with connect() as db:
        assert db.execute("SELECT pending_evolution FROM goals WHERE form_key='kadabra' AND shiny=1").fetchone()[0] == 0
    assert austin_import.build_austin_plan(b'fictional', mode, 'shiny')['counts'].get('changed', 0) == 0

@pytest.mark.parametrize('status,expected_home', [('0', 1), ('1', 0)])
def test_excel_clears_previous_evo_and_sets_exact_home(client, monkeypatch, status, expected_home):
    rows = rows_for_forms(150, shiny=True)
    next(r for r in rows if r['V'] == 'alakazam')['J'] = status
    monkeypatch.setattr(austin_import, 'list_sheet_names', lambda _: {'S-LivingFormLITE'})
    monkeypatch.setattr(austin_import, 'read_sheets', lambda *_: {'S-LivingFormLITE': rows})
    g = goal(client)
    client.patch(f"/api/goals/{g['id']}", json={'target': 3, 'in_home': 2, 'pending_evolution': True})
    plan = austin_import.build_austin_plan(b'fictional')
    assert goal(client)['in_home'] == 2
    austin_import.apply_austin_plan(plan)
    result = goal(client)
    assert (result['in_home'], result['pending_evolution'], result['target']) == (expected_home, 0, 3)
    assert austin_import.build_austin_plan(b'fictional')['counts'].get('changed', 0) == 0
