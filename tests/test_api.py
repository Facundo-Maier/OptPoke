from app.db import connect
from app.math_utils import cumulative_probability


def test_probability():
    assert cumulative_probability(1/4096,0)==0
    assert abs(cumulative_probability(0.01,100)-(1-0.99**100)) < 1e-12
    assert cumulative_probability(1,1)==1
    assert cumulative_probability(0,100)==0


def test_bank_requires_home_transfer(client):
    with connect() as db:
        db.execute("INSERT INTO bank_game_status(game) VALUES('Crystal')")
        id=db.execute("INSERT INTO bank_tasks(game,pokemon,shiny,required) VALUES('Crystal','Celebi',0,1)").lastrowid
    assert client.patch(f'/api/bank/{id}',json={'in_home':1}).status_code==422
    assert client.patch(f'/api/bank/{id}',json={'caught':1,'in_home':1}).status_code==200
    assert client.get('/api/bank').json()['items']==[]


def test_hunt_counter_and_phase(client):
    response=client.post('/api/hunts',json={'pokemon':'Tapu Koko','method':'Dynamax Adventures','probability':0.01})
    assert response.status_code==201
    hunt=response.json()
    assert client.patch(f"/api/hunts/{hunt['id']}",json={'delta':10}).json()['attempts']==10
    assert client.post(f"/api/hunts/{hunt['id']}/phases",json={'at_attempt':9,'note':'Otro shiny'}).status_code==201
    assert client.patch(f"/api/hunts/{hunt['id']}",json={'delta':-11}).status_code==422
    assert len(client.get(f"/api/hunts/{hunt['id']}/phases").json())==1


def test_backup_roundtrip(client):
    original=client.get('/api/backup').json()
    item=client.get('/api/goals?kind=shiny&search=Bulbasaur').json()['items'][0]
    assert client.patch(f"/api/goals/{item['id']}",json={'in_home':1}).status_code==200
    assert client.post('/api/backup',json=original).status_code==200
    assert client.get('/api/overview').json()['shiny']['done']==0


def test_backup_bad_data_is_atomic(client):
    saved=client.get('/api/backup').json()
    saved['data']['goals'][0]['form_key']='no-such-pokemon'
    assert client.post('/api/backup',json=saved).status_code==422
    assert client.get('/api/overview').json()['shiny']['total']==1214


def test_sprite_assets_are_served(client):
    html=client.get('/').text
    assert '/static/sprites.js' in html
    assert client.get('/static/sprites.js').status_code == 200


def test_inline_home_toggle_persists_without_changing_goal_target(client):
    goal = client.get('/api/goals?kind=shiny&search=Bulbasaur').json()['items'][0]
    goal_id = goal['id']
    assert goal['target'] == 1
    assert goal['in_home'] == 0
    first = client.patch(f'/api/goals/{goal_id}', json={'in_home': 1})
    assert first.status_code == 200
    assert first.json()['in_home'] == 1
    assert first.json()['target'] == 1
    assert client.get('/api/goals?kind=shiny&status=done&search=Bulbasaur').json()['items'][0]['id'] == goal_id
    undone = client.patch(f'/api/goals/{goal_id}', json={'in_home': 0})
    assert undone.status_code == 200
    assert undone.json()['in_home'] == 0


def test_home_cannot_exceed_target_even_with_quick_action(client):
    goal = client.get('/api/goals?kind=normal&search=Bulbasaur').json()['items'][0]
    response = client.patch(f"/api/goals/{goal['id']}", json={'in_home': 2})
    assert response.status_code == 422


def test_ot_marker_is_independent_for_shiny_and_normal(client):
    shiny=client.get('/api/goals?kind=shiny&search=Bulbasaur').json()['items'][0]
    normal=client.get('/api/goals?kind=normal&search=Bulbasaur').json()['items'][0]
    assert shiny['ot_exception'] == normal['ot_exception'] == 0
    assert client.patch(f"/api/goals/{shiny['id']}",json={'ot_exception':True}).status_code==200
    assert client.get('/api/goals?kind=shiny&status=ot_exception').json()['total']==1
    assert client.get('/api/goals?kind=normal&status=ot_exception').json()['total']==0
    assert client.patch(f"/api/goals/{normal['id']}",json={'ot_exception':True}).status_code==200
    assert client.get('/api/overview').json()['shiny']['ot_exceptions']==1
    assert client.get('/api/overview').json()['normal']['ot_exceptions']==1
    assert client.patch(f"/api/goals/{shiny['id']}",json={'obtainability':'locked'}).status_code==200
    marked=client.get('/api/goals?kind=shiny&status=ot_exception').json()['items'][0]
    assert marked['ot_exception']==1 and marked['obtainability']=='locked'
    assert client.patch(f"/api/goals/{shiny['id']}",json={'ot_exception':False}).json()['ot_exception']==0


def test_old_backups_with_no_ot_field_restore_and_default_to_unmarked(client):
    shiny=client.get('/api/goals?kind=shiny&search=Bulbasaur').json()['items'][0]
    assert client.patch(f"/api/goals/{shiny['id']}",json={'ot_exception':True}).status_code==200
    modern=client.get('/api/backup').json()
    assert any(goal['ot_exception'] == 1 for goal in modern['data']['goals'])
    older=client.get('/api/backup').json()
    for item in older['data']['goals']:
        del item['ot_exception']
    assert client.post('/api/backup',json=older).status_code==200
    updated=client.get('/api/goals?kind=shiny&search=Bulbasaur').json()['items'][0]
    assert updated['ot_exception']==0


def test_invalid_ot_marker_rejected(client):
    goal=client.get('/api/goals?kind=shiny&search=Bulbasaur').json()['items'][0]
    assert client.patch(f"/api/goals/{goal['id']}",json={'ot_exception':'maybe'}).status_code==422
