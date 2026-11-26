"""Schema for a fresh Opt. Poke SQLite database."""

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
    manual_home INTEGER NOT NULL DEFAULT 0 CHECK (manual_home >= 0),
    own_ot_obtainability TEXT NOT NULL DEFAULT 'unverified'
        CHECK (own_ot_obtainability IN ('unverified','obtainable','unobtainable')),
    obtainability TEXT NOT NULL DEFAULT 'unverified'
        CHECK (obtainability IN ('unverified','obtainable','locked')),
    ot_exception INTEGER NOT NULL DEFAULT 0 CHECK (ot_exception IN (0,1)),
    pending_evolution INTEGER NOT NULL DEFAULT 0 CHECK (pending_evolution IN (0,1)),
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
    goal_id INTEGER REFERENCES goals(id) ON DELETE SET NULL,
    save_id INTEGER REFERENCES game_saves(id) ON DELETE RESTRICT,
    ot_origin TEXT NOT NULL DEFAULT 'unspecified'
        CHECK (ot_origin IN ('unspecified','own','other')),
    synced_home INTEGER NOT NULL DEFAULT 0 CHECK (synced_home >= 0),
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
    available INTEGER NOT NULL DEFAULT 0 CHECK (available IN (0,1)),
    shiny_charm INTEGER NOT NULL DEFAULT 0 CHECK (shiny_charm IN (0,1))
);
CREATE TABLE IF NOT EXISTS game_saves (
    id INTEGER PRIMARY KEY,
    game TEXT NOT NULL REFERENCES games(name),
    name TEXT NOT NULL COLLATE NOCASE CHECK (length(trim(name)) BETWEEN 1 AND 80),
    shiny_charm INTEGER NOT NULL DEFAULT 0 CHECK (shiny_charm IN (0,1)),
    UNIQUE(game,name)
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
