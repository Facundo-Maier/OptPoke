"""Catalog and curated defaults added without overwriting user choices."""
from __future__ import annotations

import json
import sqlite3

from .connection import ROOT

CATALOG = ROOT / "data" / "catalog.json"
LOCKED_SHINIES = ROOT / "data" / "shiny_locks.json"

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
