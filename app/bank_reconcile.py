"""Previsualización conservadora de posibles vínculos Bank -> objetivo del catálogo.

Solo lectura: sugerir una coincidencia no significa que se trate del mismo
ejemplar, que deba contabilizarse en HOME ni que la tarea esté confirmada.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import unicodedata

from .db import connect


def _normalized(value: str | None) -> str:
    """Comparar textos sin depender de mayúsculas, acentos o espacios extra."""
    text = unicodedata.normalize("NFKD", str(value or "").strip().casefold())
    return " ".join("".join(ch for ch in text if not unicodedata.combining(ch)).split())


def _form(value: str | None) -> str:
    normalized = _normalized(value)
    return "" if normalized in {"", "base", "forma base", "normal"} else normalized


def build_bank_reconciliation_preview() -> dict:
    """Listar candidatas seguras sin guardar relaciones ni cambiar contadores.

    - Una especie con una sola forma en esa colección admite propuesta.
    - Con varias formas, se exige que Bank indique una forma exacta.
    - Nunca se equipara un Pokémon shiny con un objetivo normal.
    - Sin coincidencia inequívoca se muestran posibilidades, sin seleccionar.
    """
    with connect() as db:
        tasks = [dict(row) for row in db.execute(
            "SELECT id,game,pokemon,form_name,shiny,ot_exception,required,caught,in_home "
            "FROM bank_tasks ORDER BY game,source_row,id")]
        goals = [dict(row) for row in db.execute(
            "SELECT g.id,g.form_key,g.shiny,g.target,g.in_home,"
            "f.dex_number,f.species,f.form_name "
            "FROM goals g JOIN pokemon_forms f ON f.form_key=g.form_key "
            "ORDER BY f.dex_number,f.form_key")]

    by_species = defaultdict(list)
    for goal in goals:
        by_species[(_normalized(goal["species"]), goal["shiny"])].append(goal)

    result = []
    counts = Counter()
    for task in tasks:
        options = by_species.get((_normalized(task["pokemon"]), task["shiny"]), [])
        requested_form = _form(task["form_name"])
        # Una forma explícita no debe convertirse silenciosamente en otra.
        if requested_form:
            matches = [goal for goal in options if _form(goal["form_name"]) == requested_form]
        else:
            # Si Bank no indica forma, no asumir la base entre varias variantes.
            matches = options if len(options) == 1 else []
        if len(matches) == 1:
            status = "suggested"
            reason = "Coincidencia única de especie, forma y tipo shiny"
            suggestion = {
                "goal_id": matches[0]["id"],
                "form_key": matches[0]["form_key"],
                "dex_number": matches[0]["dex_number"],
                "species": matches[0]["species"],
                "form_name": matches[0]["form_name"],
                "shiny": bool(matches[0]["shiny"]),
                "goal_in_home": matches[0]["in_home"],
                "goal_target": matches[0]["target"],
            }
        elif not options:
            status = "unmatched"
            reason = "No hay objetivo de esta especie en la colección indicada"
            suggestion = None
        elif requested_form and not matches:
            status = "unmatched"
            reason = "No hay coincidencia exacta para la forma indicada"
            suggestion = None
        else:
            status = "ambiguous"
            reason = "Hay varias formas posibles; indicá la forma antes de vincular"
            suggestion = None
        counts[status] += 1
        result.append({
            "task_id": task["id"],
            "game": task["game"],
            "pokemon": task["pokemon"],
            "form_name": task["form_name"],
            "shiny": bool(task["shiny"]),
            "ot_exception": bool(task["ot_exception"]),
            "required": task["required"],
            "caught": task["caught"],
            "bank_in_home": task["in_home"],
            "status": status,
            "reason": reason,
            "suggestion": suggestion,
            "available_forms": [
                {"form_key": option["form_key"], "form_name": option["form_name"]}
                for option in options[:20]
            ] if suggestion is None else [],
        })

    return {
        "items": result,
        "counts": {
            "total": len(tasks),
            "suggested": counts["suggested"],
            "ambiguous": counts["ambiguous"],
            "unmatched": counts["unmatched"],
        },
        "read_only": True,
        "notice": (
            "Las coincidencias son propuestas no confirmadas. Bank y Pokédex "
            "siguen independientes; ningún ejemplar se suma dos veces."
        ),
    }
