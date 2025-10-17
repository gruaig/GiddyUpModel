"""
Path B — Hybrid Market-Aware Scoring

Ability-only training + market-aware scoring with:
- Odds-band specific lambda blending
- Banded edge thresholds
- Target: 200-500 bets/year with 5-15% ROI
"""

import polars as pl
import numpy as np
from typing import Dict, Tuple
import yaml
from pathlib import Path


def load_config(config_path: str = "config/path_b_hybrid.yaml") -> dict:
    """Load Path B configuration."""
    with open(config_path) as f:
        return yaml.safe_load(f)


def get_odds_band(odds: float) -> str:
    """Assign odds to a band."""
    if odds < 3.0:
        return "1.5-3.0"
    elif odds < 5.0:
        return "3.0-5.0"
    elif odds < 8.0:
        return "5.0-8.0"
    elif odds < 12.0:
        return "8.0-12.0"
    else:
        return "12.0-999"


def get_lambda_for_odds(odds: float, config: dict) -> float:
    """
    Get blending lambda for given odds.
    Higher lambda = trust market more.
    """
    band = get_odds_band(odds)
    return config['lambda_by_odds'][band]


def get_edge_min_for_odds(odds: float, config: dict) -> float:
    """Get minimum edge threshold for odds band."""
    band = get_odds_band(odds)
    return config['edge_min_by_odds'][band]


def get_ev_min_for_odds(odds: float, config: dict) -> float:
    """Get minimum EV threshold for odds band."""
    band = get_odds_band(odds)
    return config['ev_min_by_odds'][band]


def calculate_vig_free_probs(race_odds: Dict[int, float]) -> Dict[int, float]:
    """
    Calculate vig-free probabilities for a race.
    
    Args:
        race_odds: {horse_id: decimal_odds}
    
    Returns:
        {horse_id: vig_free_probability}
    """
    # Calculate overround
    q_market = {h: 1.0/o for h, o in race_odds.items() if o > 1.0}
    overround = sum(q_market.values())
    
    # Normalize to vig-free
    q_vigfree = {h: q / overround for h, q in q_market.items()}
    
    return q_vigfree, overround


def blend_probabilities(p_model: float, q_vigfree: float, lambda_blend: float) -> float:
    """
    Blend model probability with vig-free market probability.
    
    p_blend = (1 - λ) * p_model + λ * q_vigfree
    
    Args:
        p_model: Model's probability
        q_vigfree: Vig-free market probability
        lambda_blend: Blending factor (0 = pure model, 1 = pure market)
    
    Returns:
        Blended probability
    """
    p_blend = (1 - lambda_blend) * p_model + lambda_blend * q_vigfree
    return max(0.001, min(0.999, p_blend))  # Clip to valid range


def calculate_edge_and_ev(
    p_blend: float,
    odds: float,
    q_vigfree: float,
    commission: float = 0.02
) -> Tuple[float, float, float]:
    """
    Calculate edge, EV, and full Kelly stake.
    
    Args:
        p_blend: Blended probability
        odds: Decimal odds
        q_vigfree: Vig-free market probability
        commission: Commission rate (default 0.02 = 2%)
    
    Returns:
        (edge_pp, ev, kelly_full)
    """
    # Edge in percentage points
    edge_pp = p_blend - q_vigfree
    
    # Expected value
    b = (odds - 1.0) * (1.0 - commission)
    ev = p_blend * b - (1.0 - p_blend)
    
    # Full Kelly fraction
    if b > 0:
        kelly_full = max(0.0, (p_blend * (b + 1.0) - 1.0) / b)
    else:
        kelly_full = 0.0
    
    return edge_pp, ev, kelly_full


def calculate_stake(
    kelly_full: float,
    odds: float,
    config: dict
) -> float:
    """
    Calculate stake in units using fractional Kelly with caps.
    
    Args:
        kelly_full: Full Kelly fraction
        odds: Decimal odds
        config: Configuration dict
    
    Returns:
        Stake in units
    """
    # Fractional Kelly
    kelly_frac = config['kelly']['fraction']
    stake = kelly_full * kelly_frac
    
    # Cap at maximum
    stake = min(stake, config['kelly']['cap_units'])
    
    # Additional favorite penalty
    if odds < config['favorite_caps']['odds_threshold']:
        stake = min(stake, config['favorite_caps']['max_stake_units'])
    
    return stake


def passes_gates(
    odds: float,
    edge_pp: float,
    ev: float,
    liquidity: float,
    config: dict
) -> Tuple[bool, str]:
    """
    Check if selection passes all gates.
    
    Returns:
        (passes: bool, reason: str)
    """
    # Odds range
    if odds < config['odds_caps']['min']:
        return False, f"odds {odds:.1f} < min {config['odds_caps']['min']}"
    
    if odds > config['odds_caps']['max']:
        return False, f"odds {odds:.1f} > max {config['odds_caps']['max']}"
    
    # Banded edge minimum
    edge_min = get_edge_min_for_odds(odds, config)
    if edge_pp < edge_min:
        return False, f"edge {edge_pp:.3f} < min {edge_min:.3f} for odds {odds:.1f}"
    
    # Banded EV minimum
    ev_min = get_ev_min_for_odds(odds, config)
    if ev < ev_min:
        return False, f"ev {ev:.3f} < min {ev_min:.3f} for odds {odds:.1f}"
    
    # Liquidity
    if liquidity < config['liquidity']['min_gbp']:
        return False, f"liquidity £{liquidity:.0f} < min £{config['liquidity']['min_gbp']}"
    
    return True, "PASS"


def score_hybrid(
    df: pl.DataFrame,
    p_model: np.ndarray,
    config: dict
) -> pl.DataFrame:
    """
    Apply Path B hybrid scoring to a dataset.
    
    Args:
        df: DataFrame with race_id, horse_id, decimal_odds, market data
        p_model: Model predictions (numpy array, same order as df)
        config: Path B configuration
    
    Returns:
        DataFrame with all scoring columns and gate results
    """
    # Add model predictions
    df = df.with_columns(pl.Series("p_model", p_model))
    
    # Calculate vig-free probabilities per race
    df = df.with_columns([
        (1.0 / pl.col("decimal_odds")).alias("q_market")
    ])
    
    df = df.with_columns([
        pl.col("q_market").sum().over("race_id").alias("overround")
    ])
    
    df = df.with_columns([
        (pl.col("q_market") / pl.col("overround")).alias("q_vigfree")
    ])
    
    # Assign odds bands
    df = df.with_columns([
        pl.when(pl.col("decimal_odds") < 3.0).then(pl.lit("1.5-3.0"))
        .when(pl.col("decimal_odds") < 5.0).then(pl.lit("3.0-5.0"))
        .when(pl.col("decimal_odds") < 8.0).then(pl.lit("5.0-8.0"))
        .when(pl.col("decimal_odds") < 12.0).then(pl.lit("8.0-12.0"))
        .otherwise(pl.lit("12.0-999"))
        .alias("odds_band")
    ])
    
    # Get lambda for each row
    lambda_map = config['lambda_by_odds']
    df = df.with_columns([
        pl.when(pl.col("odds_band") == "1.5-3.0").then(pl.lit(lambda_map["1.5-3.0"]))
        .when(pl.col("odds_band") == "3.0-5.0").then(pl.lit(lambda_map["3.0-5.0"]))
        .when(pl.col("odds_band") == "5.0-8.0").then(pl.lit(lambda_map["5.0-8.0"]))
        .when(pl.col("odds_band") == "8.0-12.0").then(pl.lit(lambda_map["8.0-12.0"]))
        .otherwise(pl.lit(lambda_map["12.0-999"]))
        .alias("lambda_blend")
    ])
    
    # Blend probabilities
    df = df.with_columns([
        ((1.0 - pl.col("lambda_blend")) * pl.col("p_model") + 
         pl.col("lambda_blend") * pl.col("q_vigfree"))
        .alias("p_blend")
    ])
    
    # Clip to valid range
    df = df.with_columns([
        pl.col("p_blend").clip(0.001, 0.999).alias("p_blend")
    ])
    
    # Calculate edge
    df = df.with_columns([
        (pl.col("p_blend") - pl.col("q_vigfree")).alias("edge_pp")
    ])
    
    # Calculate EV
    commission = config['market']['commission']
    df = df.with_columns([
        (pl.col("p_blend") * (pl.col("decimal_odds") - 1.0) * (1.0 - commission) - 
         (1.0 - pl.col("p_blend")))
        .alias("ev")
    ])
    
    # Calculate Kelly
    df = df.with_columns([
        pl.when(pl.col("decimal_odds") > 1.0)
        .then(
            pl.max_horizontal(
                0.0,
                (pl.col("p_blend") * (pl.col("decimal_odds") - commission * (pl.col("decimal_odds") - 1.0)) - 1.0) /
                ((pl.col("decimal_odds") - 1.0) * (1.0 - commission))
            )
        )
        .otherwise(0.0)
        .alias("kelly_full")
    ])
    
    # Calculate stake
    kelly_frac = config['kelly']['fraction']
    kelly_cap = config['kelly']['cap_units']
    fav_cap = config['favorite_caps']['max_stake_units']
    fav_threshold = config['favorite_caps']['odds_threshold']
    
    df = df.with_columns([
        pl.min_horizontal(
            pl.col("kelly_full") * kelly_frac,
            pl.lit(kelly_cap)
        ).alias("stake_units")
    ])
    
    # Apply favorite cap
    df = df.with_columns([
        pl.when(pl.col("decimal_odds") < fav_threshold)
        .then(pl.min_horizontal(pl.col("stake_units"), pl.lit(fav_cap)))
        .otherwise(pl.col("stake_units"))
        .alias("stake_units")
    ])
    
    # Get edge and EV minimums for each band
    edge_map = config['edge_min_by_odds']
    ev_map = config['ev_min_by_odds']
    
    df = df.with_columns([
        pl.when(pl.col("odds_band") == "1.5-3.0").then(pl.lit(edge_map["1.5-3.0"]))
        .when(pl.col("odds_band") == "3.0-5.0").then(pl.lit(edge_map["3.0-5.0"]))
        .when(pl.col("odds_band") == "5.0-8.0").then(pl.lit(edge_map["5.0-8.0"]))
        .when(pl.col("odds_band") == "8.0-12.0").then(pl.lit(edge_map["8.0-12.0"]))
        .otherwise(pl.lit(edge_map["12.0-999"]))
        .alias("edge_min")
    ])
    
    df = df.with_columns([
        pl.when(pl.col("odds_band") == "1.5-3.0").then(pl.lit(ev_map["1.5-3.0"]))
        .when(pl.col("odds_band") == "3.0-5.0").then(pl.lit(ev_map["3.0-5.0"]))
        .when(pl.col("odds_band") == "5.0-8.0").then(pl.lit(ev_map["5.0-8.0"]))
        .when(pl.col("odds_band") == "8.0-12.0").then(pl.lit(ev_map["8.0-12.0"]))
        .otherwise(pl.lit(ev_map["12.0-999"]))
        .alias("ev_min")
    ])
    
    # Apply gates
    odds_min = config['odds_caps']['min']
    odds_max = config['odds_caps']['max']
    
    df = df.with_columns([
        (
            (pl.col("decimal_odds") >= odds_min) &
            (pl.col("decimal_odds") <= odds_max) &
            (pl.col("edge_pp") >= pl.col("edge_min")) &
            (pl.col("ev") >= pl.col("ev_min"))
        ).alias("passes_gates")
    ])
    
    # Filter to passing selections
    df_passing = df.filter(pl.col("passes_gates"))
    
    # Top-1 per race by edge
    if config['selection']['top_n_per_race'] == 1:
        df_passing = df_passing.with_columns([
            pl.col("edge_pp").rank("ordinal", descending=True).over("race_id").alias("rank_in_race")
        ])
        df_passing = df_passing.filter(pl.col("rank_in_race") == 1)
    
    return df_passing


def format_selection_summary(df: pl.DataFrame) -> str:
    """Format a human-readable summary of selections."""
    if len(df) == 0:
        return "No selections passed gates."
    
    summary = []
    summary.append(f"\n{'='*80}")
    summary.append(f"PATH B SELECTIONS: {len(df)} bets")
    summary.append(f"{'='*80}\n")
    
    for row in df.iter_rows(named=True):
        summary.append(f"🎯 {row.get('horse_name', 'Unknown')} @ {row['decimal_odds']:.1f} odds")
        summary.append(f"   Band: {row['odds_band']} | Lambda: {row['lambda_blend']:.2f}")
        summary.append(f"   Model: {row['p_model']*100:.1f}% → Blend: {row['p_blend']*100:.1f}% (Market: {row['q_vigfree']*100:.1f}%)")
        summary.append(f"   Edge: +{row['edge_pp']*100:.1f}pp | EV: +{row['ev']*100:.1f}% | Stake: {row['stake_units']:.3f}u")
        summary.append("")
    
    # Summary stats
    summary.append(f"{'─'*80}")
    summary.append(f"Total bets: {len(df)}")
    summary.append(f"Avg odds: {df['decimal_odds'].mean():.2f}")
    summary.append(f"Avg edge: +{df['edge_pp'].mean()*100:.1f}pp")
    summary.append(f"Avg EV: +{df['ev'].mean()*100:.1f}%")
    summary.append(f"Total stake: {df['stake_units'].sum():.3f} units")
    summary.append(f"{'='*80}\n")
    
    return "\n".join(summary)

