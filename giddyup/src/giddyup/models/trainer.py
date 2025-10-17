"""
Model training with LightGBM and proper time-series validation.

Uses GroupKFold by race_id to prevent leakage within races,
plus out-of-time (OOT) hold-out set for final validation.
"""

import os
from dataclasses import dataclass
from typing import Optional
import polars as pl
import numpy as np
import lightgbm as lgb
from sklearn.model_selection import GroupKFold
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import log_loss, roc_auc_score
import mlflow
import mlflow.lightgbm
from dotenv import load_dotenv

load_dotenv()


@dataclass
class TrainConfig:
    """Configuration for model training."""
    
    # Data splits
    train_date_from: str = "2006-01-01"
    train_date_to: str = "2023-12-31"      # Hold out 2024-2025 for OOT testing
    test_date_from: str = "2024-01-01"      # OOT test set
    test_date_to: str = "2025-10-16"
    
    # Features
    target: str = "won"
    group_col: str = "race_id"
    
    # LightGBM parameters
    params: dict = None
    num_boost_round: int = 2000
    early_stopping_rounds: int = 100
    
    # Cross-validation
    n_folds: int = 5
    
    # MLflow
    experiment_name: str = "horse_racing_win_prob"
    model_name: str = "hrd_win_prob"
    
    def __post_init__(self):
        """Set default params if not provided."""
        if self.params is None:
            self.params = {
                "objective": "binary",
                "metric": "binary_logloss",
                "boosting_type": "gbdt",
                "learning_rate": 0.05,
                "num_leaves": 63,
                "max_depth": 6,
                "min_data_in_leaf": 20,
                "feature_fraction": 0.9,
                "bagging_fraction": 0.9,
                "bagging_freq": 1,
                "lambda_l1": 0.1,
                "lambda_l2": 0.1,
                "verbose": -1,
            }


def train_model(
    df: pl.DataFrame,
    feature_cols: list[str],
    config: Optional[TrainConfig] = None
) -> dict:
    """
    Train LightGBM model with GroupKFold CV and OOT testing.
    
    Args:
        df: Polars DataFrame with features and target
        feature_cols: List of feature column names
        config: Training configuration
        
    Returns:
        Dictionary with metrics and MLflow run info
        
    Example:
        >>> from giddyup.data import build_training_data, get_feature_list
        >>> df = build_training_data("2008-01-01", "2025-10-16")
        >>> features = get_feature_list()
        >>> results = train_model(df, features)
    """
    if config is None:
        config = TrainConfig()
    
    print("=" * 80)
    print("🚂 TRAINING HORSE RACING WIN PROBABILITY MODEL")
    print("=" * 80)
    
    # ===== 1. Split Train/Test by Date =====
    print(f"\n📅 Splitting data:")
    print(f"   Train: {config.train_date_from} to {config.train_date_to}")
    print(f"   Test:  {config.test_date_from} to {config.test_date_to}")
    
    train_df = df.filter(
        (pl.col("race_date") >= pl.lit(config.train_date_from).str.strptime(pl.Date, "%Y-%m-%d")) &
        (pl.col("race_date") <= pl.lit(config.train_date_to).str.strptime(pl.Date, "%Y-%m-%d"))
    )
    
    test_df = df.filter(
        (pl.col("race_date") >= pl.lit(config.test_date_from).str.strptime(pl.Date, "%Y-%m-%d")) &
        (pl.col("race_date") <= pl.lit(config.test_date_to).str.strptime(pl.Date, "%Y-%m-%d"))
    )
    
    print(f"\n   Train: {len(train_df):,} runners from {train_df['race_id'].n_unique():,} races")
    print(f"   Test:  {len(test_df):,} runners from {test_df['race_id'].n_unique():,} races")
    print(f"   Train win rate: {train_df[config.target].mean():.2%}")
    print(f"   Test win rate:  {test_df[config.target].mean():.2%}")
    
    # ===== 2. Prepare Arrays =====
    print(f"\n🔧 Preparing arrays...")
    
    X_train = train_df.select(feature_cols).to_numpy()
    y_train = train_df[config.target].to_numpy()
    groups_train = train_df[config.group_col].to_numpy()
    
    X_test = test_df.select(feature_cols).to_numpy()
    y_test = test_df[config.target].to_numpy()
    
    print(f"   Features: {len(feature_cols)}")
    print(f"   Train shape: {X_train.shape}")
    print(f"   Test shape: {X_test.shape}")
    
    # ===== 3. Set up MLflow =====
    mlflow.set_experiment(config.experiment_name)
    
    with mlflow.start_run() as run:
        run_id = run.info.run_id
        print(f"\n📊 MLflow Run ID: {run_id}")
        
        # Log config
        mlflow.log_params({
            "train_date_from": config.train_date_from,
            "train_date_to": config.train_date_to,
            "test_date_from": config.test_date_from,
            "test_date_to": config.test_date_to,
            "n_folds": config.n_folds,
            "n_features": len(feature_cols),
            **config.params
        })
        
        # ===== 4. GroupKFold Cross-Validation =====
        print(f"\n🔀 Running {config.n_folds}-fold GroupKFold cross-validation...")
        print("   (Prevents leakage: all horses in same race stay in same fold)")
        
        gkf = GroupKFold(n_splits=config.n_folds)
        oof_predictions = np.zeros(len(y_train))
        models = []
        fold_scores = []
        
        for fold, (train_idx, val_idx) in enumerate(gkf.split(X_train, y_train, groups_train), 1):
            print(f"\n   Fold {fold}/{config.n_folds}:")
            print(f"      Train: {len(train_idx):,} runners")
            print(f"      Val:   {len(val_idx):,} runners")
            
            # Create LightGBM datasets
            dtrain = lgb.Dataset(X_train[train_idx], label=y_train[train_idx])
            dval = lgb.Dataset(X_train[val_idx], label=y_train[val_idx])
            
            # Train with early stopping
            callbacks = [
                lgb.log_evaluation(period=100),
                lgb.early_stopping(stopping_rounds=config.early_stopping_rounds, verbose=False)
            ]
            
            booster = lgb.train(
                config.params,
                dtrain,
                num_boost_round=config.num_boost_round,
                valid_sets=[dval],
                valid_names=['val'],
                callbacks=callbacks
            )
            
            # Predict on validation fold
            oof_predictions[val_idx] = booster.predict(X_train[val_idx])
            models.append(booster)
            
            # Fold metrics
            fold_logloss = log_loss(y_train[val_idx], oof_predictions[val_idx])
            fold_auc = roc_auc_score(y_train[val_idx], oof_predictions[val_idx])
            fold_scores.append((fold_logloss, fold_auc))
            
            print(f"      Best iteration: {booster.best_iteration}")
            print(f"      Log Loss: {fold_logloss:.4f}")
            print(f"      AUC-ROC: {fold_auc:.4f}")
        
        # ===== 5. OOF Metrics =====
        print(f"\n📈 Out-of-Fold (OOF) Metrics:")
        oof_logloss = log_loss(y_train, oof_predictions)
        oof_auc = roc_auc_score(y_train, oof_predictions)
        
        print(f"   Log Loss: {oof_logloss:.4f}")
        print(f"   AUC-ROC: {oof_auc:.4f}")
        
        mlflow.log_metrics({
            "oof_logloss": oof_logloss,
            "oof_auc": oof_auc,
        })
        
        # ===== 6. Calibration =====
        print(f"\n🎯 Calibrating probabilities (Isotonic Regression)...")
        
        # Use isotonic regression directly on OOF predictions
        from sklearn.isotonic import IsotonicRegression
        
        iso_reg = IsotonicRegression(out_of_bounds='clip')
        iso_reg.fit(oof_predictions, y_train)
        
        # Get calibrated OOF predictions
        oof_calibrated = iso_reg.predict(oof_predictions)
        
        oof_calibrated_logloss = log_loss(y_train, oof_calibrated)
        print(f"   Calibrated Log Loss: {oof_calibrated_logloss:.4f}")
        print(f"   Improvement: {oof_logloss - oof_calibrated_logloss:.4f}")
        
        mlflow.log_metric("oof_calibrated_logloss", oof_calibrated_logloss)
        
        # ===== 7. Test Set (OOT) Evaluation =====
        print(f"\n🧪 Evaluating on Out-of-Time (OOT) test set...")
        print(f"   Period: {config.test_date_from} to {config.test_date_to}")
        print(f"   This data was NEVER seen during training!")
        
        # Uncalibrated predictions
        test_preds_uncal = np.mean([m.predict(X_test) for m in models], axis=0)
        test_logloss_uncal = log_loss(y_test, test_preds_uncal)
        test_auc_uncal = roc_auc_score(y_test, test_preds_uncal)
        
        # Calibrated predictions
        test_preds_cal = iso_reg.predict(test_preds_uncal)
        test_logloss_cal = log_loss(y_test, test_preds_cal)
        test_auc_cal = roc_auc_score(y_test, test_preds_cal)
        
        print(f"\n   Uncalibrated:")
        print(f"      Log Loss: {test_logloss_uncal:.4f}")
        print(f"      AUC-ROC: {test_auc_uncal:.4f}")
        print(f"\n   Calibrated:")
        print(f"      Log Loss: {test_logloss_cal:.4f}")
        print(f"      AUC-ROC: {test_auc_cal:.4f}")
        
        mlflow.log_metrics({
            "test_logloss_uncalibrated": test_logloss_uncal,
            "test_auc_uncalibrated": test_auc_uncal,
            "test_logloss_calibrated": test_logloss_cal,
            "test_auc_calibrated": test_auc_cal,
        })
        
        # ===== 8. Feature Importance =====
        print(f"\n🔍 Top 10 Features:")
        
        # Average feature importance across folds
        feature_importance = np.mean(
            [m.feature_importance(importance_type='gain') for m in models],
            axis=0
        )
        
        importance_df = pl.DataFrame({
            "feature": feature_cols,
            "importance": feature_importance
        }).sort("importance", descending=True)
        
        for i, row in enumerate(importance_df.head(10).iter_rows(named=True), 1):
            print(f"   {i:2d}. {row['feature']:30s} {row['importance']:10.0f}")
        
        # Log to MLflow
        importance_dict = {
            f"importance_{name}": imp
            for name, imp in zip(feature_cols, feature_importance)
        }
        mlflow.log_metrics(importance_dict)
        
        # ===== 9. Log Model to MLflow =====
        print(f"\n💾 Logging model to MLflow...")
        
        # Create a simple wrapper class for prediction
        class CalibratedEnsemble:
            def __init__(self, lgb_models, calibrator):
                self.models = lgb_models
                self.calibrator = calibrator
            
            def predict_proba(self, X):
                # Average predictions from all folds
                preds = np.mean([m.predict(X) for m in self.models], axis=0)
                # Calibrate
                preds_cal = self.calibrator.predict(preds)
                return np.vstack([1 - preds_cal, preds_cal]).T
            
            def predict(self, X):
                return self.predict_proba(X)[:, 1]
        
        # Create ensemble
        ensemble = CalibratedEnsemble(models, iso_reg)
        
        # Log the ensemble model
        mlflow.sklearn.log_model(
            ensemble,
            "calibrated_model",
            registered_model_name=config.model_name
        )
        
        # Also log individual boosters
        for i, model in enumerate(models):
            mlflow.lightgbm.log_model(model, f"fold_{i+1}_booster")
        
        # Log calibrator separately
        mlflow.sklearn.log_model(iso_reg, "isotonic_calibrator")
        
        print(f"   ✅ Model logged to MLflow")
        print(f"   Model name: {config.model_name}")
        print(f"   Run ID: {run_id}")
        
        # ===== 10. Summary =====
        print(f"\n" + "=" * 80)
        print("✅ TRAINING COMPLETE")
        print("=" * 80)
        print(f"\n📊 Final Metrics:")
        print(f"   OOF Log Loss (calibrated): {oof_calibrated_logloss:.4f}")
        print(f"   Test Log Loss (calibrated): {test_logloss_cal:.4f}")
        print(f"   Test AUC-ROC: {test_auc_cal:.4f}")
        print(f"\n🎯 Model Performance:")
        if test_logloss_cal < oof_calibrated_logloss * 1.05:
            print(f"   ✅ GOOD: Test performance within 5% of training")
        else:
            print(f"   ⚠️  WARNING: Test performance degraded")
        
        print(f"\n📁 MLflow:")
        print(f"   Experiment: {config.experiment_name}")
        print(f"   Run ID: {run_id}")
        print(f"   Model: {config.model_name}")
        
        return {
            "run_id": run_id,
            "oof_logloss": oof_calibrated_logloss,
            "test_logloss": test_logloss_cal,
            "test_auc": test_auc_cal,
            "models": models,
            "calibrator": iso_reg,
            "ensemble": ensemble,
            "feature_importance": importance_df,
        }


def load_model_from_mlflow(
    model_name: str = "hrd_win_prob",
    stage: str = "Production"
) -> any:
    """
    Load a model from MLflow registry.
    
    Args:
        model_name: Registered model name
        stage: Model stage (Production, Staging, etc.)
        
    Returns:
        Loaded CalibratedEnsemble model
        
    Example:
        >>> model = load_model_from_mlflow("hrd_win_prob", "Production")
        >>> predictions = model.predict(X_test)  # Returns win probabilities
    """
    model_uri = f"models:/{model_name}/{stage}"
    print(f"📥 Loading model: {model_uri}")
    
    model = mlflow.sklearn.load_model(model_uri)
    
    print(f"   ✅ Model loaded (CalibratedEnsemble)")
    print(f"   Type: {type(model)}")
    return model

