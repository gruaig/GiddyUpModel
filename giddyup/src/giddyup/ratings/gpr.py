"""
GiddyUp Performance Rating (GPR) implementation.

Builds a pounds-scale performance rating for horses based on:
- Beaten lengths adjusted by distance
- Weight carried
- Class of race
- Context-debiased by course/going/distance
- Recency-weighted with exponential decay
- Calibrated to Official Rating scale
"""

import polars as pl
import numpy as np
from typing import Tuple
import json


def make_distance_band(dist_f: float) -> str:
    """
    Categorize distance into bands.
    
    Args:
        dist_f: Distance in furlongs
        
    Returns:
        Distance band string
        
    Example:
        >>> make_distance_band(6.0)
        '5-6f'
        >>> make_distance_band(10.0)
        '10-12f'
    """
    if dist_f < 5:
        return '<5f'
    elif dist_f <= 6:
        return '5-6f'
    elif dist_f <= 9:
        return '7-9f'
    elif dist_f <= 12:
        return '10-12f'
    else:
        return '12f+'


def lbs_per_length(dist_band: str) -> float:
    """
    Get pounds per length for distance band.
    
    Rule of thumb for how much weight equals one length.
    
    Args:
        dist_band: Distance band from make_distance_band()
        
    Returns:
        Pounds per length
        
    Example:
        >>> lbs_per_length('5-6f')
        3.8
        >>> lbs_per_length('12f+')
        2.0
    """
    mapping = {
        '<5f': 4.0,
        '5-6f': 3.8,
        '7-9f': 3.0,
        '10-12f': 2.5,
        '12f+': 2.0,
    }
    return mapping.get(dist_band, 3.0)  # Default 3.0


def make_going_band(going: str) -> str:
    """
    Simplify going descriptions into bands.
    
    Args:
        going: Going description
        
    Returns:
        Going band
    """
    if not going:
        return 'unknown'
    
    going_lower = str(going).lower()
    
    if 'heavy' in going_lower:
        return 'heavy'
    elif 'soft' in going_lower:
        return 'soft'
    elif 'good' in going_lower:
        return 'good'
    elif 'firm' in going_lower:
        return 'firm'
    else:
        return 'unknown'


def get_class_bonus(race_class: str) -> float:
    """
    Get class bonus in pounds.
    
    Higher class races get bonus to account for tougher competition.
    
    Args:
        race_class: Class string (e.g., "(Class 1)", "Group 1")
        
    Returns:
        Bonus in pounds
    """
    if not race_class:
        return 0.0
    
    class_str = str(race_class).lower()
    
    # Group races
    if 'group 1' in class_str or 'grade 1' in class_str:
        return 8.0
    elif 'group 2' in class_str or 'grade 2' in class_str:
        return 6.0
    elif 'group 3' in class_str or 'grade 3' in class_str:
        return 4.0
    elif 'listed' in class_str:
        return 3.0
    
    # Class system
    if 'class 1' in class_str:
        return 5.0
    elif 'class 2' in class_str:
        return 3.0
    elif 'class 3' in class_str:
        return 2.0
    elif 'class 4' in class_str:
        return 1.0
    elif 'class 5' in class_str:
        return 0.5
    else:
        return 0.0


def compute_gpr(
    df_runs: pl.DataFrame,
    as_of_date: str = None,
    half_life_days: float = 120.0,
    shrinkage_k: float = 4.0,
    prior_rating: float = 75.0,
) -> pl.DataFrame:
    """
    Compute GiddyUp Performance Rating (GPR) for each horse.
    
    Args:
        df_runs: DataFrame with historical runs (must have columns:
                 horse_id, race_date, dist_f, btn (beaten_lengths), lbs, 
                 course_id, going, class, pos_num)
        as_of_date: Calculate GPR as of this date (only use runs before this)
        half_life_days: Half-life for exponential decay (default 120 days)
        shrinkage_k: Shrinkage parameter (default 4.0)
        prior_rating: Prior mean rating (default 75.0)
        
    Returns:
        DataFrame with horse_id, gpr, gpr_sigma, n_runs
    """
    
    # Filter to races before as_of_date if specified
    if as_of_date:
        df_runs = df_runs.filter(
            pl.col("race_date") < pl.lit(as_of_date).str.strptime(pl.Date, "%Y-%m-%d")
        )
    
    print(f"   Computing GPR from {len(df_runs):,} historical runs...")
    
    # ===== 1. Add distance and going bands =====
    df_runs = df_runs.with_columns([
        pl.col("dist_f").map_elements(make_distance_band, return_dtype=pl.Utf8).alias("dist_band"),
        pl.col("going").map_elements(make_going_band, return_dtype=pl.Utf8).alias("going_band"),
        pl.col("class").map_elements(get_class_bonus, return_dtype=pl.Float64).alias("class_bonus"),
    ])
    
    # Add lbs per length
    df_runs = df_runs.with_columns([
        pl.col("dist_band").map_elements(lbs_per_length, return_dtype=pl.Float64).alias("lbs_per_len"),
    ])
    
    # ===== 2. Calculate raw run rating =====
    
    # Get race winner's beaten lengths (0 for winner)
    # For each race, find minimum btn (winner has btn=0 or close to it)
    race_winner_stats = df_runs.group_by("race_id").agg([
        pl.col("btn").min().alias("race_min_btn"),
    ])
    
    df_runs = df_runs.join(race_winner_stats, on="race_id")
    
    # Calculate standard lbs for the race (median or mode)
    race_std_lbs = df_runs.group_by("race_id").agg([
        pl.col("lbs").median().alias("race_std_lbs"),
    ])
    
    df_runs = df_runs.join(race_std_lbs, on="race_id")
    
    # Components of rating
    df_runs = df_runs.with_columns([
        # Lengths component (closer to winner = higher rating)
        # Winner at 0 btn gets full credit, each length back costs lbs_per_len
        ((pl.col("race_min_btn") - pl.col("btn").fill_null(10)) * pl.col("lbs_per_len"))
            .alias("len_component"),
        
        # Weight component (carrying more weight = better performance)
        # Subtract because higher lbs carried makes the performance better
        (pl.col("lbs").fill_null(pl.col("race_std_lbs")) - pl.col("race_std_lbs"))
            .alias("wt_component"),
    ])
    
    # Raw run rating
    df_runs = df_runs.with_columns([
        (pl.col("len_component") - pl.col("wt_component") + pl.col("class_bonus"))
            .alias("run_rating_raw")
    ])
    
    # ===== 3. Context de-bias =====
    print(f"   De-biasing by course/going/distance context...")
    
    # Calculate mean rating per context
    context_means = df_runs.group_by(["course_id", "going_band", "dist_band"]).agg([
        pl.col("run_rating_raw").mean().alias("ctx_mean"),
    ])
    
    df_runs = df_runs.join(context_means, on=["course_id", "going_band", "dist_band"], how="left")
    
    # Debiased rating
    df_runs = df_runs.with_columns([
        (pl.col("run_rating_raw") - pl.col("ctx_mean").fill_null(0))
            .alias("run_rating_ctx")
    ])
    
    # ===== 4. Recency weighting =====
    print(f"   Applying recency weighting (half-life: {half_life_days} days)...")
    
    # Calculate days back from most recent run per horse
    df_runs = df_runs.with_columns([
        (pl.col("race_date").max().over("horse_id") - pl.col("race_date")).dt.total_days()
            .alias("days_back")
    ])
    
    # Exponential decay weight
    decay_factor = np.log(2) / half_life_days
    df_runs = df_runs.with_columns([
        (pl.lit(-decay_factor) * pl.col("days_back")).exp().alias("recency_weight")
    ])
    
    # ===== 5. Compute weighted average per horse =====
    print(f"   Computing weighted average per horse...")
    
    horse_ratings = df_runs.group_by("horse_id").agg([
        # Weighted mean
        (pl.col("run_rating_ctx") * pl.col("recency_weight")).sum().alias("weighted_sum"),
        pl.col("recency_weight").sum().alias("weight_sum"),
        
        # For uncertainty
        pl.col("run_rating_ctx").std().alias("rating_std"),
        pl.col("run_rating_ctx").count().alias("n_runs"),
    ])
    
    horse_ratings = horse_ratings.with_columns([
        (pl.col("weighted_sum") / pl.col("weight_sum")).alias("weighted_mean")
    ])
    
    # ===== 6. Shrinkage toward prior =====
    print(f"   Applying shrinkage (k={shrinkage_k}, prior={prior_rating})...")
    
    horse_ratings = horse_ratings.with_columns([
        # Empirical Bayes shrinkage
        ((pl.col("n_runs") / (pl.col("n_runs") + shrinkage_k)) * pl.col("weighted_mean") +
         (shrinkage_k / (pl.col("n_runs") + shrinkage_k)) * prior_rating)
            .alias("gpr_raw")
    ])
    
    # ===== 7. Calibrate to OR scale =====
    print(f"   Calibrating to Official Rating scale...")
    
    # For now, use simple linear scaling
    # In production, fit a*gpr_raw + b on training data where OR is available
    # Here we'll use approximate calibration
    
    # GPR raw is roughly centered around 0 (debiased)
    # OR scale is typically 50-130
    # Simple mapping: gpr_cal = gpr_raw + 75 (shifts to OR range)
    
    horse_ratings = horse_ratings.with_columns([
        (pl.col("gpr_raw") + prior_rating).alias("gpr"),
        pl.col("rating_std").fill_null(10.0).alias("gpr_sigma"),
    ])
    
    # Select final columns
    result = horse_ratings.select([
        "horse_id",
        "gpr",
        "gpr_sigma",
        "n_runs",
    ])
    
    print(f"   ✅ GPR computed for {len(result):,} horses")
    
    return result


def add_gpr_to_dataset(
    df: pl.DataFrame,
    gpr_df: pl.DataFrame,
    or_col: str = "official_rating",
    rpr_col: str = "racing_post_rating"
) -> pl.DataFrame:
    """
    Add GPR and delta features to dataset.
    
    Args:
        df: Main dataset
        gpr_df: GPR ratings per horse
        or_col: Official rating column name
        rpr_col: Racing Post rating column name
        
    Returns:
        DataFrame with GPR, gpr_minus_or, gpr_minus_rpr columns added
    """
    # Join GPR
    df = df.join(gpr_df, on="horse_id", how="left")
    
    # Fill nulls for horses with no history
    df = df.with_columns([
        pl.col("gpr").fill_null(75.0),  # Default prior
        pl.col("gpr_sigma").fill_null(15.0),  # High uncertainty
        pl.col("n_runs").fill_null(0),
    ])
    
    # Calculate deltas
    df = df.with_columns([
        (pl.col("gpr") - pl.col(or_col).fill_null(75.0)).alias("gpr_minus_or"),
        (pl.col("gpr") - pl.col(rpr_col).fill_null(75.0)).alias("gpr_minus_rpr"),
    ])
    
    return df


def fit_gpr_calibration(df_train: pl.DataFrame) -> dict:
    """
    Fit linear calibration to match Official Rating scale.
    
    Args:
        df_train: Training data with gpr_raw and official_rating
        
    Returns:
        dict with 'a' (slope) and 'b' (intercept)
        
    Example:
        >>> calib = fit_gpr_calibration(df_train)
        >>> gpr_calibrated = calib['a'] * gpr_raw + calib['b']
    """
    from sklearn.linear_model import LinearRegression
    
    # Filter to rows with both GPR and OR
    valid = df_train.filter(
        pl.col("gpr_raw").is_not_null() &
        pl.col("official_rating").is_not_null()
    )
    
    if len(valid) < 100:
        # Not enough data, return identity transform
        return {"a": 1.0, "b": 75.0}
    
    X = valid["gpr_raw"].to_numpy().reshape(-1, 1)
    y = valid["official_rating"].to_numpy()
    
    lr = LinearRegression()
    lr.fit(X, y)
    
    return {
        "a": float(lr.coef_[0]),
        "b": float(lr.intercept_),
        "n_samples": len(valid),
    }

