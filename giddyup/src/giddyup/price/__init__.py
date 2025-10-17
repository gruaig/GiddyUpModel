"""
Pricing and value calculation utilities.

Handles edge calculation, Kelly criterion, EV computation with commission.
"""

from .value import (
    fair_odds,
    ev_win,
    kelly_fraction,
    remove_vig,
)

__all__ = [
    "fair_odds",
    "ev_win", 
    "kelly_fraction",
    "remove_vig",
]

