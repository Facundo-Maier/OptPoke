"""Idempotent migration of the user's original Bank and ShinyHunts logs."""
from __future__ import annotations

import hashlib
from pathlib import Path

from .db import connect
from .xlsx import read_sheets


def _digest(path: Path, kind: str) -> str:
    return hashlib.sha256(kind.encode() + b"\0" + path.read_bytes()).hexdigest()


def _int(s: str, default=0) -> int:
    try:
        return int(float(s))
    except (TypeError, ValueError):
        return default


def import_bank(path: str | Path) -> dict:
    path = Path(path)
    rows = read_sheets(path, {"Juegos"})["Juegos"]
    tasks = []
    games = {}
    for i, row in enumerate(rows[1:], start=2):
        game = row.get("G", "")
        if game:
            games[game] = (int(row.get("H", "").lower() in ("si", "sí")),
                           int(row.get("I", "").lower() in ("si", "sí")))
        if not row.get("B", "") or not row.get("A", "") or _int(row.get("E", "")) <= 0:
            continue
        comments = row.get("D", "")
        flags = {x.strip().upper() for x in comments.split(";")}
        tasks.append((row["A"], row["B"], row.get("C", ""), comments,
                      int("NS" not in flags), int("NOT" in flags), _int(row["E"]), i))
    digest = _digest(path, "bank")
    with connect() as db:
        if db.execute("SELECT 1 FROM import_history WHERE digest=?", (digest,)).fetchone():
            return {"imported": False, "tasks": 0, "reason": "Archivo ya importado"}
        db.executemany("INSERT OR IGNORE INTO bank_game_status(game,started,prepared) VALUES (?,?,?)",
                       [(g, *status) for g, status in games.items()])
        db.executemany("INSERT OR IGNORE INTO bank_game_status(game) VALUES (?)",
                       [(t[0],) for t in tasks])
        db.executemany("""INSERT OR IGNORE INTO bank_tasks
            (game,pokemon,form_name,comments,shiny,ot_exception,required,source_row)
            VALUES(?,?,?,?,?,?,?,?)""", tasks)
        db.execute("INSERT INTO import_history(digest,kind) VALUES (?,?)", (digest, "bank"))
    return {"imported": True, "tasks": len(tasks), "games": len(games)}


def import_hunts(path: str | Path) -> dict:
    path = Path(path)
    data = read_sheets(path, {"Resets", "DynaAdv."})
    entries = []
    for row in data["Resets"][1:]:
        if not row.get("B", ""): continue
        probability = float(row.get("C") or 0)
        entries.append((row["B"], "Resets", probability, _int(row.get("D")),
                        "paused", 0, [], 0))
    for row in data["DynaAdv."][1:]:
        if not row.get("B", ""): continue
        found = bool(_int(row.get("G", "")))
        # Rate is based on the workbook's accumulated P = 1-(1-p)^n.
        checks = _int(row.get("C", ""))
        accumulated = float(row.get("D") or 0)
        probability = 1 - (1 - accumulated)**(1 / checks) if checks and 0 < accumulated < 1 else .01
        phases = [_int(v) for v in row.get("F", "").split(",") if v.strip().isdigit()]
        entries.append((row["B"], "Dynamax Adventures", probability,
                        checks, "completed" if found else "paused", int(found), phases,
                        max(0, _int(row.get("E", "")) - len(phases))))
    digest = _digest(path, "hunts")
    with connect() as db:
        if db.execute("SELECT 1 FROM import_history WHERE digest=?", (digest,)).fetchone():
            return {"imported": False, "hunts": 0, "reason": "Archivo ya importado"}
        for name, method, probability, count, status, found, phases, unknown in entries:
            cur = db.execute("""INSERT INTO hunts
                (pokemon,method,probability,attempts,status,shiny_found,unknown_phases,source)
                VALUES (?,?,?,?,?,?,?,?)""", (name, method, probability, count, status, found, unknown, "excel"))
            db.executemany("INSERT INTO hunt_phases(hunt_id,at_attempt) VALUES (?,?)",
                           [(cur.lastrowid, phase) for phase in phases])
        db.execute("INSERT INTO import_history(digest,kind) VALUES (?,?)", (digest, "hunts"))
    return {"imported": True, "hunts": len(entries)}
