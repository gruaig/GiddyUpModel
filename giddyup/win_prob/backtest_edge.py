#!/usr/bin/env python3
"""Backtest the +EV / anti-drift signal against real BSP (no leakage).

Answers two questions:
  1. If we bet every horse where model_prob x morning_price - 1 > margin
     (the "value" signal), do we actually profit at the morning exchange price?
  2. Do those picks SHORTEN (BSP < morning) or DRIFT (BSP > morning)?

Method (leak-free): train on 2010-2023, predict 2024-2025 and 2026 (never seen),
then back with a flat 1-unit stake at the MORNING price and settle on the outcome.

Morning price = win_morningwap (Betfair morning WAP, i.e. the exchange opening).
BSP = win_bsp (the exchange price at the off).
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


def main():
    df = pl.read_parquet(SNAP)
    # reconstruct the morning price from the log feature
    df = df.with_columns(
        pl.col("log_win_morningwap").exp().alias("morning"),
        pl.col("win_bsp").alias("bsp"),
        pl.col("won").cast(pl.Int32).alias("y"),
    )

    train = df.filter(pl.col("race_date") <= pl.lit("2023-12-31").str.strptime(pl.Date, "%Y-%m-%d"))
    test = df.filter(pl.col("race_date") >= pl.lit("2024-01-01").str.strptime(pl.Date, "%Y-%m-%d"))
    print(f"Train (2010-2023): {len(train):,}  |  Test (2024+): {len(test):,}")

    Xtr = train.select(M.FEATURES).to_numpy()
    ytr = train["y"].to_numpy()
    model = lgb.train(PARAMS, lgb.Dataset(Xtr, label=ytr), num_boost_round=149)  # 149 = tuned best_iter

    p = model.predict(test.select(M.FEATURES).to_numpy())
    test = test.with_columns(pl.Series("p", p))
    test = test.with_columns(
        (pl.col("p") * pl.col("morning") - 1.0).alias("edge_morning"),
        (pl.col("p") * pl.col("bsp") - 1.0).alias("edge_bsp"),
        (pl.col("bsp").log() - pl.col("morning").log()).alias("drift"),
    )

    y = test["y"].to_numpy()
    morning = test["morning"].to_numpy()
    bsp = test["bsp"].to_numpy()

    print("\nBaselines on the test period:")
    print(f"  Bet EVERYTHING at morning: ROI = {(np.where(y == 1, morning - 1, -1.0).sum() / len(y)) * 100:+.2f}%")
    print(f"  Bet EVERYTHING at BSP:     ROI = {(np.where(y == 1, bsp - 1, -1.0).sum() / len(y)) * 100:+.2f}%")
    print(f"  Avg drift (log BSP/morning) whole field: {test['drift'].mean():+.4f}")

    print("\n" + "=" * 92)
    print("VALUE SIGNAL: back every horse with edge_morning > margin (1 unit at the MORNING price)")
    print("=" * 92)
    print(f"{'margin':>8}{'bets':>8}{'ROI@morning':>13}{'hit%':>7}{'avg morning':>12}{'avg BSP':>9}{'avg drift':>11}")
    for margin in (0.00, 0.02, 0.05, 0.10, 0.20, 0.30):
        m = test["edge_morning"].to_numpy() > margin
        n = int(m.sum())
        if n == 0:
            print(f"{margin:>8.2f}{0:>8}  (no bets)")
            continue
        roi = (np.where(y[m] == 1, morning[m] - 1, -1.0).sum() / n) * 100
        hit = y[m].mean() * 100
        avg_m = morning[m].mean()
        avg_b = bsp[m].mean()
        drift = test["drift"].to_numpy()[m].mean()
        print(f"{margin:>8.2f}{n:>8,}{roi:>+12.2f}%{hit:>7.1f}%{avg_m:>12.2f}{avg_b:>9.2f}{drift:>+11.4f}")

    print("\n" + "=" * 92)
    print("SAME SIGNAL, but settled at BSP instead of morning (isolates the drift edge)")
    print("=" * 92)
    print(f"{'margin':>8}{'bets':>8}{'ROI@BSP':>12}{'hit%':>7}")
    for margin in (0.00, 0.02, 0.05, 0.10, 0.20):
        m = test["edge_morning"].to_numpy() > margin
        n = int(m.sum())
        if n == 0:
            continue
        roi = (np.where(y[m] == 1, bsp[m] - 1, -1.0).sum() / n) * 100
        print(f"{margin:>8.2f}{n:>8,}{roi:>+11.2f}%{y[m].mean()*100:>7.1f}%")

    print("\nNote: avg drift < 0 = picks SHORTEN (price comes in); > 0 = picks DRIFT (price goes out).")


if __name__ == "__main__":
    main()
