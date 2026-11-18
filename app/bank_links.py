"""Normalización mínima para validar enlaces explícitos Bank -> objetivo Dex."""
from __future__ import annotations

import unicodedata


def _normalized(value: str | None) -> str:
    value = unicodedata.normalize("NFKD", str(value or "").strip().casefold())
    return " ".join("".join(ch for ch in value if not unicodedata.combining(ch)).split())


def _form(value: str | None) -> str:
    normalized = _normalized(value)
    return "" if normalized in {"", "base", "forma base", "normal"} else normalized
