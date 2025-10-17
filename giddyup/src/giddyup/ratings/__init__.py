"""
GiddyUp Performance Rating (GPR) system.

Builds a pounds-scale performance rating for each horse,
comparable to BHA Official Rating.
"""

from .gpr import (
    make_distance_band,
    lbs_per_length,
    compute_gpr,
)

__all__ = [
    "make_distance_band",
    "lbs_per_length",
    "compute_gpr",
]

