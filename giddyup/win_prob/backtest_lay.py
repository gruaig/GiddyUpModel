#!/usr/bin/env python3
"""Backtest the LAY side of the value signal (out-of-sample, no leakage).

The Action column emits LAY when the model thinks the exchange lay price is SHORTER
than the model's fair price (i.e. the horse is overvalued). This script tests whether
actually laying those horses is +EV.

Method: train 2010-2023, predict 2024+ (never seen), then lay every horse where
model_win% x BSP < 1 - margin (model says the horse wins less than BSP implies),
settling at BSP as the lay price (the exchange lay ≈ BSP at the off).

Lay P/L per 1-unit stake: +1 if the horse loses, -(BSP - 1) if it wins.
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
    df = pl.read_parquet(SNAP).with_columns(
        pl.col("win_bsp").alias("bsp"),
        pl.col("won").cast(pl.Int32).alias("y"),
    )
    train = df.filter(pl.col("race_date") <= pl.lit("2023-12-31").str.strptime(pl.Date, "%Y-%m-%d"))
    test = df.filter(pl.col("race_date") >= pl.lit("2024-01-01").str.strptime(pl.Date, "%Y-%m-%d"))
    print(f"Train (2010-2023): {len(train):,} | Test (2024+): {len(test):,}")

    model = lgb.train(PARAMS, lgb.Dataset(train.select(M.FEATURES).to_numpy(), label=train["y"].to_numpy()),
                      num_boost_round=149)
    p = model.predict(test.select(M.FEATURES).to_numpy())

    y = test["y"].to_numpy()
    bsp = test["bsp"].to_numpy()

    # baseline: lay EVERYTHING at BSP
    all_lay = np.where(y == 0, 1.0, -(bsp - 1.0)).sum() / len(y) * 100
    print(f"\nBaseline: lay EVERYTHING at BSP: ROI = {all_lay:+.2f}%")

    print("\n" + "=" * 92)
    print("LAY signal: lay every horse where model_win% x BSP < 1 - margin (overvalued)")
    print("=" * 92)
    print(f"{'margin':>8}{'lays':>8}{'lay ROI':>12}{'hit (loses)':>13}{'avg BSP':>9}")
    for margin in (0.00, 0.02, 0.05, 0.10, 0.15):
        m = (p * bsp) < (1 - margin)
        n = int(m.sum())
        if n == 0:
            print(f"{margin:>8.2f}{0:>8}  (no lays)")
            continue
        pnl = np.where(y[m] == 0, 1.0, -(bsp[m] - 1.0)).sum()
        roi = pnl / n * 100
        loses = (y[m] == 0).mean() * 100
        print(f"{margin:>8.2f}{n:>8,}{roi:>+11.2f}%{loses:>12.1f}%{bsp[m].mean():>9.2f}")

    # for comparison: the BACK side (same signal, back when overvalued is false -> value)
    print("\n" + "=" * 92)
    print("(comparison) BACK signal: back every horse where model_win% x BSP > 1 + margin")
    print("=" * 92)
    print(f"{'margin':>8}{'backs':>8}{'back ROI':>12}{'hit (wins)':>12}{'avg BSP':>9}")
    for margin in (0.00, 0.02, 0.05, 0.10):
        m = (p * bsp) > (1 + margin)
        n = int(m.sum())
        if n == 0:
            continue
        pnl = np.where(y[m] == 1, bsp[m] - 1, -1.0).sum()
        roi = pnl / n * 100
        wins = (y[m] == 1).mean() * 100
        print(f"{margin:>8.2f}{n:>8,}{roi:>+11.2f}%{wins:>12.1f}%{bsp[m].mean():>9.2f}")

    print("\nNote: a positive LAY ROI means the model reliably finds overvalued horses (shorten/lose more than BSP).")
    print("A negative LAY ROI means we should drop the LAY action and go BACK-only.")


if __name__ == "__main__":
    main()
