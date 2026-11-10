#!/usr/bin/env python3
"""Train a drift model: predict shorten_score = log(BSP) - log(morning WAP).

shorten_score < 0 = the horse SHORTENED (BSP < morning, it was backed).
shorten_score > 0 = the horse DRIFTED (BSP > morning, it was laid).

Combined with the win-prob model, this lets us hard-filter drifters: only bet
when the win model says "value" AND the drift model says "won't drift".

Reuses the same leak-free features as win_prob_model.py.
"""
import sys
from pathlib import Path

import numpy as np
import polars as pl
import lightgbm as lgb

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import win_prob_model as M

SNAP = ROOT / "data" / "win_prob_snapshot.parquet"

PARAMS = {
    "objective": "regression", "metric": "rmse", "boosting_type": "gbdt",
    "learning_rate": 0.05, "num_leaves": 63, "max_depth": -1,
    "min_data_in_leaf": 100, "feature_fraction": 0.8, "bagging_fraction": 0.8,
    "bagging_freq": 1, "lambda_l1": 0.1, "lambda_l2": 0.1, "verbose": -1, "seed": 42,
}


def main():
    df = pl.read_parquet(SNAP).with_columns(
        (pl.col("win_bsp").log() - pl.col("log_win_morningwap")).alias("shorten_score")
    )
    train = df.filter(pl.col("race_date") <= pl.lit("2023-12-31").str.strptime(pl.Date, "%Y-%m-%d"))
    valid = df.filter((pl.col("race_date") >= pl.lit("2024-01-01").str.strptime(pl.Date, "%Y-%m-%d"))
                      & (pl.col("race_date") <= pl.lit("2025-12-31").str.strptime(pl.Date, "%Y-%m-%d")))
    test = df.filter(pl.col("race_date") >= pl.lit("2026-01-01").str.strptime(pl.Date, "%Y-%m-%d"))
    print(f"Train {len(train):,} | Valid {len(valid):,} | Test {len(test):,}")

    Xtr, ytr = train.select(M.FEATURES).to_numpy(), train["shorten_score"].to_numpy()
    Xva, yva = valid.select(M.FEATURES).to_numpy(), valid["shorten_score"].to_numpy()
    Xte, yte = test.select(M.FEATURES).to_numpy(), test["shorten_score"].to_numpy()

    model = lgb.train(PARAMS, lgb.Dataset(Xtr, label=ytr), num_boost_round=2000,
                      valid_sets=[lgb.Dataset(Xva, label=yva)],
                      callbacks=[lgb.early_stopping(100, verbose=False)])
    print(f"Best iter: {model.best_iteration}")

    for name, X, y in [("valid", Xva, yva), ("test", Xte, yte)]:
        p = model.predict(X)
        rmse = np.sqrt(np.mean((y - p) ** 2))
        corr = np.corrcoef(p, y)[0, 1]
        # how well does predicted drift separate actual drifters (y>0) from shorteners (y<0)?
        thr = np.quantile(p, 0.5)
        drifters = y[p > thr]
        shorteners = y[p <= thr]
        sep = drifters.mean() - shorteners.mean()
        print(f"  {name}: RMSE={rmse:.4f}  corr={corr:.4f}  (pred-drifters avg score {drifters.mean():+.4f} vs pred-shorteners {shorteners.mean():+.4f}, sep={sep:+.4f})")

    model.save_model(str(ROOT / "drift_model.txt"))
    print(f"\nSaved drift model to {ROOT / 'drift_model.txt'}")


if __name__ == "__main__":
    main()
