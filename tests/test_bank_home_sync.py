"""Regressions: Bank transfers, OT origin, user-owned eligibility and HOME."""
from app.db import connect, initialize


def goal(client, shiny=False, species="Bulbasaur"):
    kind = "shiny" if shiny else "normal"
    return client.get(f"/api/goals?kind={kind}&search={species}").json()["items"][0]


def task(client, goal_id=None, *, home=0, caught=None, required=1, origin="unspecified", shiny=False):
    return client.post("/api/bank", json={
        "game": "Crystal", "pokemon": "Bulbasaur", "shiny": shiny,
        "goal_id": goal_id, "required": required,
        "caught": home if caught is None else caught,
        "in_home": home, "ot_origin": origin,
    })


def test_captured_only_and_unlinked_do_not_change_dex(client):
    target = goal(client)
    assert task(client, target["id"], caught=1, home=0, origin="own").status_code == 201
    assert task(client, None, home=1, origin="own").status_code == 201
    assert goal(client)["in_home"] == 0
    assert all(row["synced_home"] == 0 for row in client.get("/api/bank?pending=false").json()["items"])


def test_own_transfer_sync_is_idempotent_and_clears_evo(client):
    original = goal(client)
    assert client.patch(f'/api/goals/{original["id"]}', json={"pending_evolution": True}).status_code == 200
    created = task(client, original["id"], home=1, origin="own")
    assert created.status_code == 201, created.text
    task_id = created.json()["id"]
    assert created.json()["synced_home"] == 1
    updated = goal(client)
    assert updated["in_home"] == 1
    assert updated["pending_evolution"] == 0
    for _ in range(3):
        response = client.patch(f"/api/bank/{task_id}", json={"in_home": 1, "caught": 1})
        assert response.status_code == 200, response.text
        assert response.json()["synced_home"] == 1
    assert goal(client)["in_home"] == 1
    # Correcting a transfer reverses the credit.
    assert client.patch(f"/api/bank/{task_id}", json={"in_home": 0}).status_code == 200
    assert goal(client)["in_home"] == 0


def test_multiple_bank_tasks_share_target_without_duplicates(client):
    g = goal(client)
    first = task(client, g["id"], home=1, origin="own").json()
    second = task(client, g["id"], home=1, origin="own").json()
    assert goal(client)["in_home"] == 1
    assert client.delete(f'/api/bank/{first["id"]}').status_code == 204
    assert goal(client)["in_home"] == 1  # Second transfer still contributes.
    assert client.delete(f'/api/bank/{second["id"]}').status_code == 204
    assert goal(client)["in_home"] == 0


def test_existing_home_baseline_is_not_double_counted(client):
    g = goal(client)
    response = client.patch(f'/api/goals/{g["id"]}', json={"target": 3, "in_home": 2})
    assert response.status_code == 200, response.text
    t = task(client, g["id"], home=1, origin="own").json()
    assert goal(client)["in_home"] == 3
    assert client.patch(f'/api/bank/{t["id"]}', json={"in_home": 0}).status_code == 200
    assert goal(client)["in_home"] == 2
    assert client.patch(f'/api/goals/{g["id"]}', json={"in_home": 1}).status_code == 200
    assert goal(client)["in_home"] == 1


def test_manual_dex_correction_cannot_erase_active_bank_transfer(client):
    g = goal(client)
    t = task(client, g["id"], home=1, origin="own").json()
    r = client.patch(f'/api/goals/{g["id"]}', json={"in_home": 0})
    assert r.status_code == 422
    assert goal(client)["in_home"] == 1
    assert client.patch(f'/api/bank/{t["id"]}', json={"in_home": 0}).status_code == 200
    assert client.patch(f'/api/goals/{g["id"]}', json={"in_home": 0}).status_code == 200


def test_foreign_ot_requires_explicit_unobtainable_status(client):
    g = goal(client)
    t = task(client, g["id"], home=1, origin="other").json()
    assert t["ot_origin"] == "other"
    assert t["ot_exception"] == 1
    assert t["synced_home"] == 0
    assert goal(client)["in_home"] == 0
    assert client.patch(f'/api/goals/{g["id"]}', json={
        "own_ot_obtainability": "unobtainable"}).status_code == 200
    assert goal(client)["in_home"] == 1
    assert client.patch(f'/api/goals/{g["id"]}', json={
        "own_ot_obtainability": "obtainable"}).status_code == 200
    assert goal(client)["in_home"] == 0
    assert client.patch(f'/api/bank/{t["id"]}', json={
        "ot_origin": "own"}).status_code == 200
    assert goal(client)["in_home"] == 1
    assert client.patch(f'/api/bank/{t["id"]}', json={
        "ot_origin": "unspecified"}).status_code == 200
    assert goal(client)["in_home"] == 0


def test_not_marker_does_not_mean_possession_or_prohibit_own_ot(client):
    g = goal(client)
    assert client.patch(f'/api/goals/{g["id"]}', json={
        "ot_exception": True, "own_ot_obtainability": "unverified"}).status_code == 200
    changed = goal(client)
    assert changed["ot_exception"] == 1
    assert changed["own_ot_obtainability"] == "unverified"
    assert changed["in_home"] == 0


def test_relink_and_unlink_corrects_both_goal_totals(client):
    a = goal(client, shiny=False)
    b = goal(client, shiny=True)
    t = task(client, a["id"], home=1, origin="own").json()
    assert goal(client)["in_home"] == 1
    changed = client.patch(f'/api/bank/{t["id"]}', json={
        "goal_id": b["id"], "shiny": True
    })
    assert changed.status_code == 200, changed.text
    assert goal(client)["in_home"] == 0
    assert goal(client, shiny=True)["in_home"] == 1
    assert client.patch(f'/api/bank/{t["id"]}', json={"goal_id": None}).status_code == 200
    assert goal(client, shiny=True)["in_home"] == 0


def test_backup_roundtrip_keeps_bank_credits_and_old_backup_is_safe(client):
    g = goal(client)
    t = task(client, g["id"], home=1, origin="own").json()
    saved = client.get("/api/backup").json()
    assert saved["data"]["bank_tasks"][0]["synced_home"] == 1
    assert saved["data"]["goals"][0].get("manual_home") is not None
    assert client.post("/api/backup", json=saved).status_code == 200
    assert goal(client)["in_home"] == 1
    old = client.get("/api/backup").json()
    for item in old["data"]["goals"]:
        item.pop("manual_home")
        item.pop("own_ot_obtainability")
    for item in old["data"]["bank_tasks"]:
        item.pop("ot_origin")
        item.pop("synced_home")
    assert client.post("/api/backup", json=old).status_code == 200
    with connect() as db:
        row = db.execute("SELECT synced_home,ot_origin FROM bank_tasks WHERE id=?", (t["id"],)).fetchone()
        assert row["synced_home"] == 0
        assert row["ot_origin"] == "unspecified"
    assert goal(client)["in_home"] == 1  # Kept as manual baseline, never multiplied.


def test_existing_linked_task_migration_never_syncs_retroactively(local_data):
    with connect() as db:
        db.execute("DROP TABLE bank_tasks")
        db.execute("CREATE TABLE bank_tasks (id INTEGER PRIMARY KEY,"
                   "game TEXT NOT NULL, pokemon TEXT NOT NULL, form_name TEXT,"
                   "comments TEXT NOT NULL DEFAULT '',shiny INTEGER NOT NULL DEFAULT 0,"
                   "ot_exception INTEGER NOT NULL DEFAULT 0,required INTEGER NOT NULL,"
                   "caught INTEGER NOT NULL DEFAULT 0,in_home INTEGER NOT NULL DEFAULT 0,"
                   "source_row INTEGER,goal_id INTEGER,save_id INTEGER,"
                   "UNIQUE(game,source_row))")
        target = db.execute("SELECT id FROM goals WHERE form_key='bulbasaur' AND shiny=0").fetchone()[0]
        db.execute("INSERT INTO bank_tasks(game,pokemon,shiny,ot_exception,required,caught,in_home,goal_id)"
                   " VALUES('Crystal','Bulbasaur',0,1,1,1,1,?)", (target,))
    initialize()
    with connect() as db:
        row = db.execute("SELECT ot_origin,synced_home FROM bank_tasks").fetchone()
        assert tuple(row) == ("other", 0)
        assert db.execute("SELECT in_home FROM goals WHERE id=?", (target,)).fetchone()[0] == 0
