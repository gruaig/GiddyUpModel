"""
Hybrid Model Scorer

Combines:
- Path A ability-only model for predictions
- Market features for intelligent filtering
- Adaptive blending based on market context
"""

import numpy as np
import polars as pl
from typing import Dict, Tuple


# ===== Configuration =====
# V3: Focus on high-conviction disagreements only

# Disagreement thresholds (V3: much higher)
MIN_DISAGREEMENT_RATIO = 2.50  # Model must be 150%+ higher than market
MIN_EDGE_ABSOLUTE = 0.08       # Minimum 8pp edge

# Market rank filters (V3: mid-field only)
MAX_RANK = 6                    # Only ranks 3-6
MIN_RANK = 3                    # Don't bet favorite or 2nd favorite

# Odds range (V3: sweet spot only)
ODDS_MIN = 7.0                  # Focus on 7-12 range
ODDS_MAX = 12.0

# Market quality
MAX_OVERROUND = 1.18            # Very competitive markets only
MIN_OVERROUND = 1.01            # Skip suspicious markets

# EV after penalties (V3: much higher)
MIN_EV_ADJUSTED = 0.05          # 5% minimum

# Staking
KELLY_FRACTION = 0.10
MAX_STAKE = 0.3
COMMISSION = 0.02


# ===== Helper Functions =====

def logit(x):
    """Convert probability to log-odds"""
    x = np.clip(x, 0.001, 0.999)
    return np.log(x / (1 - x))


def invlogit(z):
    """Convert log-odds to probability"""
    return 1 / (1 + np.exp(-z))


def blend_to_market(p_model: float, q_market: float, lambda_blend: float) -> float:
    """
    Blend model probability towards market in log-odds space.
    
    Args:
        p_model: Model probability
        q_market: Market vig-free probability
        lambda_blend: Blending parameter (0=pure model, 1=pure market)
        
    Returns:
        Blended probability
    """
    z_model = logit(p_model)
    z_market = logit(q_market)
    z_blend = (1 - lambda_blend) * z_model + lambda_blend * z_market
    return float(invlogit(z_blend))


def get_adaptive_lambda(
    odds: float,
    market_rank: int,
    overround: float
) -> float:
    """
    Calculate adaptive blending parameter based on market context.
    
    Trust market MORE when:
    - Favorite or 2nd favorite (heavy money, efficient)
    - Low overround (competitive market)
    - Very short odds (< 4.0)
    
    Trust model MORE when:
    - Mid-field horse (rank 4-8)
    - Higher overround (less competitive)
    - Mid-range odds (6-12)
    
    Args:
        odds: Decimal odds
        market_rank: Market position (1=favorite)
        overround: Race overround
        
    Returns:
        Lambda blending parameter [0.1, 0.7]
    """
    
    # Base lambda by odds
    if odds < 5.0:
        lam = 0.40  # Trust market more on short prices
    elif odds < 8.0:
        lam = 0.30
    elif odds < 12.0:
        lam = 0.20  # Trust model most in sweet spot
    else:
        lam = 0.45  # Trust market more on longshots
    
    # Adjust for market rank
    if market_rank == 1:  # Favorite
        lam += 0.25  # Market very efficient
    elif market_rank == 2:  # 2nd favorite
        lam += 0.15  # Market efficient
    elif market_rank >= 6:  # Outsider
        lam -= 0.10  # Market less efficient
    
    # Adjust for market competitiveness
    if overround < 1.10:  # Very competitive
        lam += 0.10
    elif overround > 1.20:  # Less competitive
        lam -= 0.05
    
    # Clamp to reasonable range
    return max(0.10, min(0.70, lam))


def calculate_ev_adjusted(
    p_blend: float,
    odds: float,
    market_rank: int,
    commission: float = COMMISSION
) -> float:
    """
    Calculate EV with favorite penalty.
    
    Args:
        p_blend: Blended probability
        odds: Decimal odds
        market_rank: Market rank
        commission: Commission rate
        
    Returns:
        Adjusted expected value
    """
    
    # Base EV
    if odds <= 1.0:
        return -1.0
    
    b = (odds - 1.0) * (1.0 - commission)
    ev_base = p_blend * b - (1.0 - p_blend)
    
    # Apply favorite penalty
    if market_rank == 1:
        ev_adjusted = ev_base * 0.3  # Heavy penalty
    elif market_rank == 2:
        ev_adjusted = ev_base * 0.6  # Moderate penalty
    else:
        ev_adjusted = ev_base  # No penalty
    
    return ev_adjusted


def passes_hybrid_gates(row: Dict) -> Tuple[bool, str]:
    """
    Check if a row passes all hybrid selection gates.
    
    Args:
        row: Dictionary with all required fields
        
    Returns:
        (passes, reason) tuple
    """
    
    # Extract values
    p_model = row.get("p_model")
    q_vigfree = row.get("q_vigfree")
    odds = row.get("decimal_odds")
    market_rank = row.get("market_rank")
    overround = row.get("overround")
    edge = row.get("edge_absolute")
    disagreement = row.get("disagreement_ratio")
    ev_adj = row.get("ev_adjusted")
    
    # Gate 1: Disagreement ratio
    if disagreement < MIN_DISAGREEMENT_RATIO:
        return False, f"Low disagreement: {disagreement:.2f} < {MIN_DISAGREEMENT_RATIO}"
    
    # Gate 2: Market rank
    if market_rank < MIN_RANK:
        return False, f"Too favored: rank {market_rank} < {MIN_RANK}"
    
    if market_rank > MAX_RANK:
        return False, f"Too unfavored: rank {market_rank} > {MAX_RANK}"
    
    # Gate 3: Absolute edge
    if edge < MIN_EDGE_ABSOLUTE:
        return False, f"Low edge: {edge:.3f} < {MIN_EDGE_ABSOLUTE}"
    
    # Gate 4: Odds range
    if odds < ODDS_MIN:
        return False, f"Odds too low: {odds:.2f} < {ODDS_MIN}"
    
    if odds > ODDS_MAX:
        return False, f"Odds too high: {odds:.2f} > {ODDS_MAX}"
    
    # Gate 5: Market quality
    if overround > MAX_OVERROUND:
        return False, f"Uncompetitive market: {overround:.3f} > {MAX_OVERROUND}"
    
    if overround < MIN_OVERROUND:
        return False, f"Suspicious market: {overround:.3f} < {MIN_OVERROUND}"
    
    # Gate 6: Adjusted EV
    if ev_adj < MIN_EV_ADJUSTED:
        return False, f"Low EV: {ev_adj:.3f} < {MIN_EV_ADJUSTED}"
    
    # All gates passed
    return True, "PASS"


def score_hybrid(
    df: pl.DataFrame,
    p_model: np.ndarray
) -> pl.DataFrame:
    """
    Apply hybrid scoring logic to dataframe.
    
    Args:
        df: DataFrame with ability features AND market features
        p_model: Model predictions (ability-only)
        
    Returns:
        DataFrame with hybrid scores and selection flags
    """
    
    # Add model predictions
    df = df.with_columns(pl.Series("p_model", p_model))
    
    # Calculate disagreement metrics
    df = df.with_columns([
        (pl.col("p_model") / pl.col("q_vigfree")).alias("disagreement_ratio"),
        (pl.col("p_model") - pl.col("q_vigfree")).alias("edge_absolute"),
    ])
    
    # Calculate adaptive lambda
    df_pd = df.to_pandas()
    
    df_pd["lambda"] = df_pd.apply(
        lambda r: get_adaptive_lambda(
            r["decimal_odds"],
            r["market_rank"],
            r["overround"]
        ),
        axis=1
    )
    
    # Blend probabilities
    df_pd["p_blend"] = df_pd.apply(
        lambda r: blend_to_market(r["p_model"], r["q_vigfree"], r["lambda"]),
        axis=1
    )
    
    # Calculate adjusted EV
    df_pd["ev_adjusted"] = df_pd.apply(
        lambda r: calculate_ev_adjusted(
            r["p_blend"],
            r["decimal_odds"],
            r["market_rank"]
        ),
        axis=1
    )
    
    # Check gates
    df_pd["passes_gates"], df_pd["gate_reason"] = zip(*df_pd.apply(
        lambda r: passes_hybrid_gates(r.to_dict()),
        axis=1
    ))
    
    # Back to polars
    df = pl.from_pandas(df_pd)
    
    return df


def select_top_per_race(df: pl.DataFrame) -> pl.DataFrame:
    """
    Select top-1 bet per race by edge.
    
    Args:
        df: DataFrame with passes_gates flag
        
    Returns:
        Filtered DataFrame (one per race max)
    """
    
    # Filter to passing horses
    candidates = df.filter(pl.col("passes_gates") == True)
    
    if len(candidates) == 0:
        return candidates
    
    # Convert to pandas for groupby operations
    candidates_pd = candidates.to_pandas()
    
    # Sort by race_id and edge (descending)
    candidates_pd = candidates_pd.sort_values(
        ["race_id", "edge_absolute"],
        ascending=[True, False]
    )
    
    # Keep top-1 per race
    selected = candidates_pd.groupby("race_id", as_index=False).head(1)
    
    return pl.from_pandas(selected)


def calculate_stake(p_blend: float, odds: float) -> float:
    """
    Calculate Kelly stake with conservative fraction.
    
    Args:
        p_blend: Blended probability
        odds: Decimal odds
        
    Returns:
        Stake in units
    """
    
    if odds <= 1.0:
        return 0.0
    
    b = (odds - 1.0) * (1.0 - COMMISSION)
    
    if b <= 0:
        return 0.0
    
    # Full Kelly
    kelly_full = (p_blend * (b + 1.0) - 1.0) / b
    kelly_full = max(0.0, min(1.0, kelly_full))
    
    # Fractional Kelly
    stake = KELLY_FRACTION * kelly_full
    
    # Cap
    return min(stake, MAX_STAKE)

