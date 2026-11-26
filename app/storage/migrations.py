"""Initialize and upgrade existing local databases in historical order."""
from __future__ import annotations

import json
import sqlite3

from .catalog_seed import CATALOG, GAMES, seed_locked_shinies
from .connection import connect
from .schema import SCHEMA


def migrate_goals_ot(db: sqlite3.Connection) -> None:
    """Add a manual, independent OT marker to databases created before v0.1.6."""
    fields = {row["name"] for row in db.execute("PRAGMA table_info(goals)")}
    if "ot_exception" not in fields:
        db.execute(
            "ALTER TABLE goals ADD COLUMN ot_exception INTEGER NOT NULL DEFAULT 0 "
            "CHECK (ot_exception IN (0,1))"
        )


def initialize() -> None:
    """Create or upgrade the database and add missing catalog rows and defaults.

    Preserves personal progress and runs on every application startup. Existing
    Bank tasks are never credited retroactively; failures propagate to the
    caller through the connection context.
    """
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    with connect() as db:
        db.executescript(SCHEMA)
        migrate_goals_ot(db)
        fields = {row["name"] for row in db.execute("PRAGMA table_info(goals)")}
        if "pending_evolution" not in fields:
            db.execute("ALTER TABLE goals ADD COLUMN pending_evolution INTEGER NOT NULL DEFAULT 0 CHECK (pending_evolution IN (0,1))")
        if "own_ot_obtainability" not in fields:
            db.execute("ALTER TABLE goals ADD COLUMN own_ot_obtainability TEXT NOT NULL DEFAULT 'unverified' CHECK (own_ot_obtainability IN ('unverified','obtainable','unobtainable'))")
        if "manual_home" not in fields:
            # Existing Dex progress becomes the manual baseline; never infer Bank credits.
            db.execute("ALTER TABLE goals ADD COLUMN manual_home INTEGER NOT NULL DEFAULT 0 CHECK (manual_home >= 0)")
            db.execute("UPDATE goals SET manual_home=in_home")
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
        # Bank tasks imported before v0.2 remain independent (NULL goal_id).
        task_fields = {row["name"] for row in db.execute("PRAGMA table_info(bank_tasks)")}
        if "goal_id" not in task_fields:
            db.execute("ALTER TABLE bank_tasks ADD COLUMN goal_id INTEGER REFERENCES goals(id) ON DELETE SET NULL")
        db.execute("CREATE INDEX IF NOT EXISTS idx_bank_goal ON bank_tasks(goal_id)")
        if "save_id" not in task_fields:
            db.execute("ALTER TABLE bank_tasks ADD COLUMN save_id INTEGER REFERENCES game_saves(id) ON DELETE RESTRICT")
        if "ot_origin" not in task_fields:
            db.execute("ALTER TABLE bank_tasks ADD COLUMN ot_origin TEXT NOT NULL DEFAULT 'unspecified' CHECK (ot_origin IN ('unspecified','own','other'))")
            db.execute("UPDATE bank_tasks SET ot_origin='other' WHERE ot_exception=1")
        if "synced_home" not in task_fields:
            # Old tasks (even linked/completed ones) must not be counted retroactively.
            db.execute("ALTER TABLE bank_tasks ADD COLUMN synced_home INTEGER NOT NULL DEFAULT 0 CHECK (synced_home >= 0)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_bank_save ON bank_tasks(save_id)")
        db.executemany("INSERT OR IGNORE INTO games(name) VALUES (?)", [(g,) for g in GAMES])
        # The previous default marked every game available, even if the user
        # never changed that setting. Reset only this recognizable untouched
        # state, once; preserve all personalized choices and save profiles.
        marker = "games-unselected-by-default-v1"
        if not db.execute("SELECT 1 FROM import_history WHERE digest=?", (marker,)).fetchone():
            stats = db.execute(
                "SELECT COUNT(*) AS n, SUM(available) AS enabled, "
                "COALESCE(SUM(shiny_charm),0) AS charms FROM games"
            ).fetchone()
            save_count = db.execute("SELECT COUNT(*) FROM game_saves").fetchone()[0]
            if (stats["n"] == len(GAMES) and stats["enabled"] == stats["n"]
                    and stats["charms"] == 0 and save_count == 0):
                db.execute("UPDATE games SET available=0")
            db.execute("INSERT INTO import_history(digest,kind) VALUES(?,?)",
                       (marker, "games-defaults-migration"))
        seed_locked_shinies(db)
