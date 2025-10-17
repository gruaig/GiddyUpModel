"""
Signal publishing utilities.

Handles upserting predictions/signals to the modeling.signals table.
"""

from .signals import publish

__all__ = ["publish"]

