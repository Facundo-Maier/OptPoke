"""Primer paso de la v0.2: previsualizar vínculos Bank sin sincronizar progreso."""
from app.db import connect


def _task(db, *, name, form=None, shiny=0, required=1, caught=0, home=0):
    db.execute("INSERT OR IGNORE INTO bank_game_status(game) VALUES ('Crystal')")
    return db.execute(
        "INSERT INTO bank_tasks(game,pokemon,form_name,shiny,required,caught,in_home) "
        "VALUES(?,?,?,?,?,?,?)",
        ("Crystal", name, form, shiny, required, caught, home),
    ).lastrowid


def test_bank_preview_does_not_write_goals_or_tasks(client):
    with connect() as db:
        _task(db, name="Bulbasaur", shiny=0, required=2, caught=1, home=1)
        before_goals = db.execute(
            "SELECT id,in_home,target FROM goals WHERE form_key='bulbasaur' AND shiny=0"
        ).fetchone()
        before_tasks = db.execute("SELECT id,caught,in_home FROM bank_tasks").fetchall()
    response = client.get("/api/bank/reconciliation")
    assert response.status_code == 200
    body = response.json()
    assert body["read_only"] is True
    assert body["counts"] == {"total": 1, "suggested": 1, "ambiguous": 0, "unmatched": 0}
    item = body["items"][0]
    assert item["status"] == "suggested"
    assert item["suggestion"]["form_key"] == "bulbasaur"
    assert item["suggestion"]["shiny"] is False
    assert item["suggestion"]["goal_in_home"] == 0
    assert item["bank_in_home"] == 1
    with connect() as db:
        after_goals = db.execute(
            "SELECT id,in_home,target FROM goals WHERE form_key='bulbasaur' AND shiny=0"
        ).fetchone()
        after_tasks = db.execute("SELECT id,caught,in_home FROM bank_tasks").fetchall()
    assert tuple(before_goals) == tuple(after_goals)
    assert [tuple(row) for row in before_tasks] == [tuple(row) for row in after_tasks]


def test_bank_preview_never_assumes_base_form_for_ambiguous_species(client):
    with connect() as db:
        _task(db, name="Pikachu", shiny=0)
    item = client.get("/api/bank/reconciliation").json()["items"][0]
    assert item["status"] == "ambiguous"
    assert item["suggestion"] is None
    assert len(item["available_forms"]) > 1


def test_bank_preview_recognizes_explicit_form_and_shiny_independently(client):
    with connect() as db:
        _task(db, name="Pikachu", form="World Cap", shiny=0)
        _task(db, name="Bulbasaur", shiny=1)
        _task(db, name="Pikachu", form="World Cap", shiny=1)
    items = client.get("/api/bank/reconciliation").json()["items"]
    assert items[0]["suggestion"]["form_key"] == "pikachu-9"
    assert items[0]["suggestion"]["shiny"] is False
    shiny = [item for item in items if item["pokemon"] == "Bulbasaur"][0]
    assert shiny["suggestion"]["shiny"] is True
    # Pikachu World Cap no cuenta automáticamente como objetivo shiny si no está en S-LITE.
    world_shiny = [item for item in items if item["pokemon"] == "Pikachu" and item["shiny"]][0]
    assert world_shiny["status"] == "unmatched"
    assert world_shiny["suggestion"] is None


def test_bank_preview_requires_exact_form_and_does_not_guess(client):
    with connect() as db:
        _task(db, name="Pikachu", form="Forma inventada", shiny=0)
        _task(db, name="Especie desconocida", shiny=0)
    result = client.get("/api/bank/reconciliation").json()
    assert result["counts"] == {"total": 2, "suggested": 0, "ambiguous": 0, "unmatched": 2}
    assert all(row["suggestion"] is None for row in result["items"])


def test_bank_preview_normalizes_accents_spaces_and_case(client):
    with connect() as db:
        _task(db, name="  FLABÉBÉ  ", form=" Red Flower ", shiny=0)
    item = client.get("/api/bank/reconciliation").json()["items"][0]
    assert item["status"] == "suggested"
    assert item["suggestion"]["species"] == "Flabébé"


def test_bank_preview_does_not_sync_after_updating_task(client):
    with connect() as db:
        task = _task(db, name="Bulbasaur", shiny=0)
        initial = db.execute(
            "SELECT in_home FROM goals WHERE form_key='bulbasaur' AND shiny=0"
        ).fetchone()[0]
    response = client.patch(f"/api/bank/{task}", json={"caught": 1, "in_home": 1})
    assert response.status_code == 200
    with connect() as db:
        assert db.execute(
            "SELECT in_home FROM goals WHERE form_key='bulbasaur' AND shiny=0"
        ).fetchone()[0] == initial
