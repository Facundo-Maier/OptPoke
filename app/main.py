"""Local JSON API + lightweight frontend. Run: uvicorn app.main:app --reload."""
from __future__ import annotations

import json
import os
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .db import GAMES, ROOT, connect, initialize, seed_locked_shinies
from .math_utils import cumulative_probability
from .austin_import import build_austin_plan, apply_austin_plan
from .sprite_cache import (
    cached_image, cached_variety, cache_status, InvalidSpriteSource,
    MissingRemoteSprite, RemoteSpriteUnavailable,
)

@asynccontextmanager
async def lifespan(_app: FastAPI):
    initialize()
    yield


app = FastAPI(title="Opt. Poke", version="0.1.99", description="Living Shiny Dex personal", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")


@app.get("/api/runtime")
def runtime():
    return {"demo": os.environ.get("OPTPOKE_DEMO") == "1"}


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(ROOT / "static" / "index.html")


def rows(result):
    return [dict(row) for row in result]


@app.get("/api/sprites/image", include_in_schema=False)
def sprite_image(url: str):
    try:
        data, media_type = cached_image(url)
        return Response(data, media_type=media_type,
                        headers={"Cache-Control": "private, max-age=2592000"})
    except InvalidSpriteSource as exc:
        raise HTTPException(400, str(exc)) from exc
    except MissingRemoteSprite as exc:
        raise HTTPException(404, "Esta imagen no existe en la fuente") from exc
    except RemoteSpriteUnavailable as exc:
        raise HTTPException(503, str(exc)) from exc


@app.get("/api/sprites/variety/{key}", include_in_schema=False)
def sprite_variety(key: str):
    try:
        return cached_variety(key)
    except InvalidSpriteSource as exc:
        raise HTTPException(400, str(exc)) from exc
    except MissingRemoteSprite as exc:
        raise HTTPException(404, "Variedad no encontrada") from exc
    except RemoteSpriteUnavailable as exc:
        raise HTTPException(503, str(exc)) from exc


@app.get("/api/sprites/cache-status")
def sprite_cache_status():
    return cache_status()


@app.get("/api/overview")
def overview():
    with connect() as db:
        shiny = db.execute("""SELECT COUNT(*) AS total, SUM(CASE WHEN in_home >= target THEN 1 ELSE 0 END) AS done,
                     SUM(CASE WHEN obtainability='locked' THEN 1 ELSE 0 END) AS locked,
                     SUM(ot_exception) AS ot_exceptions
                     FROM goals WHERE shiny=1""").fetchone()
        normal = db.execute("""SELECT COUNT(*) AS total, SUM(CASE WHEN in_home >= target THEN 1 ELSE 0 END) AS done,
                     SUM(ot_exception) AS ot_exceptions
                     FROM goals WHERE shiny=0""").fetchone()
        bank = db.execute("""SELECT COALESCE(SUM(required),0) AS total,
                     COALESCE(SUM(in_home),0) AS done,
                     SUM(CASE WHEN in_home<required THEN 1 ELSE 0 END) AS open_tasks
                     FROM bank_tasks""").fetchone()
        hunts = db.execute("SELECT COUNT(*) FROM hunts WHERE status='active'").fetchone()[0]
    return {"shiny": dict(shiny), "normal": dict(normal), "bank": dict(bank), "active_hunts": hunts}


@app.get("/api/goals")
def list_goals(kind: Literal["shiny", "normal"] = "shiny", search: str = "",
               status: Literal["all", "missing", "done", "locked", "ot_exception", "pending_evolution"] = "all",
               sort: Literal["dex", "name"] = "dex",
               offset: int = Query(0, ge=0), limit: int = Query(72, ge=1, le=250)):
    where = ["g.shiny=?"]
    args: list = [int(kind == "shiny")]
    if search:
        where.append("(f.species LIKE ? OR f.form_name LIKE ? OR CAST(f.dex_number AS TEXT) LIKE ?)")
        args.extend([f"%{search}%"] * 3)
    if status == "missing": where.append("g.in_home<g.target AND g.obtainability!='locked'")
    if status == "done": where.append("g.in_home>=g.target")
    if status == "locked": where.append("g.obtainability='locked'")
    if status == "ot_exception": where.append("g.ot_exception=1")
    if status == "pending_evolution": where.append("g.pending_evolution=1 AND g.in_home<g.target")
    filter_sql = " AND ".join(where)
    ordering = "f.dex_number, f.form_key" if sort == "dex" else "f.species COLLATE NOCASE, f.form_name"
    with connect() as db:
        total = db.execute(f"SELECT COUNT(*) FROM goals g JOIN pokemon_forms f ON f.form_key=g.form_key WHERE {filter_sql}", args).fetchone()[0]
        items = rows(db.execute(f"""SELECT g.*,f.dex_number,f.species,f.form_name,f.source_form,f.source_variant
                  FROM goals g JOIN pokemon_forms f ON f.form_key=g.form_key
                  WHERE {filter_sql} ORDER BY {ordering} LIMIT ? OFFSET ?""", args + [limit, offset]))
    return {"items": items, "total": total, "offset": offset, "limit": limit}


class GoalPatch(BaseModel):
    target: int | None = Field(None, ge=1, le=999)
    in_home: int | None = Field(None, ge=0, le=999)
    obtainability: Literal["unverified", "obtainable", "locked"] | None = None
    ot_exception: bool | None = None
    pending_evolution: bool | None = None
    own_ot_obtainability: Literal["unverified", "obtainable", "unobtainable"] | None = None


def _recalculate_goal_home(db, goal_id: int):
    """Manual baseline plus credited Bank transfers, with a target cap.

    Linked Bank tasks can outnumber a goal's target, but never create
    extra specimens in the Dex. All changes run within the caller's transaction.
    """
    goal = db.execute("SELECT id,target,manual_home FROM goals WHERE id=?", (goal_id,)).fetchone()
    if not goal:
        return
    credited = db.execute(
        "SELECT COALESCE(SUM(synced_home),0) FROM bank_tasks WHERE goal_id=?",
        (goal_id,)).fetchone()[0]
    home = min(goal["target"], goal["manual_home"] + credited)
    db.execute(
        "UPDATE goals SET in_home=?,pending_evolution=CASE WHEN ?>=target THEN 0 ELSE pending_evolution END "
        "WHERE id=?", (home, home, goal_id))


def _bank_credit(db, task: dict) -> int:
    """Only transfers with a declared OT origin are Dex-eligible."""
    if task["goal_id"] is None:
        return 0
    if task["ot_origin"] == "own":
        return task["in_home"]
    if task["ot_origin"] == "other":
        status = db.execute("SELECT own_ot_obtainability FROM goals WHERE id=?",
                            (task["goal_id"],)).fetchone()
        if status and status["own_ot_obtainability"] == "unobtainable":
            return task["in_home"]
    return 0


def _update_bank_credit(db, task_id: int, old_goal_id: int | None = None):
    task = dict(db.execute("SELECT * FROM bank_tasks WHERE id=?", (task_id,)).fetchone())
    new_credit = _bank_credit(db, task)
    db.execute("UPDATE bank_tasks SET synced_home=? WHERE id=?", (new_credit, task_id))
    for goal_id in {old_goal_id, task["goal_id"]} - {None}:
        _recalculate_goal_home(db, goal_id)


@app.patch("/api/goals/{goal_id}")
def update_goal(goal_id: int, patch: GoalPatch):
    provided = patch.model_dump(exclude_unset=True)
    with connect() as db:
        current = db.execute("SELECT * FROM goals WHERE id=?", (goal_id,)).fetchone()
        if not current: raise HTTPException(404, "Objetivo no encontrado")
        if not provided: return dict(current)
        if any(v is None for v in provided.values()): raise HTTPException(422, "Valor nulo no permitido")
        target = provided.get("target", current["target"])
        home = provided.get("in_home", current["in_home"])
        if home > target: raise HTTPException(422, "En HOME no puede superar el objetivo")
        synced = db.execute("SELECT COALESCE(SUM(synced_home),0) FROM bank_tasks WHERE goal_id=?",
                            (goal_id,)).fetchone()[0]
        if "in_home" in provided:
            if home != current["in_home"]:
                if home < min(target, synced):
                    raise HTTPException(
                        422, "Hay transferencias sincronizadas desde Bank; corregí primero esas tareas")
                provided["manual_home"] = max(0, home - synced)
            del provided["in_home"]
        if "pending_evolution" in provided: provided["pending_evolution"] = int(provided["pending_evolution"])
        if "ot_exception" in provided: provided["ot_exception"] = int(provided["ot_exception"])
        # Preserve manually set counts independently of OT flags and shiny locks.
        if provided:
            db.execute("UPDATE goals SET " + ", ".join(f"{field}=?" for field in provided) + " WHERE id=?",
                       [*provided.values(), goal_id])
        if "own_ot_obtainability" in provided:
            for task in db.execute("SELECT id FROM bank_tasks WHERE goal_id=?", (goal_id,)).fetchall():
                data = dict(db.execute("SELECT * FROM bank_tasks WHERE id=?", (task["id"],)).fetchone())
                db.execute("UPDATE bank_tasks SET synced_home=? WHERE id=?",
                           (_bank_credit(db, data), task["id"]))
        _recalculate_goal_home(db, goal_id)
        return dict(db.execute("SELECT * FROM goals WHERE id=?", (goal_id,)).fetchone())


@app.post("/api/austin/preview")
async def preview_austin(request: Request, mode: Literal["merge", "replace"] = "merge",
                         source: Literal["shiny", "normal"] | None = None):
    if request.headers.get("content-length") and int(request.headers["content-length"]) > 12_000_000:
        raise HTTPException(413, "El Excel supera los 12 MB")
    payload = await request.body()
    try:
        plan = build_austin_plan(payload, mode, source)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return {"digest": plan["digest"], "mode": mode, "sheets": plan.get("sheets", []), "counts": plan["counts"],
            "changes": plan["changes"][:30], "warnings": plan["warnings"],
            "warnings_total": plan["warnings_total"]}


@app.post("/api/austin/apply")
async def apply_austin(request: Request, digest: str, mode: Literal["merge", "replace"] = "merge",
                       source: Literal["shiny", "normal"] | None = None):
    if request.headers.get("content-length") and int(request.headers["content-length"]) > 12_000_000:
        raise HTTPException(413, "El Excel supera los 12 MB")
    payload = await request.body()
    try:
        plan = build_austin_plan(payload, mode, source)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    if digest != plan["digest"]:
        raise HTTPException(409, "El archivo cambió desde la vista previa; volvé a revisarlo")
    return apply_austin_plan(plan)


@app.get("/api/bank/goal-options")
def bank_goal_options(search: str = Query("", max_length=100),
                      shiny: bool | None = None):
    """Candidates are shown only when the user explicitly searches the Dex."""
    search = search.strip()
    if len(search) < 2:
        return {"items": []}
    conditions = ["(f.species LIKE ? OR f.form_name LIKE ? OR CAST(f.dex_number AS TEXT) LIKE ?)"]
    params: list = [f"%{search}%"] * 3
    if shiny is not None:
        conditions.append("g.shiny=?")
        params.append(int(shiny))
    with connect() as db:
        items = rows(db.execute(
            "SELECT g.id AS goal_id,g.form_key,g.shiny,f.species,f.form_name,f.dex_number "
            "FROM goals g JOIN pokemon_forms f ON g.form_key=f.form_key "
            "WHERE " + " AND ".join(conditions) +
            " ORDER BY f.dex_number,f.form_key LIMIT 40", params))
    return {"items": items}


@app.get("/api/bank")
def list_bank(game: str = "", search: str = "", pending: bool = True, save_id: int | None = Query(None, ge=0)):
    conditions = ["1=1"]
    params: list = []
    if game:
        conditions.append("t.game=?")
        params.append(game)
    if search:
        conditions.append("(t.pokemon LIKE ? OR t.form_name LIKE ? OR t.comments LIKE ?)")
        params.extend([f"%{search}%"] * 3)
    if pending: conditions.append("t.in_home<t.required")
    if save_id is not None:
        if save_id == 0:
            conditions.append("t.save_id IS NULL")
        else:
            conditions.append("t.save_id=?")
            params.append(save_id)
    with connect() as db:
        items = rows(db.execute(
            """SELECT t.*,s.started,s.prepared,
                sv.name AS save_name,sv.shiny_charm AS save_shiny_charm,
                g.form_key AS linked_form_key,
                f.species AS linked_species,f.form_name AS linked_form_name,
                f.dex_number AS linked_dex_number,g.shiny AS linked_shiny
                FROM bank_tasks t JOIN bank_game_status s USING(game)
                LEFT JOIN game_saves sv ON sv.id=t.save_id
                LEFT JOIN goals g ON g.id=t.goal_id
                LEFT JOIN pokemon_forms f ON f.form_key=g.form_key
                WHERE """ + " AND ".join(conditions) +
            " ORDER BY t.game,t.source_row,t.id", params))
        statuses = rows(db.execute("SELECT * FROM bank_game_status ORDER BY game"))
    # Preserve the SQL order of tasks inside each game while grouping games
    # consistently with the catalog and save selectors.
    items.sort(key=lambda item: (GAME_ORDER.get(item["game"], len(GAMES)), item["game"]))
    statuses.sort(key=lambda item: (GAME_ORDER.get(item["game"], len(GAMES)), item["game"]))
    return {"items": items, "games": statuses}


class BankTaskCreate(BaseModel):
    game: str = Field(min_length=1, max_length=100)
    pokemon: str = Field(min_length=1, max_length=100)
    form_name: str | None = Field(default=None, max_length=100)
    comments: str = Field(default="", max_length=1000)
    shiny: bool = True
    ot_exception: bool = False
    required: int = Field(default=1, ge=1, le=999)
    caught: int = Field(default=0, ge=0, le=999)
    in_home: int = Field(default=0, ge=0, le=999)
    goal_id: int | None = Field(default=None, ge=1)
    save_id: int | None = Field(default=None, ge=1)
    ot_origin: Literal["unspecified", "own", "other"] = "unspecified"


class BankPatch(BaseModel):
    game: str | None = Field(default=None, min_length=1, max_length=100)
    pokemon: str | None = Field(default=None, min_length=1, max_length=100)
    form_name: str | None = Field(default=None, max_length=100)
    comments: str | None = Field(default=None, max_length=1000)
    shiny: bool | None = None
    ot_exception: bool | None = None
    required: int | None = Field(default=None, ge=1, le=999)
    caught: int | None = Field(default=None, ge=0, le=999)
    in_home: int | None = Field(default=None, ge=0, le=999)
    goal_id: int | None = Field(default=None, ge=1)
    save_id: int | None = Field(default=None, ge=1)
    ot_origin: Literal["unspecified", "own", "other"] | None = None


def _bank_task_values(db, values: dict):
    """Enforce consistency even when a linked task is edited later."""
    from .bank_links import _normalized, _form

    values = dict(values)
    values["game"] = values["game"].strip()
    values["pokemon"] = values["pokemon"].strip()
    values["form_name"] = (values["form_name"] or "").strip() or None
    values["comments"] = values["comments"].strip()
    # Saved profiles determine the game. Legacy Bank rows without a profile
    # retain their original game until explicitly assigned by the user.
    if values.get("save_id") is not None:
        saved = db.execute("SELECT game FROM game_saves WHERE id=?", (values["save_id"],)).fetchone()
        if not saved:
            raise HTTPException(422, "La partida seleccionada no existe")
        values["game"] = saved["game"]
    if not values["game"] or not values["pokemon"]:
        raise HTTPException(422, "Juego y Pokémon son obligatorios")
    if not (0 <= values["in_home"] <= values["caught"] <= values["required"]):
        raise HTTPException(422, "Debe cumplirse: en HOME ≤ capturados ≤ requeridos")
    values["shiny"] = int(values["shiny"])
    # Old clients/backup imports may still supply NOT as a boolean.
    # The explicit origin takes precedence; unspecified stays truly unknown.
    values["ot_exception"] = int(values["ot_origin"] == "other")
    if values["goal_id"] is not None:
        goal = db.execute(
            "SELECT g.shiny,f.species,f.form_name FROM goals g "
            "JOIN pokemon_forms f ON f.form_key=g.form_key WHERE g.id=?",
            (values["goal_id"],)).fetchone()
        if goal is None:
            raise HTTPException(422, "El objetivo de la Pokédex no existe")
        if goal["shiny"] != values["shiny"] or _normalized(goal["species"]) != _normalized(values["pokemon"]):
            raise HTTPException(422, "El vínculo debe ser de la misma especie y del mismo tipo shiny")
        if values["form_name"] and _form(goal["form_name"]) != _form(values["form_name"]):
            raise HTTPException(422, "La forma indicada no coincide con el objetivo vinculado")
    return values


@app.post("/api/bank", status_code=201)
def create_bank_task(data: BankTaskCreate):
    with connect() as db:
        input_values = data.model_dump()
        if input_values["ot_origin"] == "unspecified" and input_values["ot_exception"]:
            input_values["ot_origin"] = "other"  # Legacy POST payload.
        values = _bank_task_values(db, input_values)
        if values["save_id"] is not None:
            enabled = db.execute(
                "SELECT g.available FROM game_saves s JOIN games g ON g.name=s.game WHERE s.id=?",
                (values["save_id"],)).fetchone()
            if not enabled or not enabled["available"]:
                raise HTTPException(422, "Elegí una partida de un juego disponible")
        db.execute("INSERT OR IGNORE INTO bank_game_status(game) VALUES (?)", (values["game"],))
        columns = list(values)
        cur = db.execute(
            "INSERT INTO bank_tasks(" + ",".join(columns) + ") VALUES (" +
            ",".join("?" for _ in columns) + ")",
            [values[col] for col in columns])
        _update_bank_credit(db, cur.lastrowid)
        return dict(db.execute("SELECT * FROM bank_tasks WHERE id=?", (cur.lastrowid,)).fetchone())


@app.patch("/api/bank/{task_id}")
def update_bank(task_id: int, patch: BankPatch):
    provided = patch.model_dump(exclude_unset=True)
    with connect() as db:
        current = db.execute("SELECT * FROM bank_tasks WHERE id=?", (task_id,)).fetchone()
        if not current:
            raise HTTPException(404, "Tarea no encontrada")
        if not provided:
            return dict(current)
        if any(v is None for key, v in provided.items() if key not in {"goal_id", "form_name", "save_id"}):
            raise HTTPException(422, "Valor nulo no permitido")
        fields = ("game", "pokemon", "form_name", "comments", "shiny", "ot_exception",
                  "required", "caught", "in_home", "goal_id", "save_id", "ot_origin")
        combined = {key: provided.get(key, current[key]) for key in fields}
        if "ot_exception" in provided and "ot_origin" not in provided:
            combined["ot_origin"] = "other" if provided["ot_exception"] else "unspecified"
        normalized = _bank_task_values(db, combined)
        if normalized["game"] != current["game"] and current["source_row"] is not None:
            # The old import row is not valid provenance for a different game.
            db.execute("UPDATE bank_tasks SET source_row=NULL WHERE id=?", (task_id,))
        db.execute("INSERT OR IGNORE INTO bank_game_status(game) VALUES (?)", (normalized["game"],))
        db.execute("UPDATE bank_tasks SET " +
                   ", ".join(f"{field}=?" for field in fields) + " WHERE id=?",
                   [normalized[key] for key in fields] + [task_id])
        _update_bank_credit(db, task_id, current["goal_id"])
        return dict(db.execute("SELECT * FROM bank_tasks WHERE id=?", (task_id,)).fetchone())


@app.delete("/api/bank/{task_id}", status_code=204)
def delete_bank_task(task_id: int):
    with connect() as db:
        task = db.execute("SELECT goal_id FROM bank_tasks WHERE id=?", (task_id,)).fetchone()
        if not task:
            raise HTTPException(404, "Tarea no encontrada")
        db.execute("DELETE FROM bank_tasks WHERE id=?", (task_id,))
        if task["goal_id"] is not None:
            _recalculate_goal_home(db, task["goal_id"])
    return Response(status_code=204)


class BankGamePatch(BaseModel):
    started: bool | None = None
    prepared: bool | None = None


@app.patch("/api/bank-games/{name}")
def update_bank_game(name: str, patch: BankGamePatch):
    provided = patch.model_dump(exclude_unset=True)
    if any(v is None for v in provided.values()): raise HTTPException(422, "Valor nulo no permitido")
    with connect() as db:
        if not db.execute("SELECT 1 FROM bank_game_status WHERE game=?", (name,)).fetchone():
            raise HTTPException(404, "Juego no encontrado")
        if provided:
            db.execute("UPDATE bank_game_status SET " + ", ".join(f"{col}=?" for col in provided) + " WHERE game=?",
                       [*[int(v) for v in provided.values()], name])
        return dict(db.execute("SELECT * FROM bank_game_status WHERE game=?", (name,)).fetchone())


@app.get("/api/hunts")
def list_hunts():
    with connect() as db:
        hunts = rows(db.execute("""SELECT h.*,(SELECT COUNT(*) FROM hunt_phases p WHERE p.hunt_id=h.id) AS recorded_phases
                   FROM hunts h ORDER BY CASE h.status WHEN 'active' THEN 0 WHEN 'paused' THEN 1 ELSE 2 END,h.id DESC"""))
    for h in hunts:
        h["recorded_phases"] += h["unknown_phases"]
        h["cumulative"] = cumulative_probability(h["probability"], h["attempts"])
    return hunts


class HuntNew(BaseModel):
    pokemon: str = Field(min_length=1, max_length=100)
    game: str = Field(default="", max_length=100)
    method: str = Field(default="", max_length=100)
    probability: float = Field(gt=0, le=1)
    seconds_per_attempt: float | None = Field(default=None, gt=0)


@app.post("/api/hunts", status_code=201)
def create_hunt(data: HuntNew):
    with connect() as db:
        cur = db.execute("""INSERT INTO hunts(pokemon,game,method,probability,seconds_per_attempt,status)
              VALUES(?,?,?,?,?,'active')""", (data.pokemon.strip(), data.game.strip(), data.method.strip(),
                                             data.probability, data.seconds_per_attempt))
        return dict(db.execute("SELECT * FROM hunts WHERE id=?", (cur.lastrowid,)).fetchone())


class HuntPatch(BaseModel):
    delta: int | None = Field(default=None, ge=-100000, le=100000)
    attempts: int | None = Field(default=None, ge=0)
    probability: float | None = Field(default=None, gt=0, le=1)
    seconds_per_attempt: float | None = Field(default=None, gt=0)
    status: Literal["active", "paused", "completed"] | None = None
    shiny_found: bool | None = None


@app.patch("/api/hunts/{hunt_id}")
def update_hunt(hunt_id: int, patch: HuntPatch):
    provided = patch.model_dump(exclude_unset=True)
    with connect() as db:
        old = db.execute("SELECT * FROM hunts WHERE id=?", (hunt_id,)).fetchone()
        if not old: raise HTTPException(404, "Cacería no encontrada")
        if any(v is None for v in provided.values()): raise HTTPException(422, "Valor nulo no permitido")
        delta = provided.pop("delta", 0)
        if "attempts" in provided and delta:
            raise HTTPException(422, "Elegí delta o attempts, no ambos")
        if delta: provided["attempts"] = old["attempts"] + delta
        if provided.get("attempts", old["attempts"]) < 0:
            raise HTTPException(422, "Los intentos no pueden ser negativos")
        if "shiny_found" in provided: provided["shiny_found"] = int(provided["shiny_found"])
        if provided:
            db.execute("UPDATE hunts SET " + ", ".join(f"{col}=?" for col in provided) + " WHERE id=?",
                       [*provided.values(), hunt_id])
        updated = dict(db.execute("SELECT * FROM hunts WHERE id=?", (hunt_id,)).fetchone())
    updated["cumulative"] = cumulative_probability(updated["probability"], updated["attempts"])
    return updated


class PhaseNew(BaseModel):
    at_attempt: int = Field(ge=0)
    note: str = Field(default="", max_length=200)


@app.post("/api/hunts/{hunt_id}/phases", status_code=201)
def add_phase(hunt_id: int, phase: PhaseNew):
    with connect() as db:
        hunt = db.execute("SELECT attempts FROM hunts WHERE id=?", (hunt_id,)).fetchone()
        if not hunt: raise HTTPException(404, "Cacería no encontrada")
        if phase.at_attempt > hunt["attempts"]:
            raise HTTPException(422, "La fase no puede estar en el futuro")
        cur = db.execute("INSERT INTO hunt_phases(hunt_id,at_attempt,note) VALUES(?,?,?)",
                         (hunt_id, phase.at_attempt, phase.note))
        return {"id": cur.lastrowid, **phase.model_dump()}


@app.get("/api/hunts/{hunt_id}/phases")
def list_phases(hunt_id: int):
    with connect() as db:
        return rows(db.execute("SELECT * FROM hunt_phases WHERE hunt_id=? ORDER BY at_attempt", (hunt_id,)))


# Catalog order is grouped by generation (I–IX), not alphabetically.
GAME_ORDER = {game: position for position, game in enumerate(GAMES)}


@app.get("/api/games")
def list_games():
    with connect() as db:
        games = rows(db.execute("SELECT * FROM games ORDER BY name"))
    return sorted(games, key=lambda item: (GAME_ORDER.get(item["name"], len(GAMES)), item["name"]))


class GamePatch(BaseModel):
    available: bool | None = None
    shiny_charm: bool | None = None


@app.patch("/api/games/{name}")
def update_game(name: str, patch: GamePatch):
    values = patch.model_dump(exclude_unset=True)
    if any(v is None for v in values.values()): raise HTTPException(422, "Valor nulo no permitido")
    with connect() as db:
        if not db.execute("SELECT 1 FROM games WHERE name=?", (name,)).fetchone():
            raise HTTPException(404, "Juego no encontrado")
        if values:
            db.execute("UPDATE games SET " + ", ".join(f"{k}=?" for k in values) + " WHERE name=?",
                       [*[int(v) for v in values.values()], name])
        return dict(db.execute("SELECT * FROM games WHERE name=?", (name,)).fetchone())



@app.get("/api/game-saves")
def list_game_saves(available_only: bool = False):
    with connect() as db:
        query = """SELECT sv.id,sv.game,sv.name,sv.shiny_charm,
                    g.available AS game_available
                    FROM game_saves sv JOIN games g ON g.name=sv.game"""
        if available_only:
            query += " WHERE g.available=1"
        saves = rows(db.execute(query))
    return {"items": sorted(saves, key=lambda item: (
        GAME_ORDER.get(item["game"], len(GAMES)), item["game"],
        item["name"].casefold(), item["id"]))}


class GameSaveNew(BaseModel):
    game: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=80)
    shiny_charm: bool = False


class GameSavePatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    shiny_charm: bool | None = None


@app.post("/api/game-saves", status_code=201)
def create_game_save(data: GameSaveNew):
    name = data.name.strip()
    if not name:
        raise HTTPException(422, "La partida necesita un nombre")
    with connect() as db:
        game = db.execute("SELECT available FROM games WHERE name=?", (data.game,)).fetchone()
        if not game:
            raise HTTPException(422, "Juego fuera del catálogo")
        if not game["available"]:
            raise HTTPException(422, "Primero marcá el juego como disponible")
        try:
            cur = db.execute(
                "INSERT INTO game_saves(game,name,shiny_charm) VALUES(?,?,?)",
                (data.game, name, int(data.shiny_charm)))
        except sqlite3.IntegrityError as exc:
            raise HTTPException(409, "Ya existe una partida con ese nombre para el juego") from exc
        return dict(db.execute("SELECT * FROM game_saves WHERE id=?", (cur.lastrowid,)).fetchone())


@app.patch("/api/game-saves/{save_id}")
def update_game_save(save_id: int, patch: GameSavePatch):
    values = patch.model_dump(exclude_unset=True)
    if any(value is None for value in values.values()):
        raise HTTPException(422, "Usá un valor no nulo")
    if "name" in values:
        values["name"] = values["name"].strip()
        if not values["name"]:
            raise HTTPException(422, "La partida necesita un nombre")
    if "shiny_charm" in values:
        values["shiny_charm"] = int(values["shiny_charm"])
    with connect() as db:
        if not db.execute("SELECT 1 FROM game_saves WHERE id=?", (save_id,)).fetchone():
            raise HTTPException(404, "Partida no encontrada")
        if values:
            try:
                db.execute("UPDATE game_saves SET " +
                           ", ".join(f"{col}=?" for col in values) + " WHERE id=?",
                           [*values.values(), save_id])
            except sqlite3.IntegrityError as exc:
                raise HTTPException(409, "Ya existe una partida con ese nombre") from exc
        return dict(db.execute("SELECT * FROM game_saves WHERE id=?", (save_id,)).fetchone())


@app.delete("/api/game-saves/{save_id}", status_code=204)
def delete_game_save(save_id: int):
    with connect() as db:
        if not db.execute("SELECT 1 FROM game_saves WHERE id=?", (save_id,)).fetchone():
            raise HTTPException(404, "Partida no encontrada")
        linked = db.execute("SELECT COUNT(*) FROM bank_tasks WHERE save_id=?", (save_id,)).fetchone()[0]
        if linked:
            raise HTTPException(409, "Esta partida tiene tareas de Bank; reasignalas antes de eliminarla")
        db.execute("DELETE FROM game_saves WHERE id=?", (save_id,))
    return Response(status_code=204)


@app.get("/api/backup")
def export_backup():
    tables = ("goals", "bank_tasks", "bank_game_status", "hunts", "hunt_phases", "games", "game_saves", "import_history")
    with connect() as db:
        result = {name: rows(db.execute(f"SELECT * FROM {name}")) for name in tables}
    return JSONResponse({"format": "optpoke-backup", "version": 1, "data": result},
                        headers={"Content-Disposition": 'attachment; filename="optpoke-backup.json"'})


class BackupIn(BaseModel):
    format: Literal["optpoke-backup"]
    version: Literal[1]
    data: dict[str, list[dict]]


@app.post("/api/backup")
def restore_backup(payload: BackupIn):
    # Restore only trusted app-format backups; this replaces user progress.
    writable = {
        "goals": {"id", "form_key", "shiny", "target", "in_home", "obtainability", "ot_exception", "pending_evolution", "manual_home", "own_ot_obtainability"},
        "bank_tasks": {"id", "game", "pokemon", "form_name", "comments", "shiny", "ot_exception", "required", "caught", "in_home", "source_row", "goal_id", "save_id", "ot_origin", "synced_home"},
        "bank_game_status": {"game", "started", "prepared"},
        "hunts": {"id", "pokemon", "game", "method", "probability", "seconds_per_attempt", "attempts", "status", "shiny_found", "unknown_phases", "source", "created_at"},
        "hunt_phases": {"id", "hunt_id", "at_attempt", "note"},
        "games": {"name", "available", "shiny_charm"},
        "game_saves": {"id", "game", "name", "shiny_charm"},
        "import_history": {"digest", "kind", "imported_at"},
    }
    # Restore older v1 backups without profile rows or save_id, keeping legacy
    # Bank tasks associated with a game but without inventing a save.
    payload.data.setdefault("game_saves", [])
    if set(payload.data) != set(writable):
        raise HTTPException(422, "El respaldo no tiene todas las tablas esperadas")
    for tab, items in payload.data.items():
        for item in items:
            keys = set(item)
            # Additive fields are optional in older version-1 backups.
            if tab == "goals":
                for field in ("ot_exception", "pending_evolution"):
                    item.setdefault(field, 0)
                item.setdefault("own_ot_obtainability", "unverified")
                item.setdefault("manual_home", item["in_home"])
            if tab == "bank_tasks":
                item.setdefault("goal_id", None)
                item.setdefault("save_id", None)
                item.setdefault("ot_origin", "other" if item.get("ot_exception") else "unspecified")
                item.setdefault("synced_home", 0)
            if set(item) != writable[tab]:
                raise HTTPException(422, f"Campos inválidos en {tab}")
    try:
        with connect() as db:
            for table in ("hunt_phases", "hunts", "bank_tasks", "game_saves", "bank_game_status", "goals", "games", "import_history"):
                db.execute(f"DELETE FROM {table}")
            for tab in ("goals", "games", "game_saves", "bank_game_status", "bank_tasks", "hunts", "hunt_phases", "import_history"):
                items = payload.data[tab]
                if items:
                    columns = list(items[0])
                    db.executemany(f"INSERT INTO {tab}({','.join(columns)}) VALUES ({','.join('?' for _ in columns)})",
                                   [[item[col] for col in columns] for item in items])
            # Older backups predate the curated lock catalog. Seed them once without
            # resetting explicit user choices (obtainable / locked).
            seed_locked_shinies(db)
    except sqlite3.IntegrityError as exc:
        raise HTTPException(422, f"Respaldo inconsistente: {exc}") from exc
    return {"restored": True}

