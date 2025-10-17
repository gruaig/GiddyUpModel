"""
Feature lists for training vs scoring.

CRITICAL: Training uses ABILITY_FEATURES only (no market data).
Market features are joined at SCORING time only.
"""

# ===== ABILITY FEATURES (for training) =====
# These predict horse ability independent of market pricing
ABILITY_FEATURES = [
    # Horse ability / speed
    "official_rating",
    "racing_post_rating",
    "best_rpr_last_3",
    
    # GiddyUp Performance Rating (GPR)
    "gpr",
    "gpr_minus_or",
    "gpr_minus_rpr",
    "gpr_sigma",
    
    # Recency & recent form
    "days_since_run",
    "last_pos",
    "avg_btn_last_3",
    
    # Career history
    "career_runs",
    "career_strike_rate",
    
    # Trainer long-term stats
    "trainer_sr_total",
    "trainer_wins_total",
    "trainer_runs_total",
    
    # Jockey long-term stats
    "jockey_sr_total",
    "jockey_wins_total",
    "jockey_runs_total",
    
    # Course/distance proficiency
    "runs_at_course",
    "wins_at_course",
    
    # Race context
    "field_size",
    "class_numeric",
    "is_flat",
    "is_aw",
    "dist_f",
    "draw",
    "age",
    "lbs",
]


# ===== MARKET FEATURES (for scoring only) =====
# These are NEVER used in training - only at prediction/betting time
MARKET_FEATURES = [
    "decimal_odds",
    "market_rank",
    "is_fav",
    "is_morning_fav",
    "price_drift_ratio",
    "price_movement",
    "price_spread",
    "volume_traded",
    "volume_per_runner",
]


def guard_no_market(cols: list[str]) -> None:
    """
    Ensure no market features leak into training.
    
    Raises:
        AssertionError: If any market features found in cols
        
    Example:
        >>> guard_no_market(["official_rating", "trainer_sr_total"])  # OK
        >>> guard_no_market(["official_rating", "decimal_odds"])  # FAILS!
    """
    bad = set(cols) & set(MARKET_FEATURES)
    if bad:
        raise AssertionError(
            f"🚨 LEAKAGE GUARD: Training features include market columns: {sorted(bad)}\n"
            f"   Market features should ONLY be used at scoring time, not training!"
        )
    print(f"✅ Leakage guard passed: No market features in training set")


# For clarity, export what should be used when
__all__ = [
    "ABILITY_FEATURES",
    "MARKET_FEATURES", 
    "guard_no_market",
]

