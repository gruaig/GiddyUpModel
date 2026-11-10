#!/usr/bin/env bash
# Morning routine: predict today's card, then review yesterday's P&L.
#
# Usage:
#   bash win_prob/morning.sh [BANK]
#   e.g. bash win_prob/morning.sh 1000
#
# BANK = your current balance (drives the stake sizing in predict_today).

set -euo pipefail
cd "$(dirname "$0")/.."

BANK="${1:-1000}"
PY=".venv/bin/python"

echo "═══════════════════════════════════════════════════════════"
echo " 1/4 — PREDICT today's card (soonest-first, upcoming races)"
echo "═══════════════════════════════════════════════════════════"
$PY win_prob/predict_today.py --bank "$BANK" --margin 0.10 --drift-max 0.10 --max-per-race 1

echo
echo "═══════════════════════════════════════════════════════════"
echo " 2/4 — SETTLE logged predictions (fills in results + BSP)"
echo "═══════════════════════════════════════════════════════════"
$PY win_prob/settle.py || echo "  (nothing to settle yet — DB may be behind)"

echo
echo "═══════════════════════════════════════════════════════════"
echo " 3/4 — YOUR betting journal (open offers + settled P&L)"
echo "═══════════════════════════════════════════════════════════"
$PY win_prob/pnl.py || echo "  (no settled bets today)"

echo
echo "═══════════════════════════════════════════════════════════"
echo " 4/4 — REPORT (model vs your P&L)"
echo "═══════════════════════════════════════════════════════════"
$PY win_prob/report.py

echo
echo "Done. Logs: win_prob/predictions_log.csv, bets.csv, predictions_settled.csv"
