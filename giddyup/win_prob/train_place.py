#!/usr/bin/env python3
"""Train a PLACE model: predict whether a horse finishes in the places (top 2/3/4).

Place terms (each-way standard):
  - 2-4 runners : win only (1 place)
  - 5-7 runners : 2 places, 1/4 odds
  - 8-15 runners: 3 places, 1/5 odds
  - 16+ runners : 4 places, 1/4 odds

Reuses the same leak-free features as win_prob_model.py, target = pos_num <= n_places.
This enables each-way / place bets on top of the win model.
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
    "objective": "binary", "metric": "binary_logloss", "boosting_type": "gbdt",
    "learning_rate": 0.05, "num_leaves": 127, "max_depth": -1,
    "min_data_in_leaf": 100, "feature_fraction": 0.8, "bagging_fraction": 0.8,
    "bagging_freq": 1, "lambda_l1": 0.5, "lambda_l2": 1.0, "verbose": -1, "seed": 42,
}


def n_places(field_size):
    if field_size is None:
        return 3
    if field_size <= 4:
        return 1
    if field_size <= 7:
        return 2
    if field_size <= 15:
        return 3
    return 4


def place_fraction(field_size):
    """Each-way place odds fraction (of the win odds)."""
    if field_size is None:
        return 0.2
    if field_size <= 7:
        return 0.25
    if field_size <= 15:
        return 0.20
    return 0.25


def main():
    df = pl.read_parquet(SNAP)
    df = df.filter(pl.col("pos_num").is_not_null())  # only horses that actually ran
    df = df.with_columns([
        pl.col("pos_num").cast(pl.Int64),
        pl.col("field_size").cast(pl.Int64),
    ])
    df = df.with_columns(
        pl.when(pl.col("field_size") <= 4).then(1)
        .when(pl.col("field_size") <= 7).then(2)
        .when(pl.col("field_size") <= 15).then(3)
        .otherwise(4).alias("n_places")
    ).with_columns(
        (pl.col("pos_num") <= pl.col("n_places")).cast(pl.Int32).alias("placed")
    )

    train = df.filter(pl.col("race_date") <= pl.lit("2023-12-31").str.strptime(pl.Date, "%Y-%m-%d"))
    valid = df.filter((pl.col("race_date") >= pl.lit("2024-01-01").str.strptime(pl.Date, "%Y-%m-%d"))
                      & (pl.col("race_date") <= pl.lit("2025-12-31").str.strptime(pl.Date, "%Y-%m-%d")))
    test = df.filter(pl.col("race_date") >= pl.lit("2026-01-01").str.strptime(pl.Date, "%Y-%m-%d"))
    print(f"Train {len(train):,} | Valid {len(valid):,} | Test {len(test):,}")

    Xtr, ytr = train.select(M.FEATURES).to_numpy(), train["placed"].to_numpy()
    Xva, yva = valid.select(M.FEATURES).to_numpy(), valid["placed"].to_numpy()
    Xte, yte = test.select(M.FEATURES).to_numpy(), test["placed"].to_numpy()

    model = lgb.train(PARAMS, lgb.Dataset(Xtr, label=ytr), num_boost_round=3000,
                      valid_sets=[lgb.Dataset(Xva, label=yva)],
                      callbacks=[lgb.early_stopping(100, verbose=False)])
    print(f"Best iter: {model.best_iteration}")

    def logloss(y, p):
        p = np.clip(p, 1e-12, 1 - 1e-12)
        return -np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))

    def auc(y, p):
        o = np.argsort(p); y = y[o]
        np_ = y.sum(); nn = len(y) - np_
        if np_ == 0 or nn == 0:
            return float("nan")
        ranks = np.arange(1, len(y) + 1)[y == 1]
        return (ranks.sum() - np_ * (np_ + 1) / 2) / (np_ * nn)

    for name, X, y, d in [("valid", Xva, yva, valid), ("test", Xte, yte, test)]:
        p = model.predict(X)
        base = (d["n_places"].to_numpy() / d["field_size"].to_numpy()).clip(0, 1)
        print(f"  {name}: model logloss={logloss(y, p):.4f} (baseline {logloss(y, base):.4f})  AUC={auc(y, p):.4f}")

    model.save_model(str(ROOT / "place_model.txt"))
    print(f"\nSaved place model to {ROOT / 'place_model.txt'}")


if __name__ == "__main__":
    main()
