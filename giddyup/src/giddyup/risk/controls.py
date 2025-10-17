"""
Risk Control Framework

Implements betting risk controls:
- Per-race caps
- Daily stake limits
- Auto-stop on losses
- Liquidity checks
"""

import os
from typing import List, Dict
from datetime import datetime, date
import polars as pl


class RiskControls:
    """
    Risk control system for bet filtering and stake management.
    """
    
    def __init__(
        self,
        max_bets_per_race: int = 1,
        max_stake_per_race: float = 1.0,
        max_daily_stake: float = 20.0,
        max_daily_loss: float = 5.0,
        min_liquidity_required: float = 100.0,
    ):
        """
        Initialize risk controls.
        
        Args:
            max_bets_per_race: Maximum selections per race (default 1)
            max_stake_per_race: Max total stake per race in units (default 1.0)
            max_daily_stake: Max total stake per day in units (default 20.0)
            max_daily_loss: Stop trading if daily loss exceeds this (default 5.0)
            min_liquidity_required: Min GBP available at best back (default 100)
        """
        self.max_bets_per_race = max_bets_per_race
        self.max_stake_per_race = max_stake_per_race
        self.max_daily_stake = max_daily_stake
        self.max_daily_loss = max_daily_loss
        self.min_liquidity_required = min_liquidity_required
    
    def apply_per_race_cap(self, bets: pl.DataFrame) -> pl.DataFrame:
        """
        Apply per-race betting caps.
        
        Keep only top N bets per race by EV.
        If keeping multiple bets, scale stakes so total per race <= max_stake_per_race.
        
        Args:
            bets: DataFrame with bets
            
        Returns:
            Filtered DataFrame
        """
        if len(bets) == 0:
            return bets
        
        # Sort by race_id and EV descending
        bets = bets.sort(["race_id", "ev_after_commission"], descending=[False, True])
        
        # Keep top N per race
        bets = bets.with_columns([
            pl.col("race_id").cum_count().over("race_id").alias("rank_in_race")
        ])
        
        bets = bets.filter(pl.col("rank_in_race") <= self.max_bets_per_race)
        
        # Scale stakes if total per race exceeds cap
        race_totals = bets.group_by("race_id").agg([
            pl.col("stake_units").sum().alias("total_stake_per_race")
        ])
        
        bets = bets.join(race_totals, on="race_id")
        
        bets = bets.with_columns([
            pl.when(pl.col("total_stake_per_race") > self.max_stake_per_race)
            .then(pl.col("stake_units") * self.max_stake_per_race / pl.col("total_stake_per_race"))
            .otherwise(pl.col("stake_units"))
            .alias("stake_units")
        ])
        
        # Clean up
        bets = bets.drop(["rank_in_race", "total_stake_per_race"])
        
        return bets
    
    def check_daily_limits(self, today_bets: pl.DataFrame, today_date: date) -> Dict[str, bool]:
        """
        Check if daily limits are breached.
        
        Args:
            today_bets: Bets for today
            today_date: Target date
            
        Returns:
            dict with 'stake_ok', 'loss_ok', 'can_bet' flags
        """
        if len(today_bets) == 0:
            return {"stake_ok": True, "loss_ok": True, "can_bet": True, "reason": None}
        
        # Total stake
        total_stake = today_bets["stake_units"].sum()
        stake_ok = total_stake <= self.max_daily_stake
        
        # Total loss (requires settled bets with results)
        if "roi_bet" in today_bets.columns:
            total_pnl = today_bets["roi_bet"].sum()
            loss_ok = total_pnl >= -self.max_daily_loss
        else:
            # Can't check P&L without results
            loss_ok = True
        
        can_bet = stake_ok and loss_ok
        
        reason = None
        if not stake_ok:
            reason = f"Daily stake limit breached: {total_stake:.2f}/{self.max_daily_stake:.2f}"
        elif not loss_ok:
            reason = f"Daily loss limit breached: {total_pnl:.2f} < -{self.max_daily_loss:.2f}"
        
        return {
            "stake_ok": stake_ok,
            "loss_ok": loss_ok,
            "can_bet": can_bet,
            "reason": reason,
            "total_stake": total_stake,
            "total_pnl": total_pnl if "roi_bet" in today_bets.columns else None,
        }
    
    def check_liquidity(self, bets: pl.DataFrame, liquidity_col: str = "liquidity_gbp") -> pl.DataFrame:
        """
        Filter bets by liquidity requirements.
        
        Args:
            bets: DataFrame with liquidity info
            liquidity_col: Column name for liquidity in GBP
            
        Returns:
            Filtered DataFrame (only liquid bets)
        """
        if liquidity_col not in bets.columns:
            # No liquidity data, assume all OK
            return bets.with_columns([pl.lit(True).alias("liquidity_ok")])
        
        # Filter
        bets = bets.with_columns([
            (pl.col(liquidity_col) >= self.min_liquidity_required).alias("liquidity_ok")
        ])
        
        bets = bets.filter(pl.col("liquidity_ok"))
        
        return bets
    
    def apply_all_controls(
        self,
        bets: pl.DataFrame,
        today_settled_bets: pl.DataFrame = None,
        today_date: date = None
    ) -> tuple[pl.DataFrame, Dict]:
        """
        Apply all risk controls.
        
        Args:
            bets: New bets to filter
            today_settled_bets: Already settled bets from today (for daily limit check)
            today_date: Current date
            
        Returns:
            (filtered_bets, control_status)
        """
        if today_date is None:
            today_date = datetime.now().date()
        
        # 1. Per-race cap
        bets = self.apply_per_race_cap(bets)
        
        # 2. Liquidity
        bets = self.check_liquidity(bets)
        
        # 3. Daily limits (check before adding new bets)
        if today_settled_bets is not None and len(today_settled_bets) > 0:
            combined = pl.concat([today_settled_bets, bets])
        else:
            combined = bets
        
        daily_status = self.check_daily_limits(combined, today_date)
        
        if not daily_status["can_bet"]:
            print(f"⚠️  RISK CONTROL: Trading halted - {daily_status['reason']}")
            return pl.DataFrame(), daily_status
        
        # 4. Scale down if approaching daily limit
        remaining_capacity = self.max_daily_stake - daily_status["total_stake"]
        new_stake_total = bets["stake_units"].sum()
        
        if new_stake_total > remaining_capacity:
            print(f"⚠️  Scaling down stakes to fit daily limit")
            scale_factor = remaining_capacity / new_stake_total
            bets = bets.with_columns([
                (pl.col("stake_units") * scale_factor).alias("stake_units")
            ])
        
        return bets, daily_status


def load_risk_controls_from_env() -> RiskControls:
    """
    Load risk control parameters from environment variables.
    
    Returns:
        RiskControls instance
    """
    return RiskControls(
        max_bets_per_race=int(os.getenv("MAX_BETS_PER_RACE", "1")),
        max_stake_per_race=float(os.getenv("MAX_STAKE_PER_RACE", "1.0")),
        max_daily_stake=float(os.getenv("MAX_DAILY_STAKE", "20.0")),
        max_daily_loss=float(os.getenv("MAX_DAILY_LOSS", "5.0")),
        min_liquidity_required=float(os.getenv("MIN_LIQUIDITY_GBP", "100.0")),
    )

