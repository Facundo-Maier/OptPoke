"""Probability utilities. Independent attempts with constant p only."""
from math import expm1, log1p


def cumulative_probability(p: float, attempts: int) -> float:
    if not 0 <= p <= 1 or attempts < 0:
        raise ValueError("Probabilidad o intentos inválidos")
    if p == 1:
        return 1.0 if attempts else 0.0
    if p == 0 or attempts == 0:
        return 0.0
    return -expm1(attempts * log1p(-p))
