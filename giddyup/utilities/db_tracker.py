#!/usr/bin/env python3
"""
Database Tracker for Bot Activities
====================================
Provides easy-to-use functions for tracking all bot activities in PostgreSQL.

Usage:
    from utilities.db_tracker import BotTracker
    
    tracker = BotTracker()
    session_id = tracker.start_session('2025-10-20', 'HorseBot', 5000, 50000)
    selection_id = tracker.record_selection(session_id, ...)
    tracker.record_bet_decision(selection_id, 'PLACED', ...)
    tracker.record_telegram_notification(selection_id, 'BET_PLACED', ...)
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, time
from typing import Optional, Dict, List, Any
from decimal import Decimal
import os

class BotTracker:
    """Track all bot activities in PostgreSQL database."""
    
    def __init__(self, connection_string: Optional[str] = None):
        """
        Initialize database connection.
        
        Args:
            connection_string: PostgreSQL connection string
                              If None, reads from environment or uses default
        """
        if connection_string is None:
            connection_string = os.getenv(
                'DATABASE_URL',
                'postgresql://localhost/giddyup'
            )
        
        self.conn_string = connection_string
        self._conn = None
    
    def _get_connection(self):
        """Get or create database connection."""
        if self._conn is None or self._conn.closed:
            self._conn = psycopg2.connect(self.conn_string)
        return self._conn
    
    def _execute(self, query: str, params: tuple = None, fetch_one=False, fetch_all=False):
        """Execute query and optionally fetch results."""
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                
                if fetch_one:
                    return cur.fetchone()
                elif fetch_all:
                    return cur.fetchall()
                else:
                    conn.commit()
                    return cur.rowcount
        except Exception as e:
            conn.rollback()
            raise e
    
    # ========================================================================
    # SESSION MANAGEMENT
    # ========================================================================
    
    def start_session(self, date: str, bot_type: str, 
                      bankroll_a: float = None, bankroll_b: float = None,
                      mode: str = 'DRY_RUN') -> int:
        """
        Start a new bot session.
        
        Args:
            date: Date in YYYY-MM-DD format
            bot_type: 'HorseBot', 'BackLayBot', etc.
            bankroll_a: Strategy A bankroll
            bankroll_b: Strategy B bankroll
            mode: 'DRY_RUN' or 'LIVE'
            
        Returns:
            session_id: ID of created session
        """
        query = """
            INSERT INTO bot_sessions 
            (date, bot_type, start_time, bankroll_a, bankroll_b, mode)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING session_id
        """
        result = self._execute(
            query,
            (date, bot_type, datetime.now(), bankroll_a, bankroll_b, mode),
            fetch_one=True
        )
        return result['session_id']
    
    def end_session(self, session_id: int, status: str = 'COMPLETED',
                   total_selections: int = None, total_bets_placed: int = None,
                   total_bets_skipped: int = None, final_pnl: float = None,
                   notes: str = None):
        """End a bot session with summary stats."""
        query = """
            UPDATE bot_sessions
            SET end_time = %s,
                status = %s,
                total_selections = %s,
                total_bets_placed = %s,
                total_bets_skipped = %s,
                final_pnl = %s,
                notes = %s
            WHERE session_id = %s
        """
        self._execute(query, (
            datetime.now(), status, total_selections, total_bets_placed,
            total_bets_skipped, final_pnl, notes, session_id
        ))
    
    # ========================================================================
    # MORNING SELECTIONS
    # ========================================================================
    
    def record_selection(self, session_id: int, date: str, race_time: str,
                        course: str, horse: str, strategy: str,
                        expected_odds: float, min_odds_needed: float,
                        stake_gbp: float, reasoning: str = None) -> int:
        """
        Record a morning selection.
        
        Returns:
            selection_id: ID of created selection
        """
        query = """
            INSERT INTO morning_selections
            (session_id, date, race_time, course, horse, strategy,
             expected_odds, min_odds_needed, stake_gbp, reasoning)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (date, race_time, course, horse, strategy) 
            DO UPDATE SET
                expected_odds = EXCLUDED.expected_odds,
                min_odds_needed = EXCLUDED.min_odds_needed,
                stake_gbp = EXCLUDED.stake_gbp
            RETURNING selection_id
        """
        result = self._execute(
            query,
            (session_id, date, race_time, course, horse, strategy,
             expected_odds, min_odds_needed, stake_gbp, reasoning),
            fetch_one=True
        )
        return result['selection_id']
    
    def get_selection_id(self, date: str, race_time: str, course: str,
                        horse: str, strategy: str) -> Optional[int]:
        """Get selection ID for a given race/horse."""
        query = """
            SELECT selection_id
            FROM morning_selections
            WHERE date = %s AND race_time = %s AND course = %s 
              AND horse = %s AND strategy = %s
        """
        result = self._execute(
            query,
            (date, race_time, course, horse, strategy),
            fetch_one=True
        )
        return result['selection_id'] if result else None
    
    # ========================================================================
    # PRICE TRACKING
    # ========================================================================
    
    def record_price_observation(self, selection_id: int, minutes_to_off: int,
                                back_odds: float = None, lay_odds: float = None,
                                market_id: str = None, selection_id_betfair: str = None,
                                market_status: str = 'OPEN'):
        """Record a price observation."""
        query = """
            INSERT INTO price_observations
            (selection_id, observed_at, minutes_to_off, back_odds, lay_odds,
             market_id, selection_id_betfair, market_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        self._execute(query, (
            selection_id, datetime.now(), minutes_to_off, back_odds, lay_odds,
            market_id, selection_id_betfair, market_status
        ))
    
    # ========================================================================
    # BET DECISIONS
    # ========================================================================
    
    def record_bet_decision(self, selection_id: int, decision: str,
                          minutes_to_off: int, current_odds: float,
                          stake_gbp: float = None, bet_id: str = None,
                          market_id: str = None, selection_id_betfair: str = None,
                          reason: str = None, drift_percentage: float = None) -> int:
        """
        Record a betting decision (PLACED, SKIPPED, or FAILED).
        
        Returns:
            decision_id: ID of created decision
        """
        query = """
            INSERT INTO bet_decisions
            (selection_id, decision_time, minutes_to_off, decision, current_odds,
             stake_gbp, bet_id, market_id, selection_id_betfair, reason, drift_percentage)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (selection_id, decision_time)
            DO UPDATE SET
                decision = EXCLUDED.decision,
                current_odds = EXCLUDED.current_odds,
                stake_gbp = EXCLUDED.stake_gbp,
                bet_id = EXCLUDED.bet_id,
                reason = EXCLUDED.reason
            RETURNING decision_id
        """
        result = self._execute(
            query,
            (selection_id, datetime.now(), minutes_to_off, decision, current_odds,
             stake_gbp, bet_id, market_id, selection_id_betfair, reason, drift_percentage),
            fetch_one=True
        )
        return result['decision_id']
    
    # ========================================================================
    # BET RESULTS
    # ========================================================================
    
    def record_bet_result(self, decision_id: int, result: str,
                         settled_odds: float, stake_gbp: float,
                         gross_return: float = None, commission: float = None,
                         net_pnl: float = None) -> int:
        """
        Record final bet result and P&L.
        
        Returns:
            result_id: ID of created result
        """
        # Calculate P&L if not provided
        if net_pnl is None:
            if result == 'WIN':
                gross_return = settled_odds * stake_gbp
                commission = (gross_return - stake_gbp) * 0.02
                net_pnl = gross_return - stake_gbp - commission
            elif result == 'LOSS':
                gross_return = 0
                commission = 0
                net_pnl = -stake_gbp
            else:
                gross_return = stake_gbp
                commission = 0
                net_pnl = 0
        
        query = """
            INSERT INTO bet_results
            (decision_id, result, settled_odds, stake_gbp, gross_return,
             commission, net_pnl, result_checked_at, settled_at)
            VALUES (
                (SELECT decision_id FROM bet_decisions WHERE decision_id = %s),
                %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (decision_id)
            DO UPDATE SET
                result = EXCLUDED.result,
                settled_odds = EXCLUDED.settled_odds,
                net_pnl = EXCLUDED.net_pnl,
                result_checked_at = EXCLUDED.result_checked_at,
                settled_at = EXCLUDED.settled_at
            RETURNING result_id
        """
        result_row = self._execute(
            query,
            (decision_id, result, settled_odds, stake_gbp, gross_return,
             commission, net_pnl, datetime.now(), datetime.now()),
            fetch_one=True
        )
        return result_row['result_id']
    
    def record_result_by_selection(self, selection_id: int, result: str,
                                   settled_odds: float, stake_gbp: float) -> Optional[int]:
        """Record result using selection_id (finds most recent decision)."""
        # Get the most recent decision for this selection
        query = """
            SELECT decision_id
            FROM bet_decisions
            WHERE selection_id = %s
              AND decision = 'PLACED'
            ORDER BY decision_time DESC
            LIMIT 1
        """
        decision = self._execute(query, (selection_id,), fetch_one=True)
        
        if decision:
            return self.record_bet_result(
                decision['decision_id'], result, settled_odds, stake_gbp
            )
        return None
    
    # ========================================================================
    # TELEGRAM NOTIFICATIONS
    # ========================================================================
    
    def record_telegram_notification(self, notification_type: str,
                                    session_id: int = None, selection_id: int = None,
                                    decision_id: int = None, result_id: int = None,
                                    channel_id: str = None, message_id: str = None,
                                    message_text: str = None, success: bool = True,
                                    error_message: str = None) -> int:
        """
        Record a Telegram notification.
        
        Returns:
            notification_id: ID of created notification
        """
        query = """
            INSERT INTO telegram_notifications
            (session_id, selection_id, decision_id, result_id, notification_type,
             sent_at, channel_id, message_id, message_text, success, error_message)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING notification_id
        """
        result = self._execute(
            query,
            (session_id, selection_id, decision_id, result_id, notification_type,
             datetime.now(), channel_id, message_id, message_text, success, error_message),
            fetch_one=True
        )
        return result['notification_id']
    
    # ========================================================================
    # BACKLAY TRADES
    # ========================================================================
    
    def record_backlay_open(self, session_id: int, selection_id: int,
                           back_odds: float, back_stake: float) -> int:
        """
        Record opening a back-lay trade.
        
        Returns:
            trade_id: ID of created trade
        """
        query = """
            INSERT INTO backlay_trades
            (session_id, selection_id, back_time, back_odds, back_stake, status)
            VALUES (%s, %s, %s, %s, %s, 'OPEN')
            RETURNING trade_id
        """
        result = self._execute(
            query,
            (session_id, selection_id, datetime.now(), back_odds, back_stake),
            fetch_one=True
        )
        return result['trade_id']
    
    def record_backlay_close(self, trade_id: int, lay_odds: float,
                            lay_stake: float, lay_reason: str,
                            profit_gbp: float, profit_percentage: float):
        """Close a back-lay trade."""
        query = """
            UPDATE backlay_trades
            SET lay_time = %s,
                lay_odds = %s,
                lay_stake = %s,
                lay_reason = %s,
                profit_gbp = %s,
                profit_percentage = %s,
                status = 'CLOSED'
            WHERE trade_id = %s
        """
        self._execute(query, (
            datetime.now(), lay_odds, lay_stake, lay_reason,
            profit_gbp, profit_percentage, trade_id
        ))
    
    # ========================================================================
    # QUERIES
    # ========================================================================
    
    def get_daily_pnl(self, date: str) -> Dict:
        """Get daily P&L summary."""
        query = "SELECT * FROM vw_daily_pnl WHERE date = %s"
        return self._execute(query, (date,), fetch_one=True)
    
    def get_bet_details(self, date: str) -> List[Dict]:
        """Get all bet details for a date."""
        query = "SELECT * FROM vw_bet_details WHERE date = %s"
        return self._execute(query, (date,), fetch_all=True)
    
    def get_strategy_performance(self, strategy: str, days: int = 30) -> List[Dict]:
        """Get strategy performance over last N days."""
        query = """
            SELECT * FROM vw_strategy_performance
            WHERE strategy = %s
              AND date >= CURRENT_DATE - %s
            ORDER BY date DESC
        """
        return self._execute(query, (strategy, days), fetch_all=True)
    
    def get_telegram_activity(self, date: str) -> List[Dict]:
        """Get Telegram notification activity for a date."""
        query = "SELECT * FROM vw_telegram_activity WHERE date = %s"
        return self._execute(query, (date,), fetch_all=True)
    
    def close(self):
        """Close database connection."""
        if self._conn and not self._conn.closed:
            self._conn.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def get_tracker() -> BotTracker:
    """Get a database tracker instance."""
    return BotTracker()

