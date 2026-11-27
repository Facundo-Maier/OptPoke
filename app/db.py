"""Compatibility imports for code using the original SQLite module.

New code can import the focused modules in app.storage directly.
"""
from .storage.catalog_seed import CATALOG, GAMES, LOCKED_SHINIES, seed_locked_shinies
from .storage.connection import ROOT, connect, database_path
from .storage.migrations import initialize, migrate_goals_ot
from .storage.schema import SCHEMA
