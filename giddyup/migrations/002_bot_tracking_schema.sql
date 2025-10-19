-- ============================================================================
-- Bot Activity Tracking Schema
-- ============================================================================
-- Purpose: Track all bot activities, bets, results, and notifications
-- Created: 2025-10-20
-- ============================================================================

-- ============================================================================
-- 1. DAILY SESSIONS TABLE
-- ============================================================================
-- Tracks each bot run session

CREATE TABLE IF NOT EXISTS bot_sessions (
    session_id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    bot_type VARCHAR(50) NOT NULL, -- 'HorseBot', 'BackLayBot', etc.
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    bankroll_a DECIMAL(10,2),
    bankroll_b DECIMAL(10,2),
    mode VARCHAR(20) NOT NULL, -- 'DRY_RUN' or 'LIVE'
    status VARCHAR(20) DEFAULT 'RUNNING', -- 'RUNNING', 'COMPLETED', 'FAILED'
    total_selections INTEGER,
    total_bets_placed INTEGER,
    total_bets_skipped INTEGER,
    final_pnl DECIMAL(10,2),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(date, bot_type, start_time)
);

CREATE INDEX idx_bot_sessions_date ON bot_sessions(date);
CREATE INDEX idx_bot_sessions_status ON bot_sessions(status);

-- ============================================================================
-- 2. MORNING SELECTIONS TABLE
-- ============================================================================
-- Stores all morning selections from the model

CREATE TABLE IF NOT EXISTS morning_selections (
    selection_id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES bot_sessions(session_id),
    date DATE NOT NULL,
    race_time TIME NOT NULL,
    course VARCHAR(100) NOT NULL,
    horse VARCHAR(200) NOT NULL,
    strategy VARCHAR(50) NOT NULL, -- 'A-Hybrid_V3', 'B-Path_B'
    expected_odds DECIMAL(10,2) NOT NULL,
    min_odds_needed DECIMAL(10,2) NOT NULL,
    stake_gbp DECIMAL(10,2) NOT NULL,
    reasoning TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(date, race_time, course, horse, strategy)
);

CREATE INDEX idx_morning_selections_date ON morning_selections(date);
CREATE INDEX idx_morning_selections_session ON morning_selections(session_id);
CREATE INDEX idx_morning_selections_race ON morning_selections(date, race_time);

-- ============================================================================
-- 3. PRICE TRACKING TABLE
-- ============================================================================
-- Tracks all price observations throughout the day

CREATE TABLE IF NOT EXISTS price_observations (
    observation_id SERIAL PRIMARY KEY,
    selection_id INTEGER REFERENCES morning_selections(selection_id),
    observed_at TIMESTAMP NOT NULL,
    minutes_to_off INTEGER,
    back_odds DECIMAL(10,2),
    lay_odds DECIMAL(10,2),
    market_id VARCHAR(100),
    selection_id_betfair VARCHAR(100),
    market_status VARCHAR(50), -- 'OPEN', 'SUSPENDED', 'CLOSED'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_price_observations_selection ON price_observations(selection_id);
CREATE INDEX idx_price_observations_time ON price_observations(observed_at);

-- ============================================================================
-- 4. BET DECISIONS TABLE
-- ============================================================================
-- Records every betting decision (placed or skipped)

CREATE TABLE IF NOT EXISTS bet_decisions (
    decision_id SERIAL PRIMARY KEY,
    selection_id INTEGER REFERENCES morning_selections(selection_id),
    decision_time TIMESTAMP NOT NULL,
    minutes_to_off INTEGER,
    decision VARCHAR(20) NOT NULL, -- 'PLACED', 'SKIPPED', 'FAILED'
    current_odds DECIMAL(10,2),
    stake_gbp DECIMAL(10,2),
    bet_id VARCHAR(100), -- Betfair bet ID or DRY_RUN_xxx
    market_id VARCHAR(100),
    selection_id_betfair VARCHAR(100),
    reason TEXT, -- Why placed or skipped
    drift_percentage DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(selection_id, decision_time)
);

CREATE INDEX idx_bet_decisions_selection ON bet_decisions(selection_id);
CREATE INDEX idx_bet_decisions_decision ON bet_decisions(decision);
CREATE INDEX idx_bet_decisions_time ON bet_decisions(decision_time);

-- ============================================================================
-- 5. BET RESULTS TABLE
-- ============================================================================
-- Stores final results and P&L for each bet

CREATE TABLE IF NOT EXISTS bet_results (
    result_id SERIAL PRIMARY KEY,
    decision_id INTEGER REFERENCES bet_decisions(decision_id) UNIQUE,
    selection_id INTEGER REFERENCES morning_selections(selection_id),
    result VARCHAR(20), -- 'WIN', 'LOSS', 'VOID', 'PENDING'
    settled_odds DECIMAL(10,2), -- Final odds (may differ from placed odds)
    stake_gbp DECIMAL(10,2),
    gross_return DECIMAL(10,2), -- Total return if won
    commission DECIMAL(10,2), -- Betfair commission
    net_pnl DECIMAL(10,2), -- Final P&L after commission
    result_checked_at TIMESTAMP,
    settled_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_bet_results_selection ON bet_results(selection_id);
CREATE INDEX idx_bet_results_result ON bet_results(result);
CREATE INDEX idx_bet_results_pnl ON bet_results(net_pnl);

-- ============================================================================
-- 6. TELEGRAM NOTIFICATIONS TABLE
-- ============================================================================
-- Tracks all Telegram notifications sent

CREATE TABLE IF NOT EXISTS telegram_notifications (
    notification_id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES bot_sessions(session_id),
    selection_id INTEGER REFERENCES morning_selections(selection_id),
    decision_id INTEGER REFERENCES bet_decisions(decision_id),
    result_id INTEGER REFERENCES bet_results(result_id),
    notification_type VARCHAR(50) NOT NULL, -- 'MORNING_PICKS', 'BET_PLACED', 'BET_SKIPPED', 'RESULT', 'DAILY_SUMMARY'
    sent_at TIMESTAMP NOT NULL,
    channel_id VARCHAR(100),
    message_id VARCHAR(100), -- Telegram message ID
    message_text TEXT,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_telegram_notifications_session ON telegram_notifications(session_id);
CREATE INDEX idx_telegram_notifications_type ON telegram_notifications(notification_type);
CREATE INDEX idx_telegram_notifications_sent ON telegram_notifications(sent_at);
CREATE INDEX idx_telegram_notifications_selection ON telegram_notifications(selection_id);

-- ============================================================================
-- 7. BACKLAY TRADES TABLE
-- ============================================================================
-- Tracks back-to-lay trading activity

CREATE TABLE IF NOT EXISTS backlay_trades (
    trade_id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES bot_sessions(session_id),
    selection_id INTEGER REFERENCES morning_selections(selection_id),
    back_time TIMESTAMP NOT NULL,
    back_odds DECIMAL(10,2) NOT NULL,
    back_stake DECIMAL(10,2) NOT NULL,
    lay_time TIMESTAMP,
    lay_odds DECIMAL(10,2),
    lay_stake DECIMAL(10,2),
    lay_reason VARCHAR(200), -- Why we laid (price drop, T-15, etc.)
    profit_gbp DECIMAL(10,2),
    profit_percentage DECIMAL(5,2),
    status VARCHAR(20) DEFAULT 'OPEN', -- 'OPEN', 'CLOSED', 'EXPIRED'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_backlay_trades_session ON backlay_trades(session_id);
CREATE INDEX idx_backlay_trades_selection ON backlay_trades(selection_id);
CREATE INDEX idx_backlay_trades_status ON backlay_trades(status);

-- ============================================================================
-- VIEWS FOR EASY QUERYING
-- ============================================================================

-- Daily P&L Summary
CREATE OR REPLACE VIEW vw_daily_pnl AS
SELECT 
    s.date,
    s.bot_type,
    s.mode,
    COUNT(DISTINCT ms.selection_id) as total_selections,
    COUNT(DISTINCT bd.decision_id) as total_bets,
    COUNT(DISTINCT CASE WHEN bd.decision = 'PLACED' THEN bd.decision_id END) as bets_placed,
    COUNT(DISTINCT CASE WHEN bd.decision = 'SKIPPED' THEN bd.decision_id END) as bets_skipped,
    COUNT(DISTINCT CASE WHEN br.result = 'WIN' THEN br.result_id END) as wins,
    COUNT(DISTINCT CASE WHEN br.result = 'LOSS' THEN br.result_id END) as losses,
    SUM(CASE WHEN bd.decision = 'PLACED' THEN bd.stake_gbp ELSE 0 END) as total_staked,
    SUM(br.net_pnl) as net_pnl,
    CASE 
        WHEN SUM(CASE WHEN bd.decision = 'PLACED' THEN bd.stake_gbp ELSE 0 END) > 0 
        THEN (SUM(br.net_pnl) / SUM(CASE WHEN bd.decision = 'PLACED' THEN bd.stake_gbp ELSE 0 END) * 100)
        ELSE 0 
    END as roi_percentage
FROM bot_sessions s
LEFT JOIN morning_selections ms ON s.session_id = ms.session_id
LEFT JOIN bet_decisions bd ON ms.selection_id = bd.selection_id
LEFT JOIN bet_results br ON bd.decision_id = br.decision_id
GROUP BY s.date, s.bot_type, s.mode
ORDER BY s.date DESC;

-- Bet Detail View
CREATE OR REPLACE VIEW vw_bet_details AS
SELECT 
    ms.date,
    ms.race_time,
    ms.course,
    ms.horse,
    ms.strategy,
    ms.expected_odds,
    ms.min_odds_needed,
    ms.stake_gbp,
    bd.decision,
    bd.current_odds as actual_odds,
    bd.reason as decision_reason,
    bd.drift_percentage,
    br.result,
    br.net_pnl,
    tn.notification_type,
    tn.sent_at as telegram_sent_at
FROM morning_selections ms
LEFT JOIN bet_decisions bd ON ms.selection_id = bd.selection_id
LEFT JOIN bet_results br ON bd.decision_id = br.decision_id
LEFT JOIN telegram_notifications tn ON ms.selection_id = tn.selection_id
ORDER BY ms.date DESC, ms.race_time;

-- Telegram Activity View
CREATE OR REPLACE VIEW vw_telegram_activity AS
SELECT 
    DATE(tn.sent_at) as date,
    tn.notification_type,
    COUNT(*) as count,
    COUNT(CASE WHEN tn.success THEN 1 END) as successful,
    COUNT(CASE WHEN NOT tn.success THEN 1 END) as failed
FROM telegram_notifications tn
GROUP BY DATE(tn.sent_at), tn.notification_type
ORDER BY date DESC, notification_type;

-- Strategy Performance View
CREATE OR REPLACE VIEW vw_strategy_performance AS
SELECT 
    ms.strategy,
    ms.date,
    COUNT(DISTINCT ms.selection_id) as total_selections,
    COUNT(DISTINCT CASE WHEN bd.decision = 'PLACED' THEN bd.decision_id END) as bets_placed,
    COUNT(DISTINCT CASE WHEN br.result = 'WIN' THEN br.result_id END) as wins,
    COUNT(DISTINCT CASE WHEN br.result = 'LOSS' THEN br.result_id END) as losses,
    SUM(CASE WHEN bd.decision = 'PLACED' THEN bd.stake_gbp ELSE 0 END) as total_staked,
    SUM(br.net_pnl) as net_pnl,
    CASE 
        WHEN COUNT(DISTINCT CASE WHEN br.result IN ('WIN', 'LOSS') THEN br.result_id END) > 0
        THEN (COUNT(DISTINCT CASE WHEN br.result = 'WIN' THEN br.result_id END)::DECIMAL / 
              COUNT(DISTINCT CASE WHEN br.result IN ('WIN', 'LOSS') THEN br.result_id END) * 100)
        ELSE 0 
    END as win_rate_percentage
FROM morning_selections ms
LEFT JOIN bet_decisions bd ON ms.selection_id = bd.selection_id
LEFT JOIN bet_results br ON bd.decision_id = br.decision_id
GROUP BY ms.strategy, ms.date
ORDER BY ms.date DESC, ms.strategy;

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function to get current session
CREATE OR REPLACE FUNCTION get_current_session(p_date DATE, p_bot_type VARCHAR)
RETURNS INTEGER AS $$
BEGIN
    RETURN (
        SELECT session_id 
        FROM bot_sessions 
        WHERE date = p_date 
        AND bot_type = p_bot_type 
        AND status = 'RUNNING'
        ORDER BY start_time DESC 
        LIMIT 1
    );
END;
$$ LANGUAGE plpgsql;

-- Function to calculate P&L
CREATE OR REPLACE FUNCTION calculate_pnl(
    p_result VARCHAR,
    p_odds DECIMAL,
    p_stake DECIMAL,
    p_commission_rate DECIMAL DEFAULT 0.02
)
RETURNS DECIMAL AS $$
BEGIN
    IF p_result = 'WIN' THEN
        -- Gross return - stake - commission on profit
        RETURN ROUND((p_odds * p_stake) - p_stake - ((p_odds * p_stake - p_stake) * p_commission_rate), 2);
    ELSIF p_result = 'LOSS' THEN
        RETURN -p_stake;
    ELSE
        RETURN 0;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- GRANT PERMISSIONS (adjust user as needed)
-- ============================================================================

-- GRANT ALL ON ALL TABLES IN SCHEMA public TO your_user;
-- GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO your_user;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO your_user;

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE bot_sessions IS 'Tracks each bot run session with metadata and summary stats';
COMMENT ON TABLE morning_selections IS 'All morning selections from the model before betting starts';
COMMENT ON TABLE price_observations IS 'Continuous price tracking throughout the day';
COMMENT ON TABLE bet_decisions IS 'Every betting decision made (placed, skipped, or failed)';
COMMENT ON TABLE bet_results IS 'Final results and P&L for each bet';
COMMENT ON TABLE telegram_notifications IS 'All Telegram notifications sent with success status';
COMMENT ON TABLE backlay_trades IS 'Back-to-lay trading activity for the BackLayBot';

COMMENT ON VIEW vw_daily_pnl IS 'Daily profit/loss summary by bot type';
COMMENT ON VIEW vw_bet_details IS 'Complete bet details with all related information';
COMMENT ON VIEW vw_telegram_activity IS 'Telegram notification activity summary';
COMMENT ON VIEW vw_strategy_performance IS 'Performance metrics by strategy';

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================

