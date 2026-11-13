"""Upgrade a pre-0.1.6 SQLite file without touching personal progress."""
import sqlite3
from pathlib import Path
from app.db import connect, initialize


def test_legacy_goal_migration_preserves_data(local_data):
    db_file=Path(local_data)/"optpoke.db"
    with connect() as db:
        db.execute("UPDATE goals SET in_home=1 WHERE form_key='bulbasaur' AND shiny=1")
        db.execute("ALTER TABLE goals RENAME TO old_goals")
        db.execute("""CREATE TABLE goals (
            id INTEGER PRIMARY KEY, form_key TEXT NOT NULL REFERENCES pokemon_forms(form_key),
            shiny INTEGER NOT NULL, target INTEGER NOT NULL DEFAULT 1,
            in_home INTEGER NOT NULL DEFAULT 0,
            obtainability TEXT NOT NULL DEFAULT 'unverified', UNIQUE(form_key, shiny)
        )""")
        db.execute("INSERT INTO goals(id,form_key,shiny,target,in_home,obtainability) SELECT id,form_key,shiny,target,in_home,obtainability FROM old_goals")
        db.execute("DROP TABLE old_goals")
    initialize()
    with connect() as db:
        columns={row['name'] for row in db.execute("PRAGMA table_info(goals)")}
        assert 'ot_exception' in columns
        goal=db.execute("SELECT in_home,ot_exception FROM goals WHERE form_key='bulbasaur' AND shiny=1").fetchone()
        assert (goal['in_home'],goal['ot_exception'])==(1,0)
