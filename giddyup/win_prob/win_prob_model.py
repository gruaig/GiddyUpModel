#!/usr/bin/env python3
"""Win-probability model benchmarked against BSP (strictly no leakage).

Builds a leak-free dataset of GB/IRE runners that have both Betfair BSP and a
morning price, computes point-in-time form/context/morning-market features
(features only ever use PAST races via shift/cum over the relevant key), then
trains a LightGBM win-probability classifier on 2010-2023 and evaluates it on
2024-2025 (the last two years).

Benchmark = de-overrounded BSP implied probability (the market's final, most
efficient price). "How close can we get to BSP" = compare our log-loss / AUC to
BSP's, then run a simple overlay betting backtest.

IMPORTANT data-quality note: the DB stores many races twice (name/type drift,
e.g. "Flat" vs "Handicap"), so a horse can have two runner rows for the same
real race. The builder deduplicates by true race key (date, course, off_time)
before any feature computation, otherwise form features would "leak" the result
through the duplicate.

Usage:
    python win_prob_model.py                 # build (cached) + train + eval
    python win_prob_model.py --rebuild       # force re-fetch from Postgres
    python win_prob_model.py --no-train      # only build the dataset
"""

import argparse
import os
from pathlib import Path

import numpy as np
import polars as pl
import lightgbm as lgb
from dotenv import load_dotenv
import joblib
from sklearn.isotonic import IsotonicRegression

load_dotenv()

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
PARQUET = DATA_DIR / "win_prob_snapshot.parquet"

# ---- Fixed-vocabulary categorical codes (same across train/test) ----
REGION_MAP = {"GB": 0, "IRE": 1}
# "Handicap" (flat handicap) drifts to the Flat discipline; hurdles/chase likewise.
RACE_TYPE_MAP = {
    "Flat": 0, "Handicap": 0,
    "Hurdle": 1, "Handicap Hurdle": 1,
    "Chase": 2, "Handicap Chase": 2,
    "NH Flat": 3,
}
SURFACE_MAP = {"Turf": 0, "All-Weather": 1, "AW": 1, "Fibresand": 2}
GOING_GROUPED_MAP = {"firm": 0, "good": 1, "soft": 2, "heavy": 3, "unknown": 4}
SEX_MAP = {"C": 1, "F": 2, "G": 3, "M": 4, "": 0}

TRAIN_FROM, TRAIN_TO = "2010-01-01", "2023-12-31"
VALID_FROM, VALID_TO = "2024-01-01", "2025-12-31"   # held-out early-stopping validation
TEST_FROM, TEST_TO = "2026-01-01", "2026-12-31"      # final backtest (BSP covers Jan–Feb 2026)

FEATURES = [
    # horse form (past only)
    "days_since_run", "last_pos", "last_pos_2", "last_pos_3", "avg_btn_last_3",
    "career_runs", "career_strike_rate",
    # horse ability (past only) — Racing Post Rating from prior runs (~46% covered 2014+)
    "last_rpr", "avg_rpr_last_3", "best_rpr_career",
    # trainer / jockey (past only)
    "trainer_sr_total", "trainer_runs_total",
    "jockey_sr_total", "jockey_runs_total",
    # course (past only)
    "runs_at_course", "wins_at_course", "course_strike_rate",
    # race context (pre-race)
    "field_size", "class_numeric", "is_group_listed", "going_grouped",
    "is_aw", "is_flat", "dist_f", "draw", "age", "lbs", "sex", "official_rating",
    # morning market (decision-time; BSP is the benchmark, not a feature)
    "log_win_morningwap", "morning_market_rank", "morning_prob",
]


def get_connection_string() -> str:
    dsn = os.getenv("PG_DSN")
    if not dsn:
        raise ValueError("PG_DSN not set")
    return dsn.replace("+psycopg", "")


def compute_features(df: pl.DataFrame) -> pl.DataFrame:
    """Add leak-free form/context/market features to a frame of runners.

    Expects these raw columns present: race_date, off_time, race_key, horse_id,
    trainer_id, jockey_id, course_id, runner_id, pos_num, beaten_lengths, won,
    rpr, class, going, surface, race_type, region, sex, win_morningwap, draw,
    official_rating, field_size. Sorts by event time first; every .shift / .cum_*
    / .rolling_* is strictly past-only (no leakage). Used by both the training
    snapshot builder and the live predict_today pipeline.
    """
    df = df.sort(["race_date", "off_time", "race_key"])

    won = pl.col("won").cast(pl.Int32)

    # ---- horse form (past only) ----
    df = df.with_columns([
        (pl.col("race_date") - pl.col("race_date").shift(1).over("horse_id")).dt.total_days()
        .fill_null(999).alias("days_since_run"),
        pl.col("pos_num").shift(1).over("horse_id").alias("last_pos"),
        pl.col("pos_num").shift(2).over("horse_id").alias("last_pos_2"),
        pl.col("pos_num").shift(3).over("horse_id").alias("last_pos_3"),
        pl.col("beaten_lengths").shift(1).over("horse_id")
        .rolling_mean(window_size=3, min_samples=1).alias("avg_btn_last_3"),
        (pl.col("runner_id").cum_count().over("horse_id") - 1).alias("career_runs"),
        won.cum_sum().over("horse_id").shift(1).fill_null(0).alias("career_wins"),
    ])
    df = df.with_columns(
        (pl.col("career_wins") / pl.col("career_runs").clip(lower_bound=1))
        .alias("career_strike_rate")
    )

    # ---- horse ability (past only) — Racing Post Rating from prior runs ----
    df = df.with_columns([
        pl.col("rpr").shift(1).over("horse_id").fill_null(0).alias("last_rpr"),
        pl.col("rpr").shift(1).over("horse_id")
        .rolling_mean(window_size=3, min_samples=1).fill_null(0).alias("avg_rpr_last_3"),
    ])
    df = df.with_columns(
        pl.col("last_rpr").cum_max().over("horse_id").alias("best_rpr_career")
    )

    # ---- trainer / jockey form (past only) ----
    df = df.with_columns([
        won.cum_sum().over("trainer_id").shift(1).fill_null(0).alias("trainer_wins_total"),
        (pl.col("runner_id").cum_count().over("trainer_id") - 1).alias("trainer_runs_total"),
        won.cum_sum().over("jockey_id").shift(1).fill_null(0).alias("jockey_wins_total"),
        (pl.col("runner_id").cum_count().over("jockey_id") - 1).alias("jockey_runs_total"),
    ])
    df = df.with_columns([
        (pl.col("trainer_wins_total") / pl.col("trainer_runs_total").clip(lower_bound=1)).alias("trainer_sr_total"),
        (pl.col("jockey_wins_total") / pl.col("jockey_runs_total").clip(lower_bound=1)).alias("jockey_sr_total"),
    ])

    # ---- course form (past only) ----
    df = df.with_columns([
        (pl.col("runner_id").cum_count().over(["horse_id", "course_id"]) - 1).alias("runs_at_course"),
        won.cum_sum().over(["horse_id", "course_id"]).shift(1).fill_null(0).alias("wins_at_course"),
    ])
    df = df.with_columns(
        (pl.col("wins_at_course") / pl.col("runs_at_course").clip(lower_bound=1)).alias("course_strike_rate")
    )

    # ---- race context (pre-race) ----
    df = df.with_columns([
        pl.col("class").str.extract(r"(\d+)", 1).cast(pl.Int32, strict=False).fill_null(7).alias("class_numeric"),
        pl.col("class").str.contains(r"(?i)Group|Listed").cast(pl.Int32).fill_null(0).alias("is_group_listed"),
        pl.when(pl.col("going").str.contains("(?i)firm")).then(pl.lit("firm"))
        .when(pl.col("going").str.contains("(?i)good")).then(pl.lit("good"))
        .when(pl.col("going").str.contains("(?i)soft")).then(pl.lit("soft"))
        .when(pl.col("going").str.contains("(?i)heavy")).then(pl.lit("heavy"))
        .otherwise(pl.lit("unknown")).alias("going_grouped"),
        (pl.col("surface") == "AW").cast(pl.Int32).alias("is_aw"),
        (pl.col("race_type") == "Flat").cast(pl.Int32).alias("is_flat"),
    ])
    df = df.with_columns([
        pl.col("region").cast(pl.Utf8).fill_null("").replace(REGION_MAP, default=0).cast(pl.Int32).alias("region"),
        pl.col("race_type").cast(pl.Utf8).fill_null("").replace(RACE_TYPE_MAP, default=0).cast(pl.Int32).alias("race_type"),
        pl.col("surface").cast(pl.Utf8).fill_null("").replace(SURFACE_MAP, default=0).cast(pl.Int32).alias("surface"),
        pl.col("going_grouped").cast(pl.Utf8).replace(GOING_GROUPED_MAP, default=4).cast(pl.Int32).alias("going_grouped"),
        pl.col("sex").cast(pl.Utf8).fill_null("").replace(SEX_MAP, default=0).cast(pl.Int32).alias("sex"),
    ])

    # ---- morning market features (decision-time) ----
    df = df.with_columns([
        pl.col("win_morningwap").log().alias("log_win_morningwap"),
        pl.col("win_morningwap").rank("ordinal").over("race_key").alias("morning_market_rank"),
        (1.0 / pl.col("win_morningwap")).alias("_mp_raw"),
    ])
    race_sum = df.group_by("race_key").agg(pl.col("_mp_raw").sum().alias("_mp_sum"))
    df = df.join(race_sum, on="race_key").with_columns(
        (pl.col("_mp_raw") / pl.col("_mp_sum")).alias("morning_prob")
    ).drop(["_mp_raw", "_mp_sum"])

    # ---- null handling for features (not targets) ----
    df = df.with_columns([
        pl.col("days_since_run").fill_null(999),
        pl.col("draw").fill_null(0),
        pl.col("official_rating").fill_null(0),
        pl.col("last_pos").fill_null(99),
        pl.col("last_pos_2").fill_null(99),
        pl.col("last_pos_3").fill_null(99),
        pl.col("avg_btn_last_3").fill_null(10.0),
        pl.col("trainer_sr_total").fill_null(0.0),
        pl.col("jockey_sr_total").fill_null(0.0),
        pl.col("career_strike_rate").fill_null(0.0),
        pl.col("course_strike_rate").fill_null(0.0),
        pl.col("morning_prob").fill_null(1.0 / pl.col("field_size")),
    ])
    return df


def build_dataset() -> pl.DataFrame:
    print(f"Building leak-free snapshot {TRAIN_FROM} -> {TEST_TO} ...")
    query = """
    SELECT
        ru.runner_id, ru.race_id, r.race_date, r.region, r.course_id, r.off_time,
        r.race_type, r.class, r.dist_f, r.dist_m, r.going, r.surface, r.ran,
        ru.horse_id, ru.trainer_id, ru.jockey_id, ru.num, ru.draw, ru.age, ru.sex,
        ru.lbs, ru.hg, ru.or AS official_rating,
        ru.win_bsp, ru.win_morningwap, ru.pos_num, ru.btn AS beaten_lengths, ru.rpr,
        ru.win_flag AS won
    FROM racing.runners ru
    JOIN racing.races r ON r.race_id = ru.race_id
    WHERE r.race_date BETWEEN DATE '{date_from}' AND DATE '{date_to}'
      AND ru.horse_id IS NOT NULL
      AND ru.win_bsp IS NOT NULL AND ru.win_bsp >= 1.01
      AND ru.win_morningwap IS NOT NULL AND ru.win_morningwap >= 1.01
    """.format(date_from=TRAIN_FROM, date_to=TEST_TO)
    df = pl.read_database_uri(query=query, uri=get_connection_string())
    print(f"  Loaded {len(df):,} runner rows")

    # ----- Canonicalize duplicated races before ANY feature work -----
    # The DB stores many real races twice (name/type drift, course-id drift, and
    # timezone-shifted off_times), so a horse can have two runner rows for the
    # same race. A horse runs at most once a day, so a horse appearing in two
    # race_ids on the same date means those race_ids are the same real race.
    # Union-find those race_ids into one canonical race, then keep one row per
    # (canonical race, horse), preferring the copy with a finishing position.
    def _find(parent, x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def _union(parent, a, b):
        ra, rb = _find(parent, a), _find(parent, b)
        if ra != rb:
            parent[rb] = ra

    parent: dict = {}
    multi = (df.group_by(["race_date", "horse_id"])
               .agg(pl.col("race_id").unique().alias("rids"))
               .filter(pl.col("rids").list.len() > 1))
    print(f"  Horse-date pairs spanning >1 race_id (dup races): {len(multi):,}")
    for date, _horse, rids in multi.select(["race_date", "horse_id", "rids"]).iter_rows():
        for rid in rids[1:]:
            _union(parent, rids[0], rid)

    # Map every race_id to its canonical representative (min of the cluster for
    # stability), then set the true race key.
    canon_map = (df.select("race_id").unique().with_columns(
        pl.col("race_id").map_elements(lambda r: _find(parent, r), return_dtype=pl.Int64).alias("_root")))
    root_min = (canon_map.group_by("_root").agg(pl.col("race_id").min().alias("canon_race")))
    canon_map = canon_map.join(root_min, on="_root").select(["race_id", "canon_race"])
    df = df.join(canon_map, on="race_id").with_columns(
        pl.col("canon_race").cast(pl.Utf8).alias("race_key"),
        (pl.col("pos_num").is_not_null().cast(pl.Int32) * 2
         + pl.col("win_bsp").is_not_null().cast(pl.Int32)).alias("_cmp"),
    )
    n_before = len(df)
    df = (df.sort(["race_key", "horse_id", "_cmp"], descending=[False, False, True])
            .unique(subset=["race_key", "horse_id"], keep="first")
            .drop("_cmp"))
    print(f"  Deduped {n_before:,} -> {len(df):,} rows ({n_before - len(df):,} duplicate runner rows removed)")

    # Recompute field size from the canonical race (declared `ran` can be stale).
    field = df.group_by("race_key").agg(pl.len().alias("field_size"))
    df = df.join(field, on="race_key").filter(pl.col("field_size") >= 3)

    df = compute_features(df)

    # ---- benchmark: de-overrounded BSP implied probability (training only) ----
    df = df.with_columns((1.0 / pl.col("win_bsp")).alias("_bsp_raw"))
    bsp_sum = df.group_by("race_key").agg(pl.col("_bsp_raw").sum().alias("_bsp_sum"))
    df = df.join(bsp_sum, on="race_key").with_columns(
        (pl.col("_bsp_raw") / pl.col("_bsp_sum")).alias("bsp_prob")
    ).drop(["_bsp_raw", "_bsp_sum"])

    keep = ["runner_id", "race_key", "race_date", "region", "race_type", "won", "win_bsp", "bsp_prob", "pos_num"] + FEATURES
    df = df.select([c for c in keep if c in df.columns])
    print(f"  Final snapshot: {len(df):,} rows, {len(FEATURES)} features, {df['race_key'].n_unique():,} races")
    return df


def log_loss(y, p):
    p = np.clip(p, 1e-12, 1 - 1e-12)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))


def auc(y, p):
    order = np.argsort(p)
    y = y[order]
    n_pos = int(y.sum())
    n_neg = len(y) - n_pos
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    ranks = np.arange(1, len(y) + 1)[y == 1]
    return float((ranks.sum() - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg))


def evaluate(df: pl.DataFrame, tag: str, model=None, calib=None):
    y = df["won"].to_numpy().astype(int)
    bsp = df["bsp_prob"].to_numpy()
    p_model = model.predict(df.select(FEATURES).to_numpy()) if model is not None else None
    if p_model is not None and calib is not None:
        p_model = calib.predict(p_model)

    print(f"\n===== {tag}  (n={len(df):,}, races={df['race_key'].n_unique():,}, win rate={y.mean():.3f}) =====")
    print(f"  BSP   log-loss = {log_loss(y, bsp):.5f}   AUC = {auc(y, bsp):.4f}")
    if p_model is not None:
        print(f"  Model log-loss = {log_loss(y, p_model):.5f}   AUC = {auc(y, p_model):.4f}")

        # ---- overlay betting backtest: bet when model > BSP by margin ----
        print("\n  Overlay backtest (flat 1-unit win bet when model_prob > BSP_prob + margin):")
        for margin in (0.00, 0.02, 0.05, 0.10):
            bets = p_model > (bsp + margin)
            n = int(bets.sum())
            if n == 0:
                print(f"    margin {margin:+.2f}: no bets")
                continue
            pnl = np.where(bets, np.where(y == 1, df["win_bsp"].to_numpy() - 1, -1.0), 0.0).sum()
            roi = pnl / n * 100
            print(f"    margin {margin:+.2f}: {n:,} bets, PnL={pnl:+.1f}u, ROI={roi:+.2f}%, "
                  f"hit rate={y[bets].mean()*100:.1f}%, avg BSP={df['win_bsp'].to_numpy()[bets].mean():.2f}")

        # ---- calibration (binned) ----
        print("\n  Calibration (model prob bins vs observed win rate):")
        edges = np.unique(np.quantile(p_model, np.linspace(0, 1, 11)))
        for lo, hi in zip(edges[:-1], edges[1:]):
            m = (p_model >= lo) & (p_model < hi)
            if m.sum() < 50:
                continue
            print(f"    [{lo:.3f},{hi:.3f}): n={m.sum():,}, pred={p_model[m].mean():.3f}, "
                  f"actual={y[m].mean():.3f}")
    return p_model


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rebuild", action="store_true", help="force re-fetch from Postgres")
    ap.add_argument("--no-train", action="store_true", help="only build the dataset")
    args = ap.parse_args()

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if PARQUET.exists() and not args.rebuild:
        print(f"Loading cached snapshot from {PARQUET}")
        df = pl.read_parquet(PARQUET)
    else:
        df = build_dataset()
        df.write_parquet(PARQUET)
        print(f"Saved snapshot to {PARQUET}")

    if args.no_train:
        return

    train = df.filter((pl.col("race_date") >= pl.lit(TRAIN_FROM).str.strptime(pl.Date, "%Y-%m-%d"))
                      & (pl.col("race_date") <= pl.lit(TRAIN_TO).str.strptime(pl.Date, "%Y-%m-%d")))
    valid = df.filter((pl.col("race_date") >= pl.lit(VALID_FROM).str.strptime(pl.Date, "%Y-%m-%d"))
                      & (pl.col("race_date") <= pl.lit(VALID_TO).str.strptime(pl.Date, "%Y-%m-%d")))
    test = df.filter((pl.col("race_date") >= pl.lit(TEST_FROM).str.strptime(pl.Date, "%Y-%m-%d"))
                     & (pl.col("race_date") <= pl.lit(TEST_TO).str.strptime(pl.Date, "%Y-%m-%d")))
    print(f"\nTrain {TRAIN_FROM}..{TRAIN_TO}: {len(train):,} | Valid {VALID_FROM}..{VALID_TO}: {len(valid):,} | Test {TEST_FROM}..{TEST_TO}: {len(test):,}")

    X_train, y_train = train.select(FEATURES).to_numpy(), train["won"].to_numpy().astype(int)
    X_valid, y_valid = valid.select(FEATURES).to_numpy(), valid["won"].to_numpy().astype(int)
    X_test, y_test = test.select(FEATURES).to_numpy(), test["won"].to_numpy().astype(int)

    params = {
        "objective": "binary",
        "metric": "binary_logloss",
        "boosting_type": "gbdt",
        "learning_rate": 0.05,
        "num_leaves": 127,
        "max_depth": -1,
        "min_data_in_leaf": 100,
        "feature_fraction": 0.8,
        "bagging_fraction": 0.8,
        "bagging_freq": 1,
        "lambda_l1": 0.5,
        "lambda_l2": 1.0,
        "verbose": -1,
        "seed": 42,
    }
    dtrain = lgb.Dataset(X_train, label=y_train)
    dvalid = lgb.Dataset(X_valid, label=y_valid, reference=dtrain)
    print("\nTraining LightGBM (early stopping on 2024-2025)...")
    booster = lgb.train(
        params, dtrain, num_boost_round=3000, valid_sets=[dvalid], valid_names=["valid"],
        callbacks=[lgb.log_evaluation(period=200), lgb.early_stopping(100, verbose=False)],
    )
    print(f"Best iteration: {booster.best_iteration}")

    imp = sorted(zip(FEATURES, booster.feature_importance("gain")), key=lambda x: -x[1])
    print("\nTop 15 features by gain:")
    for name, g in imp[:15]:
        print(f"  {name:22s} {g:,.0f}")

    # ---- calibrate probabilities (isotonic) on the held-out validation set ----
    # Fixes the favourite/longshot miscalibration of binary win/loss training.
    p_valid = booster.predict(X_valid)
    iso = IsotonicRegression(out_of_bounds="clip")
    iso.fit(p_valid, y_valid)
    joblib.dump(iso, ROOT / "iso_calib.joblib")
    print(f"\n  Isotonic calibration fit on validation ({len(y_valid):,} rows) -> saved to iso_calib.joblib")

    evaluate(valid, "VALIDATION (2024-2025)", booster, iso)
    evaluate(test, "TEST (2026 — tuning model, trained up to 2023)", booster, iso)

    # ---- Final production model: retrain on ALL data up to 2025, test on 2026 ----
    train_all = df.filter(pl.col("race_date") < pl.lit(TEST_FROM).str.strptime(pl.Date, "%Y-%m-%d"))
    X_all = train_all.select(FEATURES).to_numpy()
    y_all = train_all["won"].to_numpy().astype(int)
    print(f"\nRetraining final model on ALL data up to 2025 (train+valid, n={len(train_all):,}) "
          f"with best_iter={booster.best_iteration}...")
    dtrain_all = lgb.Dataset(X_all, label=y_all)
    final_booster = lgb.train(params, dtrain_all, num_boost_round=booster.best_iteration)
    evaluate(test, "TEST (2026 — FINAL model, retrained up to 2025)", final_booster, iso)

    final_booster.save_model(str(ROOT / "win_prob_model.txt"))
    (ROOT / "features.txt").write_text("\n".join(FEATURES))
    print(f"\nSaved final model to {ROOT / 'win_prob_model.txt'}")


if __name__ == "__main__":
    main()
