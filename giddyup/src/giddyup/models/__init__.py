"""
Model training module.

Handles LightGBM/XGBoost training with proper cross-validation.
"""

from .trainer import train_model, load_model_from_mlflow

__all__ = ["train_model", "load_model_from_mlflow"]

