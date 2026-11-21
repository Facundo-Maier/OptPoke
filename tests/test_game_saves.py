"""Game catalog/save profiles are independent and preserve legacy Bank rows."""
from app.db import GAMES, connect, initialize


def new_save(client, game="Crystal", name="Principal", shiny_charm=False):
    return client.post("/api/game-saves", json={
        "game": game, "name": name, "shiny_charm": shiny_charm})


def test_catalog_only_and_distinct_saves(client):
    names = {game["name"] for game in client.get("/api/games").json()}
    assert {"Crystal", "Emerald", "Scarlet"}.issubset(names)
    assert all(not item["available"] for item in client.get("/api/games").json())
    assert client.patch("/api/games/Crystal", json={"available": True}).status_code == 200
    assert new_save(client, "Crystal", "Principal", True).status_code == 201
    second = new_save(client, "Crystal", "Otra partida", False)
    assert second.status_code == 201, second.text
    assert new_save(client, "Crystal", "principal").status_code == 409
    saves = client.get("/api/game-saves").json()["items"]
    assert len(saves) == 2
    assert [s["shiny_charm"] for s in saves] == [0, 1] or sorted(
        s["shiny_charm"] for s in saves) == [0, 1]
    assert client.patch(f'/api/game-saves/{second.json()["id"]}',
                        json={"name": "Alt", "shiny_charm": True}).status_code == 200
    assert client.get("/api/game-saves").json()["items"][0]["shiny_charm"] == 1
    assert new_save(client, "Inventado", "X").status_code == 422
    assert client.patch("/api/games/Crystal", json={"available": False}).status_code == 200
    assert new_save(client, "Crystal", "Tercera").status_code == 422
    assert client.get("/api/game-saves?available_only=true").json()["items"] == []


def test_bank_uses_save_game_and_filters_per_save(client):
    assert client.patch("/api/games/Crystal", json={"available": True}).status_code == 200
    first = new_save(client, "Crystal", "Principal", True).json()
    second = new_save(client, "Crystal", "Secundaria").json()
    a = client.post("/api/bank", json={
        "game": "No manual", "save_id": first["id"], "pokemon": "Celebi", "shiny": True})
    b = client.post("/api/bank", json={
        "game": "Crystal", "save_id": second["id"], "pokemon": "Suicune", "shiny": False})
    assert a.status_code == b.status_code == 201, (a.text, b.text)
    assert a.json()["game"] == "Crystal"
    tasks = client.get("/api/bank?pending=false").json()["items"]
    assert {t["save_name"] for t in tasks} == {"Principal", "Secundaria"}
    by_first = client.get(f'/api/bank?pending=false&save_id={first["id"]}').json()["items"]
    assert [t["pokemon"] for t in by_first] == ["Celebi"]
    assert client.delete(f'/api/game-saves/{first["id"]}').status_code == 409
    assert client.patch(f'/api/bank/{a.json()["id"]}', json={"save_id": None}).status_code == 200
    assert client.delete(f'/api/game-saves/{first["id"]}').status_code == 204
    assert client.get("/api/bank?pending=false&save_id=0").json()["items"][0]["pokemon"] == "Celebi"


def test_legacy_task_survives_and_can_be_assigned(client):
    with connect() as db:
        db.execute("INSERT OR IGNORE INTO bank_game_status(game) VALUES('Emerald')")
        task_id = db.execute(
            "INSERT INTO bank_tasks(game,pokemon,required,source_row) "
            "VALUES('Emerald','Rayquaza',1,22)").lastrowid
    before = client.get("/api/bank?pending=false").json()["items"][0]
    assert before["save_id"] is None and before["game"] == "Emerald"
    assert client.patch("/api/games/Emerald", json={"available": True}).status_code == 200
    created = new_save(client, "Emerald", "Mi partida").json()
    assert client.patch(f"/api/bank/{task_id}", json={"save_id": created["id"]}).status_code == 200
    after = client.get("/api/bank?pending=false").json()["items"][0]
    assert after["source_row"] == 22 and after["save_name"] == "Mi partida"
    # No progress is written to the Dex.
    goals = client.get("/api/goals?kind=shiny&search=Rayquaza").json()["items"]
    assert all(goal["in_home"] == 0 for goal in goals)


def test_reassignment_to_another_game_clears_old_import_row(client):
    with connect() as db:
        db.execute("INSERT OR IGNORE INTO bank_game_status(game) VALUES('Crystal')")
        id_ = db.execute(
            "INSERT INTO bank_tasks(game,pokemon,required,source_row) "
            "VALUES('Crystal','Celebi',1,8)").lastrowid
    assert client.patch("/api/games/Emerald", json={"available": True}).status_code == 200
    save = new_save(client, "Emerald", "Nueva partida").json()
    updated = client.patch(f"/api/bank/{id_}", json={"save_id": save["id"]})
    assert updated.status_code == 200, updated.text
    assert updated.json()["game"] == "Emerald"
    assert updated.json()["source_row"] is None


def test_backup_preserves_saves_and_accepts_legacy_backup(client):
    assert client.patch("/api/games/Crystal", json={"available": True}).status_code == 200
    save = new_save(client, "Crystal", "Principal").json()
    task = client.post("/api/bank", json={
        "game": "Crystal", "save_id": save["id"], "pokemon": "Celebi"})
    assert task.status_code == 201
    original = client.get("/api/backup").json()
    assert original["data"]["game_saves"][0]["name"] == "Principal"
    assert client.post("/api/backup", json=original).status_code == 200
    restored = client.get("/api/bank?pending=false").json()["items"]
    assert restored[0]["save_id"] == save["id"]
    old = client.get("/api/backup").json()
    old["data"].pop("game_saves")
    for row in old["data"]["bank_tasks"]:
        row.pop("save_id")
    response = client.post("/api/backup", json=old)
    assert response.status_code == 200, response.text
    assert client.get("/api/game-saves").json()["items"] == []
    assert client.get("/api/bank?pending=false").json()["items"][0]["save_id"] is None


def test_legacy_schema_migrates_additively(local_data):
    with connect() as db:
        db.execute("INSERT OR IGNORE INTO bank_game_status(game) VALUES('Crystal')")
        db.execute("DROP TABLE bank_tasks")
        db.execute("""CREATE TABLE bank_tasks (
            id INTEGER PRIMARY KEY, game TEXT NOT NULL REFERENCES bank_game_status(game),
            pokemon TEXT NOT NULL, form_name TEXT, comments TEXT NOT NULL DEFAULT '',
            shiny INTEGER NOT NULL DEFAULT 1, ot_exception INTEGER NOT NULL DEFAULT 0,
            required INTEGER NOT NULL, caught INTEGER NOT NULL DEFAULT 0,
            in_home INTEGER NOT NULL DEFAULT 0, source_row INTEGER,
            goal_id INTEGER REFERENCES goals(id) ON DELETE SET NULL,
            UNIQUE(game,source_row))""")
        db.execute("INSERT INTO bank_tasks(game,pokemon,required,source_row) VALUES('Crystal','Celebi',1,44)")
    initialize()
    with connect() as db:
        fields = {row["name"] for row in db.execute("PRAGMA table_info(bank_tasks)")}
        assert "save_id" in fields
        entry = db.execute("SELECT game,pokemon,source_row,save_id FROM bank_tasks").fetchone()
        assert tuple(entry) == ("Crystal", "Celebi", 44, None)
    initialize()


def test_one_time_legacy_defaults_reset_only_when_untouched(local_data):
    with connect() as db:
        db.execute("UPDATE games SET available=1")
        db.execute("DELETE FROM import_history WHERE digest='games-unselected-by-default-v1'")
    initialize()
    with connect() as db:
        assert db.execute("SELECT SUM(available) FROM games").fetchone()[0] == 0
        db.execute("UPDATE games SET available=1 WHERE name='Emerald'")
    initialize()
    with connect() as db:
        assert db.execute("SELECT available FROM games WHERE name='Emerald'").fetchone()[0] == 1


def test_legacy_customized_games_and_saves_are_preserved(local_data):
    with connect() as db:
        db.execute("UPDATE games SET available=1 WHERE name='Crystal'")
        db.execute("UPDATE games SET available=0 WHERE name='Emerald'")
        db.execute("DELETE FROM import_history WHERE digest='games-unselected-by-default-v1'")
    initialize()
    with connect() as db:
        assert db.execute("SELECT available FROM games WHERE name='Crystal'").fetchone()[0] == 1
        assert db.execute("SELECT available FROM games WHERE name='Emerald'").fetchone()[0] == 0
        db.execute("UPDATE games SET available=1")
        db.execute("INSERT INTO game_saves(game,name) VALUES('Crystal','Mi partida')")
        db.execute("DELETE FROM import_history WHERE digest='games-unselected-by-default-v1'")
    initialize()
    with connect() as db:
        assert db.execute("SELECT COUNT(*) FROM games WHERE available=1").fetchone()[0] == len(GAMES)
        assert db.execute("SELECT name FROM game_saves").fetchone()[0] == "Mi partida"
