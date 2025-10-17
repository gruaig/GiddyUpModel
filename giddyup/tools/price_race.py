"""
Price a Single Race Tool

Takes a specific race (date, course, time) with current market prices,
then uses the trained model to calculate fair odds and identify value.

Usage:
    python price_race.py --date 2025-10-18 --course "Ascot" --time "14:30"
    python price_race.py --race-id 12345
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import os
import argparse
from datetime import datetime
import polars as pl
import mlflow
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

from giddyup.data.build import build_training_data
from giddyup.data.feature_lists import ABILITY_FEATURES
from giddyup.price.value import fair_odds, ev_win

load_dotenv()

PG_DSN = os.getenv("PG_DSN")
engine = create_engine(PG_DSN, pool_pre_ping=True)

COMMISSION = float(os.getenv("COMMISSION", "0.02"))


def find_race(date_str: str = None, course_name: str = None, time_str: str = None, race_id: int = None):
    """
    Find race_id by date/course/time or use provided race_id.
    
    Args:
        date_str: Race date (YYYY-MM-DD)
        course_name: Course name (e.g., "Ascot")
        time_str: Off time (HH:MM)
        race_id: Direct race ID
        
    Returns:
        race_id, race info dict
    """
    if race_id:
        sql = """
        SELECT 
            r.race_id,
            r.race_date,
            r.off_time,
            c.course_name,
            r.class,
            r.dist_f
        FROM racing.races r
        LEFT JOIN racing.courses c USING (course_id)
        WHERE r.race_id = :race_id
        """
        with engine.begin() as cx:
            result = cx.execute(text(sql), {"race_id": race_id}).fetchone()
        
        if not result:
            raise ValueError(f"Race ID {race_id} not found")
        
        return result[0], {
            "race_id": result[0],
            "race_date": result[1],
            "off_time": result[2],
            "course_name": result[3],
            "class": result[4],
            "dist_f": result[5],
        }
    
    else:
        # Find by date/course/time
        sql = """
        SELECT 
            r.race_id,
            r.race_date,
            r.off_time,
            c.course_name,
            r.class,
            r.dist_f
        FROM racing.races r
        LEFT JOIN racing.courses c USING (course_id)
        WHERE DATE(r.race_date) = DATE(:date_str)
        AND LOWER(c.course_name) LIKE LOWER(:course_pattern)
        AND r.off_time::time = :time_str::time
        LIMIT 1
        """
        
        with engine.begin() as cx:
            result = cx.execute(text(sql), {
                "date_str": date_str,
                "course_pattern": f"%{course_name}%",
                "time_str": time_str
            }).fetchone()
        
        if not result:
            raise ValueError(f"Race not found: {date_str} {course_name} {time_str}")
        
        return result[0], {
            "race_id": result[0],
            "race_date": result[1],
            "off_time": result[2],
            "course_name": result[3],
            "class": result[4],
            "dist_f": result[5],
        }


def get_race_runners(race_id: int) -> pl.DataFrame:
    """
    Get ability features for all runners in a race.
    
    Args:
        race_id: Race ID
        
    Returns:
        DataFrame with runners and ability features
    """
    print(f"\n📊 Loading race data for race_id={race_id}...")
    
    # Get race date
    sql = "SELECT race_date FROM racing.races WHERE race_id = :race_id"
    with engine.begin() as cx:
        race_date = cx.execute(text(sql), {"race_id": race_id}).scalar()
    
    if not race_date:
        raise ValueError(f"Race {race_id} not found")
    
    race_date_str = race_date.strftime("%Y-%m-%d")
    
    # Build features
    df = build_training_data(
        date_from=race_date_str,
        date_to=race_date_str,
        output_path=None
    )
    
    # Filter to this race
    df = df.filter(pl.col("race_id") == race_id)
    
    if len(df) == 0:
        raise ValueError(f"No runners found for race {race_id}")
    
    print(f"   ✅ Loaded {len(df)} runners")
    
    return df


def get_current_prices(race_id: int) -> pl.DataFrame:
    """
    Get latest market prices for race runners.
    
    Args:
        race_id: Race ID
        
    Returns:
        DataFrame with horse_id, decimal_odds, source
    """
    print(f"\n💰 Fetching current market prices...")
    
    # Get most recent snapshot for this race
    sql = """
    WITH latest AS (
        SELECT 
            horse_id,
            decimal_odds,
            source,
            snapped_at,
            ROW_NUMBER() OVER (PARTITION BY horse_id ORDER BY snapped_at DESC) AS rn
        FROM market.price_snapshots
        WHERE race_id = :race_id
        AND decimal_odds >= 1.01
    )
    SELECT horse_id, decimal_odds, source
    FROM latest
    WHERE rn = 1
    ORDER BY decimal_odds
    """
    
    with engine.begin() as cx:
        df = pl.read_database(sql, connection=cx.connection, params={"race_id": race_id})
    
    if len(df) == 0:
        print(f"   ⚠️  No market prices found - using fallback decimal_odds from racing.runners")
        
        # Fallback to morning prices
        sql_fallback = """
        SELECT 
            horse_id,
            COALESCE(win_ppwap, dec) as decimal_odds,
            'morning_line' as source
        FROM racing.runners
        WHERE race_id = :race_id
        AND COALESCE(win_ppwap, dec) >= 1.01
        ORDER BY COALESCE(win_ppwap, dec)
        """
        
        with engine.begin() as cx:
            df = pl.read_database(sql_fallback, connection=cx.connection, params={"race_id": race_id})
    
    print(f"   ✅ Loaded prices for {len(df)} horses")
    
    return df


def score_race(df: pl.DataFrame, model_name: str = "hrd_win_prob", model_stage: str = "Production") -> pl.DataFrame:
    """
    Score race runners with ability model.
    
    Args:
        df: DataFrame with ability features
        model_name: MLflow model name
        model_stage: MLflow stage
        
    Returns:
        DataFrame with p_model predictions
    """
    print(f"\n🤖 Scoring with model: {model_name} ({model_stage})")
    
    # Load model
    model_uri = f"models:/{model_name}/{model_stage}"
    model = mlflow.pyfunc.load_model(model_uri)
    
    # Prepare features
    X = df.select([f for f in ABILITY_FEATURES if f in df.columns])
    X = X.with_columns([pl.col(col).fill_null(0) for col in X.columns])
    
    # Predict
    p_model = model.predict(X.to_pandas()).astype(float)
    
    df = df.with_columns([
        pl.Series(name="p_model", values=p_model)
    ])
    
    print(f"   ✅ Predictions complete")
    
    return df


def compute_value_analysis(df: pl.DataFrame, prices: pl.DataFrame) -> pl.DataFrame:
    """
    Join prices and compute value analysis.
    
    Args:
        df: DataFrame with predictions
        prices: DataFrame with market prices
        
    Returns:
        DataFrame with value analysis
    """
    print(f"\n🧮 Computing value analysis...")
    
    # Join prices
    df = df.join(prices, on="horse_id", how="inner")
    
    # Market probability
    df = df.with_columns([
        (1.0 / pl.col("decimal_odds")).alias("q_market")
    ])
    
    # Vig-free
    overround = df["q_market"].sum()
    
    df = df.with_columns([
        (pl.col("q_market") / overround).alias("q_vigfree"),
        pl.lit(overround).alias("overround")
    ])
    
    # Fair odds
    df = df.with_columns([
        (1.0 / pl.col("p_model")).alias("fair_odds_win")
    ])
    
    # Edge
    df = df.with_columns([
        (pl.col("p_model") - pl.col("q_vigfree")).alias("edge_prob")
    ])
    
    # EV
    def calc_ev(p, odds):
        return ev_win(p, odds, COMMISSION)
    
    df = df.with_columns([
        pl.struct(["p_model", "decimal_odds"]).map_elements(
            lambda x: calc_ev(x["p_model"], x["decimal_odds"]),
            return_dtype=pl.Float64
        ).alias("ev_after_commission")
    ])
    
    print(f"   ✅ Analysis complete")
    print(f"   Overround: {overround:.3f} ({(overround-1)*100:.1f}% margin)")
    
    return df


def display_results(df: pl.DataFrame, race_info: dict) -> None:
    """
    Display race pricing results.
    
    Args:
        df: DataFrame with value analysis
        race_info: Race metadata
    """
    print(f"\n" + "=" * 100)
    print(f"🏇 RACE PRICING ANALYSIS")
    print(f"=" * 100)
    print(f"\n📍 Race Details:")
    print(f"   ID: {race_info['race_id']}")
    print(f"   Course: {race_info['course_name']}")
    print(f"   Date: {race_info['race_date']}")
    print(f"   Time: {race_info['off_time']}")
    print(f"   Class: {race_info['class']}")
    print(f"   Distance: {race_info['dist_f']}f")
    
    # Sort by market odds
    df = df.sort("decimal_odds")
    
    # Display table
    print(f"\n📊 FAIR ODDS vs MARKET ODDS:")
    print(f"=" * 100)
    
    # Select columns to display
    display_df = df.select([
        "horse_name",
        "decimal_odds",
        "fair_odds_win",
        "p_model",
        "q_vigfree",
        "edge_prob",
        "ev_after_commission",
        "gpr",
        "gpr_minus_or"
    ])
    
    # Rename for display
    display_df = display_df.rename({
        "horse_name": "Horse",
        "decimal_odds": "Market",
        "fair_odds_win": "Fair",
        "p_model": "P_model",
        "q_vigfree": "P_market",
        "edge_prob": "Edge",
        "ev_after_commission": "EV%",
        "gpr": "GPR",
        "gpr_minus_or": "GPR-OR"
    })
    
    # Format
    display_df = display_df.with_columns([
        (pl.col("Market").round(2)),
        (pl.col("Fair").round(2)),
        (pl.col("P_model").round(3)),
        (pl.col("P_market").round(3)),
        (pl.col("Edge").round(3)),
        (pl.col("EV%").round(3)),
        (pl.col("GPR").round(1)),
        (pl.col("GPR-OR").round(1))
    ])
    
    print(display_df)
    
    # Value bets
    value_bets = df.filter(
        (pl.col("edge_prob") >= 0.03) &
        (pl.col("decimal_odds") >= 2.0) &
        (pl.col("ev_after_commission") >= 0.02)
    )
    
    print(f"\n" + "=" * 100)
    if len(value_bets) > 0:
        print(f"✅ VALUE BETS FOUND: {len(value_bets)}")
        print(f"=" * 100)
        
        for row in value_bets.iter_rows(named=True):
            print(f"\n🎯 {row['horse_name']}")
            print(f"   Market Odds: {row['decimal_odds']:.2f}")
            print(f"   Fair Odds:   {row['fair_odds_win']:.2f}")
            print(f"   Edge:        {row['edge_prob']:.3f} ({row['edge_prob']*100:+.1f}pp)")
            print(f"   EV:          {row['ev_after_commission']:.3f} ({row['ev_after_commission']*100:+.1f}%)")
            print(f"   GPR:         {row['gpr']:.1f} (OR: {row.get('official_rating', 0):.0f}, Δ: {row['gpr_minus_or']:+.1f})")
    else:
        print(f"⚠️  NO VALUE BETS FOUND")
        print(f"=" * 100)
        print(f"\n   All horses are fairly priced or overbet by the market.")
        print(f"   No bets recommended for this race.")
    
    print(f"\n" + "=" * 100)


def main():
    parser = argparse.ArgumentParser(description="Price a single race")
    parser.add_argument("--race-id", type=int, help="Direct race ID")
    parser.add_argument("--date", type=str, help="Race date (YYYY-MM-DD)")
    parser.add_argument("--course", type=str, help="Course name")
    parser.add_argument("--time", type=str, help="Off time (HH:MM)")
    parser.add_argument("--model-name", type=str, default="hrd_win_prob", help="Model name")
    parser.add_argument("--model-stage", type=str, default="Production", help="Model stage")
    
    args = parser.parse_args()
    
    # Validate inputs
    if not args.race_id and not (args.date and args.course and args.time):
        parser.error("Either --race-id OR --date/--course/--time must be provided")
    
    # Find race
    race_id, race_info = find_race(
        date_str=args.date,
        course_name=args.course,
        time_str=args.time,
        race_id=args.race_id
    )
    
    print(f"✅ Found race: {race_info['course_name']} {race_info['race_date']} {race_info['off_time']}")
    
    # Get runners with ability features
    df = get_race_runners(race_id)
    
    # Get current prices
    prices = get_current_prices(race_id)
    
    # Score
    df = score_race(df, args.model_name, args.model_stage)
    
    # Value analysis
    df = compute_value_analysis(df, prices)
    
    # Display
    display_results(df, race_info)


if __name__ == "__main__":
    main()
