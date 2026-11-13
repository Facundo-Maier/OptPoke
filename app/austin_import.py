"""Import AustinJohn's *personal copy* of the two LITE trackers safely.

Sheet J: 0 = obtained, 1 = pending, NOT = 'No OT' (OT exception).
NOT says nothing about ownership. Never infer in_home from NOT.

A preview is computed without writing data. Apply requires a matching SHA-256
of the uploaded bytes, then changes goals only in one SQLite transaction.
"""
from __future__ import annotations

from collections import Counter
import hashlib
from io import BytesIO
import re

from .db import connect
from .xlsx import read_sheets, list_sheet_names

# Austin now distributes Shiny and Living as *separate workbooks*.
# We also accept older copies where both sheets are in one workbook.
SHEETS = (("S-LivingFormLITE", 1), ("LivingFormLITE", 0))
SHEET_NAMES = {sheet for sheet, _ in SHEETS}


def _normalize(text: str | None) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip()).casefold()


def _status(value: str | None) -> str | None:
    value = str(value or "").strip().upper()
    if value == "NOT":
        return "NOT"
    if value in {"0", "0.0"}:
        return "0"
    if value in {"1", "1.0"}:
        return "1"
    return None


def _lookup_key(row: dict[str, str], forms: dict[str, dict]) -> str | None:
    """Use a stable source keyword; disambiguate Hoopa's duplicated shiny key.

    Never match by position/row number, because Austin's sheet is updated.
    """
    keyword = row.get("V", "").strip()
    species = _normalize(row.get("H"))
    form_name = _normalize(row.get("L"))
    possibilities = [keyword]
    if keyword == "hoopa" and form_name == "unbound":
        possibilities = ["hoopa-1"]
    # Some versions of Austin's template permute form-key suffixes (notably
    # Pumpkaboo Large/Super). Trust species + full form name over the suffix.
    try:
        dex = int(float(row["I"]))
    except (ValueError, KeyError):
        dex = None
    preferred = possibilities + [key for key, form in forms.items()
                             if _normalize(form["species"]) == species
                             and _normalize(form["form_name"]) == form_name
                             and (dex is None or form["dex_number"] == dex)]
    for key in dict.fromkeys(preferred):
        form = forms.get(key)
        if not form or _normalize(form["species"]) != species:
            continue
        if dex and form["dex_number"] != dex:
            continue
        if _normalize(form["form_name"]) != form_name:
            continue
        return key
    return None


def build_austin_plan(content: bytes, mode: str = "merge", source: str | None = None) -> dict:
    if mode not in {"merge", "replace"}:
        raise ValueError("Modo de importación desconocido")
    if source not in {None, "shiny", "normal"}:
        raise ValueError("Tipo de colección desconocido")
    if not content or len(content) > 12_000_000:
        raise ValueError("El Excel debe pesar como máximo 12 MB")
    digest = hashlib.sha256(content).hexdigest()
    try:
        available = list_sheet_names(BytesIO(content))
        wanted = SHEET_NAMES.intersection(available)
        if source is not None:
            required = "S-LivingFormLITE" if source == "shiny" else "LivingFormLITE"
            if required not in wanted:
                raise ValueError(f"Este archivo no contiene {required}. Seleccioná el Excel correcto de AustinJohn.")
            wanted = {required}
        if not wanted:
            raise ValueError("No se encontró LivingFormLITE ni S-LivingFormLITE en este Excel")
        sheets = read_sheets(BytesIO(content), wanted)
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError("No se pudo leer el Excel de AustinJohn; verificá que sea un .xlsx válido") from exc
    with connect() as db:
        forms = {row["form_key"]: dict(row) for row in db.execute("SELECT * FROM pokemon_forms")}
        goals = {(row["form_key"], row["shiny"]): dict(row) for row in db.execute("SELECT * FROM goals")}
    actions = []
    problems = []
    stats = Counter()
    seen = set()
    for sheet, shiny in SHEETS:
        if sheet not in sheets:
            continue
        for row in sheets[sheet]:
            # Heading rows do not have Pokémon reference keywords in the catalog.
            if row.get("H") == "Name" or not row.get("V") or not row.get("J"):
                continue
            if row.get("V", "").casefold() == "gen" and row.get("H", "").casefold() == "gen":
                continue  # generation separators are not Pokémon
            status = _status(row["J"])
            if status is None:
                if row["J"].strip().upper() == "EVO":
                    stats["evo_unresolved"] += 1
                    problems.append(f"{sheet}: EVO sin interpretar, no se modifica: {row.get('H', '?')} / {row.get('L') or 'Forma base'}")
                else:
                    stats["other_status"] += 1
                    problems.append(f"{sheet}: valor de estado desconocido para {row.get('H', '?')}: {row['J'][:25]}")
                continue
            key = _lookup_key(row, forms)
            if not key or (key, shiny) not in goals:
                stats["unmatched"] += 1
                problems.append(f"{sheet}: sin coincidencia segura: {row.get('H', '?')} / {row.get('L') or 'Base'} ({row.get('V')})")
                continue
            identity = (key, shiny)
            if identity in seen:
                stats["duplicates"] += 1
                problems.append(f"{sheet}: entrada duplicada: {row.get('H')} / {row.get('L') or 'Base'}")
                continue
            seen.add(identity)
            goal = goals[identity]
            stats["matched"] += 1
            stats["shiny" if shiny else "normal"] += 1
            stats[{"0": "obtained", "1": "pending", "NOT": "not_ot"}[status]] += 1
            updates = {}
            if status == "0":
                if goal["in_home"] == 0:
                    # A checkbox 0 proves at least one Pokémon, not every
                    # extra copy the user may have added to their target.
                    updates["in_home"] = 1
            elif status == "1" and mode == "replace" and goal["in_home"] != 0:
                updates["in_home"] = 0
            elif status == "NOT" and not goal["ot_exception"]:
                # NOT is an OT exception, NOT a synonym for obtained or pending.
                updates["ot_exception"] = 1
            if updates:
                stats["changed"] += 1
                actions.append({"goal_id": goal["id"], "name": goal["species"] if "species" in goal else forms[key]["species"],
                                "form": forms[key]["form_name"] or "Forma base", "shiny": bool(shiny),
                                "source": status, "before_home": goal["in_home"],
                                "after_home": updates.get("in_home", goal["in_home"]),
                                "ot_exception": bool(updates.get("ot_exception", goal["ot_exception"])),
                                "updates": updates})
            else:
                stats["unchanged"] += 1
    if stats["matched"] < 100:
        raise ValueError("No se reconoció el catálogo de AustinJohn; se canceló la importación")
    return {"digest": digest, "mode": mode, "sheets": sorted(sheets),
            "counts": dict(stats), "changes": actions,
            "warnings": problems[:40], "warnings_total": len(problems)}


def apply_austin_plan(plan: dict) -> dict:
    # Only the exact changed fields are updated. Unlisted goals are untouched.
    with connect() as db:
        for change in plan["changes"]:
            values = change["updates"]
            db.execute("UPDATE goals SET " + ", ".join(f"{column}=?" for column in values)
                       + " WHERE id=?", [*values.values(), change["goal_id"]])
    return {"applied": len(plan["changes"]), "counts": plan["counts"], "warnings_total": plan["warnings_total"]}
