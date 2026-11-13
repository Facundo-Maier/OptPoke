"""SQLite storage and additive catalog seed (never overwrite personal progress)."""
from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data" / "catalog.json"
LOCKED_SHINIES = ROOT / "data" / "shiny_locks.json"


def database_path() -> Path:
    directory = Path(os.environ.get("OPTPOKE_DATA_DIR", str(Path.home() / ".optpoke")))
    directory.mkdir(parents=True, exist_ok=True)
    return directory / "optpoke.db"


@contextmanager
def connect():
    db = sqlite3.connect(database_path(), timeout=15)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("PRAGMA busy_timeout=15000")
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


SCHEMA = """
CREATE TABLE IF NOT EXISTS pokemon_forms (
    form_key TEXT PRIMARY KEY,
    dex_number INTEGER NOT NULL CHECK (dex_number > 0),
    species TEXT NOT NULL,
    form_name TEXT,
    source_form TEXT,
    source_variant TEXT
);
CREATE TABLE IF NOT EXISTS goals (
    id INTEGER PRIMARY KEY,
    form_key TEXT NOT NULL REFERENCES pokemon_forms(form_key),
    shiny INTEGER NOT NULL CHECK (shiny IN (0,1)),
    target INTEGER NOT NULL DEFAULT 1 CHECK (target >= 1),
    in_home INTEGER NOT NULL DEFAULT 0 CHECK (in_home >= 0),
    obtainability TEXT NOT NULL DEFAULT 'unverified'
        CHECK (obtainability IN ('unverified','obtainable','locked')),
    ot_exception INTEGER NOT NULL DEFAULT 0 CHECK (ot_exception IN (0,1)),
    UNIQUE(form_key, shiny)
);
CREATE TABLE IF NOT EXISTS bank_game_status (
    game TEXT PRIMARY KEY,
    started INTEGER NOT NULL DEFAULT 0,
    prepared INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS bank_tasks (
    id INTEGER PRIMARY KEY,
    game TEXT NOT NULL REFERENCES bank_game_status(game),
    pokemon TEXT NOT NULL,
    form_name TEXT,
    comments TEXT NOT NULL DEFAULT '',
    shiny INTEGER NOT NULL DEFAULT 1 CHECK (shiny IN (0,1)),
    ot_exception INTEGER NOT NULL DEFAULT 0 CHECK (ot_exception IN (0,1)),
    required INTEGER NOT NULL CHECK (required > 0),
    caught INTEGER NOT NULL DEFAULT 0 CHECK (caught >= 0),
    in_home INTEGER NOT NULL DEFAULT 0 CHECK (in_home >= 0),
    source_row INTEGER,
    UNIQUE(game, source_row)
);
CREATE TABLE IF NOT EXISTS hunts (
    id INTEGER PRIMARY KEY,
    pokemon TEXT NOT NULL,
    game TEXT NOT NULL DEFAULT '',
    method TEXT NOT NULL DEFAULT '',
    probability REAL NOT NULL CHECK (probability >= 0 AND probability <= 1),
    seconds_per_attempt REAL CHECK (seconds_per_attempt IS NULL OR seconds_per_attempt > 0),
    attempts INTEGER NOT NULL DEFAULT 0 CHECK (attempts >= 0),
    status TEXT NOT NULL DEFAULT 'paused'
        CHECK (status IN ('active','paused','completed')),
    shiny_found INTEGER NOT NULL DEFAULT 0 CHECK (shiny_found IN (0,1)),
    unknown_phases INTEGER NOT NULL DEFAULT 0 CHECK (unknown_phases >= 0),
    source TEXT NOT NULL DEFAULT 'manual',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS hunt_phases (
    id INTEGER PRIMARY KEY,
    hunt_id INTEGER NOT NULL REFERENCES hunts(id) ON DELETE CASCADE,
    at_attempt INTEGER NOT NULL CHECK (at_attempt >= 0),
    note TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS games (
    name TEXT PRIMARY KEY,
    available INTEGER NOT NULL DEFAULT 1 CHECK (available IN (0,1)),
    shiny_charm INTEGER NOT NULL DEFAULT 0 CHECK (shiny_charm IN (0,1))
);
CREATE TABLE IF NOT EXISTS import_history (
    digest TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_forms_dex ON pokemon_forms(dex_number);
CREATE INDEX IF NOT EXISTS idx_goals_type ON goals(shiny, obtainability);
CREATE INDEX IF NOT EXISTS idx_bank_game ON bank_tasks(game);
"""

GAMES = [
    "Red", "Blue", "Yellow", "Gold", "Silver", "Crystal",
    "Ruby", "Sapphire", "Emerald", "FireRed", "LeafGreen",
    "Colosseum", "XD: Gale of Darkness", "Diamond", "Pearl", "Platinum",
    "HeartGold", "SoulSilver", "Black", "White", "Black 2", "White 2",
    "X", "Y", "Omega Ruby", "Alpha Sapphire", "Sun", "Moon",
    "Ultra Sun", "Ultra Moon", "Let's Go Pikachu", "Let's Go Eevee",
    "Sword", "Shield", "Brilliant Diamond", "Shining Pearl",
    "Legends: Arceus", "Scarlet", "Violet", "Legends: Z-A",
]



def seed_locked_shinies(db: sqlite3.Connection) -> int:
    """Add curated *global* shiny locks once per catalog revision.

    Existing user choices (obtainable or locked) are not overridden. A migration
    marker prevents a user changing a seeded lock back to unverified from
    having that choice reset the next time the application starts.
    """
    data = json.loads(LOCKED_SHINIES.read_text(encoding="utf-8"))
    marker = f"shiny-locks:{data['version']}"
    if db.execute("SELECT 1 FROM import_history WHERE digest=?", (marker,)).fetchone():
        return 0
    keys = data["locked_shiny_keys"]
    if len(keys) != len(set(keys)) or not keys:
        raise ValueError("El catálogo de shiny locks contiene entradas duplicadas o está vacío")
    changed = 0
    for key in keys:
        # Only the shiny goal is affected. Never mark normal Pokémon as locked.
        result = db.execute(
            "UPDATE goals SET obtainability='locked' "
            "WHERE form_key=? AND shiny=1 AND obtainability='unverified'",
            (key,),
        )
        changed += result.rowcount
    db.execute(
        "INSERT INTO import_history(digest,kind) VALUES(?,?)",
        (marker, "catalog-default-shiny-locks"),
    )
    return changed


def migrate_goals_ot(db: sqlite3.Connection) -> None:
    """Add a manual, independent OT marker to databases created before v0.1.6."""
    fields = {row["name"] for row in db.execute("PRAGMA table_info(goals)")}
    if "ot_exception" not in fields:
        db.execute(
            "ALTER TABLE goals ADD COLUMN ot_exception INTEGER NOT NULL DEFAULT 0 "
            "CHECK (ot_exception IN (0,1))"
        )


def initialize() -> None:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    with connect() as db:
        db.executescript(SCHEMA)
        migrate_goals_ot(db)
        db.executemany(
            """INSERT OR IGNORE INTO pokemon_forms
               (form_key, dex_number, species, form_name, source_form, source_variant)
               VALUES (:key, :dex_number, :species, :form_name, :source_form, :source_variant)""",
            catalog["forms"],
        )
        db.executemany(
            "INSERT OR IGNORE INTO goals(form_key, shiny) VALUES (?, ?)",
            [(key, 1) for key in catalog["shiny_keys"]] +
            [(key, 0) for key in catalog["normal_keys"]],
        )
        db.executemany("INSERT OR IGNORE INTO games(name) VALUES (?)", [(g,) for g in GAMES])
        seed_locked_shinies(db)
