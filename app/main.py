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

from .db import ROOT, connect, initialize, seed_locked_shinies
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
               status: Literal["all", "missing", "done", "locked", "ot_exception"] = "all",
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
        if "ot_exception" in provided: provided["ot_exception"] = int(provided["ot_exception"])
        db.execute("UPDATE goals SET " + ", ".join(f"{field}=?" for field in provided) + " WHERE id=?",
                   [*provided.values(), goal_id])
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


@app.get("/api/bank")
def list_bank(game: str = "", search: str = "", pending: bool = True):
    conditions = ["1=1"]
    params: list = []
    if game:
        conditions.append("t.game=?")
        params.append(game)
    if search:
        conditions.append("(t.pokemon LIKE ? OR t.form_name LIKE ? OR t.comments LIKE ?)")
        params.extend([f"%{search}%"] * 3)
    if pending: conditions.append("t.in_home<t.required")
    with connect() as db:
        items = rows(db.execute("""SELECT t.*,s.started,s.prepared
                  FROM bank_tasks t JOIN bank_game_status s USING(game)
                  WHERE """ + " AND ".join(conditions) + " ORDER BY t.game,t.source_row", params))
        statuses = rows(db.execute("SELECT * FROM bank_game_status ORDER BY game"))
    return {"items": items, "games": statuses}


class BankPatch(BaseModel):
    caught: int | None = Field(None, ge=0, le=999)
    in_home: int | None = Field(None, ge=0, le=999)


@app.patch("/api/bank/{task_id}")
def update_bank(task_id: int, patch: BankPatch):
    provided = patch.model_dump(exclude_unset=True)
    with connect() as db:
        current = db.execute("SELECT * FROM bank_tasks WHERE id=?", (task_id,)).fetchone()
        if not current: raise HTTPException(404, "Tarea no encontrada")
        if any(v is None for v in provided.values()): raise HTTPException(422, "Valor nulo no permitido")
        caught = provided.get("caught", current["caught"])
        in_home = provided.get("in_home", current["in_home"])
        if in_home > caught or caught > current["required"]:
            raise HTTPException(422, "Debe cumplirse: en HOME ≤ capturados ≤ requeridos")
        if provided:
            db.execute("UPDATE bank_tasks SET " + ", ".join(f"{col}=?" for col in provided) + " WHERE id=?",
                       [*provided.values(), task_id])
        return dict(db.execute("SELECT * FROM bank_tasks WHERE id=?", (task_id,)).fetchone())


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


@app.get("/api/games")
def list_games():
    with connect() as db:
        return rows(db.execute("SELECT * FROM games ORDER BY name"))


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


@app.get("/api/backup")
def export_backup():
    tables = ("goals", "bank_tasks", "bank_game_status", "hunts", "hunt_phases", "games", "import_history")
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
        "goals": {"id", "form_key", "shiny", "target", "in_home", "obtainability", "ot_exception"},
        "bank_tasks": {"id", "game", "pokemon", "form_name", "comments", "shiny", "ot_exception", "required", "caught", "in_home", "source_row"},
        "bank_game_status": {"game", "started", "prepared"},
        "hunts": {"id", "pokemon", "game", "method", "probability", "seconds_per_attempt", "attempts", "status", "shiny_found", "unknown_phases", "source", "created_at"},
        "hunt_phases": {"id", "hunt_id", "at_attempt", "note"},
        "games": {"name", "available", "shiny_charm"},
        "import_history": {"digest", "kind", "imported_at"},
    }
    if set(payload.data) != set(writable):
        raise HTTPException(422, "El respaldo no tiene todas las tablas esperadas")
    for tab, items in payload.data.items():
        for item in items:
            keys = set(item)
            # v0.1.5 and older exports do not contain the OT column.
            if tab == "goals" and keys == writable[tab] - {"ot_exception"}:
                item["ot_exception"] = 0
            elif keys != writable[tab]:
                raise HTTPException(422, f"Campos inválidos en {tab}")
    try:
        with connect() as db:
            for table in ("hunt_phases", "hunts", "bank_tasks", "bank_game_status", "goals", "games", "import_history"):
                db.execute(f"DELETE FROM {table}")
            for tab in ("goals", "bank_game_status", "bank_tasks", "hunts", "hunt_phases", "games", "import_history"):
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
