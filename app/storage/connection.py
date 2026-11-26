"""Open the local SQLite database and delimit one unit of work."""
from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

ROOT = Path(__file__).resolve().parents[2]


def database_path() -> Path:
    """Create the selected private data directory and return its database path."""
    directory = Path(os.environ.get("OPTPOKE_DATA_DIR", str(Path.home() / ".optpoke")))
    directory.mkdir(parents=True, exist_ok=True)
    return directory / "optpoke.db"


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    """Yield a row-based connection; commit on success and roll back on error.

    Each caller owns this transaction. Foreign keys and a 15-second busy timeout
    apply to the connection; it is always closed after the context exits.
    """
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
