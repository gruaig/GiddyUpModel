"""
End-to-end model training script.

Builds features → Trains model → Evaluates on OOT test set → Logs to MLflow
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from giddyup.data.build import build_training_data, get_feature_list
from giddyup.data.feature_lists import guard_no_market
from giddyup.models.trainer import train_model, TrainConfig


def main():
    """Run full training pipeline."""
    print("🏇 GiddyUp Model Training Pipeline - ABILITY-ONLY")
    print("=" * 80)
    
    # ===== Configuration =====
    config = TrainConfig(
        # IMPORTANT: Hold out 2024-2025 for backtesting!
        train_date_from="2006-01-01",
        train_date_to="2023-12-31",      # Train on 18 years (2006-2023)
        test_date_from="2024-01-01",      # Test on 22 months (OOT)
        test_date_to="2025-10-16",
        
        n_folds=5,
        num_boost_round=2000,
        early_stopping_rounds=100,
        
        experiment_name="horse_racing_win_prob",
        model_name="hrd_win_prob",
    )
    
    print(f"\n📅 Data Split Strategy:")
    print(f"   Training:   {config.train_date_from} to {config.train_date_to}")
    print(f"   Testing:    {config.test_date_from} to {config.test_date_to}")
    print(f"   (Test set is NEVER seen during training - pure backtest!)")
    
    # ===== Step 1: Build Features =====
    print(f"\n" + "=" * 80)
    print("STEP 1: FEATURE ENGINEERING")
    print("=" * 80)
    
    # Build full dataset (both train and test periods)
    df = build_training_data(
        date_from=config.train_date_from,
        date_to=config.test_date_to,  # Include test period for evaluation
        output_path="data/training_dataset.parquet"
    )
    
    # Get feature list (ability-only, no market!)
    features = get_feature_list()
    print(f"\n   Selected {len(features)} features for modeling")
    print(f"\n   Feature List:")
    for i, f in enumerate(features, 1):
        print(f"      {i:2d}. {f}")
    
    # GUARD: Ensure no market features leak into training
    print(f"\n🔒 Running leakage guard...")
    guard_no_market(features)
    print(f"   ✅ No market features detected - training is independent!")
    
    # Check for any market-related keywords that might have snuck in
    market_keywords = ['odds', 'price', 'market', 'rank', 'fav', 'volume', 'drift', 'bsp', 'sp']
    suspicious = [f for f in features if any(k in f.lower() for k in market_keywords)]
    if suspicious:
        print(f"\n⚠️  WARNING: Suspicious features found: {suspicious}")
        print(f"   These may be market-related. Please verify they're pre-race data only.")
    else:
        print(f"   ✅ No suspicious market keywords found in features")
    
    # ===== Step 2: Train Model =====
    print(f"\n" + "=" * 80)
    print("STEP 2: MODEL TRAINING")
    print("=" * 80)
    
    results = train_model(
        df=df,
        feature_cols=features,
        config=config
    )
    
    # ===== Step 3: Summary =====
    print(f"\n" + "=" * 80)
    print("🎉 PIPELINE COMPLETE!")
    print("=" * 80)
    
    print(f"\n✅ Model trained successfully!")
    print(f"\n📊 Performance Summary:")
    print(f"   OOF Log Loss:  {results['oof_logloss']:.4f}")
    print(f"   Test Log Loss: {results['test_logloss']:.4f}")
    print(f"   Test AUC-ROC:  {results['test_auc']:.4f}")
    
    print(f"\n📁 Next Steps:")
    print(f"   1. Review MLflow UI: mlflow ui --backend-store-uri sqlite:///mlflow.db")
    print(f"   2. Promote model to Production if metrics look good")
    print(f"   3. Run backtest on 2024-2025 data to validate edge")
    print(f"   4. Set up scoring pipeline for live predictions")
    
    print(f"\n🔬 Backtest Period Available:")
    print(f"   {config.test_date_from} to {config.test_date_to}")
    print(f"   This data was NEVER used in training!")
    print(f"   Use this to:")
    print(f"      - Validate your signals have edge vs market")
    print(f"      - Check Closing Line Value (CLV)")
    print(f"      - Calculate ROI on recommended stakes")


if __name__ == "__main__":
    main()

