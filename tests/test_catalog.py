from app.db import connect


def test_template_catalog_and_variant_keys(local_data):
    with connect() as db:
        assert db.execute('SELECT COUNT(*) FROM pokemon_forms').fetchone()[0] == 1284
        assert db.execute('SELECT COUNT(*) FROM goals WHERE shiny=1').fetchone()[0] == 1214
        assert db.execute('SELECT COUNT(*) FROM goals WHERE shiny=0').fetchone()[0] == 1284
        # The source shiny template repeats the Hoopa keyword on its Unbound row.
        assert db.execute("SELECT COUNT(*) FROM goals WHERE shiny=1 AND form_key IN ('hoopa','hoopa-1')").fetchone()[0] == 2
        # Its shiny Bloodmoon Ursaluna row lacks a Dex number; the other sheet supplies it.
        row = db.execute("SELECT dex_number FROM pokemon_forms WHERE form_key='ursaluna-1'").fetchone()
        assert row[0] == 901


def test_seed_never_overwrites_progress(local_data):
    from app.db import initialize
    with connect() as db:
        db.execute("UPDATE goals SET in_home=1 WHERE form_key='bulbasaur' AND shiny=1")
    initialize()
    with connect() as db:
        assert db.execute("SELECT in_home FROM goals WHERE form_key='bulbasaur' AND shiny=1").fetchone()[0] == 1


def test_goal_validation(client):
    data=client.get('/api/goals?kind=shiny&search=Bulbasaur').json()
    goal=data['items'][0]
    assert client.patch(f"/api/goals/{goal['id']}",json={'target':3,'in_home':2,'obtainability':'obtainable'}).status_code == 200
    assert client.patch(f"/api/goals/{goal['id']}",json={'target':1}).status_code == 422
    assert client.get('/api/overview').json()['shiny']['total'] == 1214
