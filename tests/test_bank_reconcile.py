"""Bank is a modifiable TODO list; Dex membership is optional and explicit."""
from app.db import connect, initialize


def _goal(client, species="Bulbasaur", shiny=False):
    kind = "shiny" if shiny else "normal"
    return client.get(f"/api/goals?kind={kind}&search={species}").json()["items"][0]


def test_bank_task_crud_is_independent_of_dex(client):
    goal = _goal(client)
    resp = client.post("/api/bank", json={
        "game": "Crystal", "pokemon": "Bulbasaur", "shiny": False,
        "required": 3, "caught": 1, "in_home": 0,
        "comments": "Criar antes de transferir",
    })
    assert resp.status_code == 201, resp.text
    task = resp.json()
    assert task["goal_id"] is None
    assert task["source_row"] is None
    bank_list = client.get("/api/bank?pending=false").json()["items"]
    assert bank_list[0]["goal_id"] is None
    assert bank_list[0]["linked_form_key"] is None
    assert client.patch(f'/api/bank/{task["id"]}', json={
        "comments": "Nueva nota", "required": 3, "caught": 2,
        "in_home": 1, "game": "Emerald"
    }).status_code == 200
    changed = client.get("/api/bank?pending=false").json()["items"][0]
    assert (changed["game"], changed["comments"], changed["caught"], changed["in_home"]) == (
        "Emerald", "Nueva nota", 2, 1)
    assert client.get("/api/goals?kind=normal&search=Bulbasaur").json()["items"][0]["in_home"] == goal["in_home"]
    assert client.delete(f'/api/bank/{task["id"]}').status_code == 204
    assert client.delete(f'/api/bank/{task["id"]}').status_code == 404
    assert client.get("/api/bank?pending=false").json()["items"] == []
    assert client.get("/api/goals?kind=normal&search=Bulbasaur").json()["items"][0]["in_home"] == goal["in_home"]


def test_bank_explicit_link_and_unlink_never_sync_home(client):
    goal = _goal(client)
    task = client.post("/api/bank", json={
        "game": "Crystal", "pokemon": "Bulbasaur", "shiny": False,
        "required": 1, "caught": 1, "in_home": 1,
        "goal_id": goal["id"],
    })
    assert task.status_code == 201, task.text
    item = client.get("/api/bank?pending=false").json()["items"][0]
    assert item["goal_id"] == goal["id"]
    assert item["linked_form_key"] == goal["form_key"]
    assert item["linked_species"] == goal["species"]
    assert client.get("/api/goals?kind=normal&search=Bulbasaur").json()["items"][0]["in_home"] == 0
    assert client.patch(f'/api/bank/{task.json()["id"]}', json={"goal_id": None}).status_code == 200
    assert client.get("/api/bank?pending=false").json()["items"][0]["goal_id"] is None


def test_link_requires_existing_species_form_and_same_shiny(client):
    normal = _goal(client)
    shiny = _goal(client, shiny=True)
    base = {"game": "Crystal", "pokemon": "Bulbasaur", "shiny": False, "goal_id": normal["id"]}
    assert client.post("/api/bank", json=base).status_code == 201
    assert client.post("/api/bank", json={**base, "goal_id": shiny["id"]}).status_code == 422
    assert client.post("/api/bank", json={**base, "goal_id": 999999}).status_code == 422
    assert client.post("/api/bank", json={**base, "pokemon": "Pikachu"}).status_code == 422
    assert client.post("/api/bank", json={**base, "form_name": "World Cap"}).status_code == 422
    # Existing linked tasks cannot silently change the species or shiny.
    task_id = client.get("/api/bank?pending=false").json()["items"][0]["id"]
    assert client.patch(f"/api/bank/{task_id}", json={"pokemon": "Pikachu"}).status_code == 422
    assert client.patch(f"/api/bank/{task_id}", json={"shiny": True}).status_code == 422


def test_bank_tasks_without_catalog_entries_are_valid_todos(client):
    response = client.post("/api/bank", json={
        "game": "Crystal", "pokemon": "Meta externa sin entrada", "form_name": "Evento",
        "shiny": True, "required": 2
    })
    assert response.status_code == 201, response.text
    item = client.get("/api/bank?pending=false").json()["items"][0]
    assert item["goal_id"] is None
    assert item["pokemon"] == "Meta externa sin entrada"
    assert item["form_name"] == "Evento"


def test_bank_goal_options_only_return_actual_dex_goals(client):
    empty = client.get("/api/bank/goal-options?search=P").json()
    assert empty["items"] == []
    results = client.get("/api/bank/goal-options?search=World%20Cap&shiny=false").json()["items"]
    assert len(results) >= 1
    assert any(row["form_key"] == "pikachu-9" and row["shiny"] == 0 for row in results)
    shiny_results = client.get("/api/bank/goal-options?search=World%20Cap&shiny=true").json()["items"]
    assert all(row["shiny"] == 1 for row in shiny_results)
    assert not any(row["form_key"] == "pikachu-9" for row in shiny_results)


def test_bank_link_counter_validation_and_unlink(client):
    goal = _goal(client)
    task = client.post("/api/bank", json={
        "game": "Crystal", "pokemon": "Bulbasaur", "shiny": False,
        "required": 2, "caught": 2, "in_home": 1, "goal_id": goal["id"]
    }).json()
    assert client.patch(f'/api/bank/{task["id"]}', json={"in_home": 3}).status_code == 422
    assert client.patch(f'/api/bank/{task["id"]}', json={"caught": 0}).status_code == 422
    assert client.patch(f'/api/bank/{task["id"]}', json={"goal_id": None, "shiny": True}).status_code == 200
    assert client.get("/api/bank?pending=false").json()["items"][0]["goal_id"] is None


def test_old_bank_backup_without_goal_id_restores_as_independent(client):
    goal = _goal(client)
    create = client.post("/api/bank", json={"game": "Crystal", "pokemon": "Bulbasaur",
                                              "shiny": False, "goal_id": goal["id"]})
    assert create.status_code == 201
    saved = client.get("/api/backup").json()
    assert saved["data"]["bank_tasks"][0]["goal_id"] == goal["id"]
    old = client.get("/api/backup").json()
    for task in old["data"]["bank_tasks"]:
        task.pop("goal_id")
    response = client.post("/api/backup", json=old)
    assert response.status_code == 200, response.text
    assert client.get("/api/bank?pending=false").json()["items"][0]["goal_id"] is None


def test_legacy_bank_table_migration_preserves_todos(local_data):
    with connect() as db:
        db.execute("INSERT OR IGNORE INTO bank_game_status(game) VALUES('Crystal')")
        db.execute("DROP TABLE bank_tasks")
        db.execute("""CREATE TABLE bank_tasks(
            id INTEGER PRIMARY KEY,
            game TEXT NOT NULL REFERENCES bank_game_status(game),
            pokemon TEXT NOT NULL,
            form_name TEXT, comments TEXT NOT NULL DEFAULT '',
            shiny INTEGER NOT NULL DEFAULT 1, ot_exception INTEGER NOT NULL DEFAULT 0,
            required INTEGER NOT NULL, caught INTEGER NOT NULL DEFAULT 0,
            in_home INTEGER NOT NULL DEFAULT 0, source_row INTEGER,
            UNIQUE(game,source_row))""")
        db.execute("INSERT INTO bank_tasks(game,pokemon,required,caught,in_home,source_row) VALUES('Crystal','Celebi',1,1,0,17)")
    initialize()
    with connect() as db:
        fields = {row["name"] for row in db.execute("PRAGMA table_info(bank_tasks)")}
        assert "goal_id" in fields
        task = db.execute("SELECT pokemon,source_row,caught,in_home,goal_id FROM bank_tasks").fetchone()
        assert tuple(task) == ("Celebi", 17, 1, 0, None)
        initialize()  # Migration is idempotent
