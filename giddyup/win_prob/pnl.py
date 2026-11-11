#!/usr/bin/env python3
"""Betting journal: read your actual Betfair offers (open + settled) and track P&L.

Pulls both your CURRENT (open/unmatched) orders and your SETTLED bets from
Betfair, saves them to bets.csv, and reports:
  - open positions (live offers still in the market)
  - settled P&L / ROI / win-rate, split by side (BACK vs LAY)

Usage:
    .venv/bin/python win_prob/pnl.py                  # today
    .venv/bin/python win_prob/pnl.py --from 2026-11-01 --to 2026-11-10
"""
import argparse
import csv
import datetime as dt
import sys
from pathlib import Path

import pytz

ROOT = Path(__file__).resolve().parent
BETS_CSV = ROOT / "bets.csv"
sys.path.insert(0, str(ROOT))
import betfair_client as bf
from betfairlightweight import filters as F


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="from_d", default=dt.date.today().isoformat())
    ap.add_argument("--to", dest="to_d", default=None)
    args = ap.parse_args()

    start = dt.datetime.fromisoformat(args.from_d).replace(tzinfo=pytz.UTC)
    end = (dt.datetime.fromisoformat(args.to_d).replace(tzinfo=pytz.UTC) + dt.timedelta(days=1)) if args.to_d else start + dt.timedelta(days=1)

    c = bf.login()

    # ---- current orders: split unmatched vs matched-but-not-settled ----
    open_rows = []       # genuinely open (still unmatched, can cancel/take)
    matched_unsettled = []  # fully matched, race not settled yet
    try:
        cur = c.betting.list_current_orders()
        for o in (cur.orders or []):
            ps = getattr(o, "price_size", None)
            price = getattr(ps, "price", 0) or 0
            size = getattr(ps, "size", 0) or 0
            remaining = getattr(o, "size_remaining", 0) or 0
            row = {
                "settled_at": str(getattr(o, "placed_date", "") or ""),
                "market_id": str(getattr(o, "market_id", "") or ""),
                "selection_id": str(getattr(o, "selection_id", "") or ""),
                "side": getattr(o, "side", "") or "",
                "price": price, "stake": size,
                "matched": getattr(o, "size_matched", 0) or 0,
                "remaining": remaining,
                "profit": 0.0,
                "status": "OPEN" if remaining > 0 else "PLACED",
            }
            if remaining > 0:
                open_rows.append(row)
            else:
                matched_unsettled.append(row)
    except Exception as e:
        print(f"  (could not fetch current orders: {e})")

    # ---- settled bets ----
    print(f"Fetching settled bets {start:%Y-%m-%d} -> {end:%Y-%m-%d} ...")
    cleared = c.betting.list_cleared_orders(
        bet_status="SETTLED",
        settled_date_range=F.time_range(from_=start.isoformat(), to=end.isoformat()),
        group_by="BET",
    )
    c.logout()

    settled_rows = []
    for o in (cleared.orders or []):
        settled_rows.append({
            "settled_at": str(getattr(o, "settled_date", "") or ""),
            "market_id": str(getattr(o, "market_id", "") or ""),
            "selection_id": str(getattr(o, "selection_id", "") or ""),
            "side": getattr(o, "side", "") or "",
            "price": getattr(o, "price_matched", 0) or 0,
            "stake": getattr(o, "size_settled", 0) or 0,
            "matched": getattr(o, "size_settled", 0) or 0,
            "remaining": 0,
            "profit": getattr(o, "profit", 0) or 0, "status": "SETTLED",
        })

    all_rows = open_rows + matched_unsettled + settled_rows
    fields = ["settled_at", "market_id", "selection_id", "side", "price", "stake", "matched", "remaining", "profit", "status"]
    new = not BETS_CSV.exists()
    with BETS_CSV.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        if new:
            w.writeheader()
        for r in all_rows:
            w.writerow(r)

    # ---- report ----
    if open_rows:
        print(f"\n=== OPEN OFFERS — unmatched, still in the market ({len(open_rows)}) ===")
        print(f"{'side':5s} {'price':>7s} {'stake':>7s} {'matched':>7s} {'remaining':>9s}")
        for r in open_rows:
            print(f"{r['side']:5s} {r['price']:>7.2f} {r['stake']:>7.2f} {r['matched']:>7.2f} {r['remaining']:>9.2f}")

    if matched_unsettled:
        print(f"\n=== PLACED — matched, awaiting settlement ({len(matched_unsettled)}) ===")
        print(f"{'side':5s} {'price':>7s} {'stake':>7s}")
        for r in matched_unsettled:
            print(f"{r['side']:5s} {r['price']:>7.2f} {r['stake']:>7.2f}")

    if settled_rows:
        tot = sum(r["profit"] for r in settled_rows)
        stake_sum = sum(r["stake"] for r in settled_rows)

        def line(label, group):
            p = sum(r["profit"] for r in group)
            s = sum(r["stake"] for r in group)
            roi = p / s * 100 if s else 0
            wr = sum(1 for r in group if r["profit"] > 0) / len(group) * 100 if group else 0
            print(f"  {label:6s}: {len(group):3d} bets, P&L {p:+7.2f}, stake £{s:7.2f}, ROI {roi:+6.1f}%, win-rate {wr:.0f}%")

        print(f"\n=== SETTLED P&L {args.from_d} -> {args.to_d or 'today'} ===")
        line("ALL", settled_rows)
        line("BACK", [r for r in settled_rows if r["side"] == "BACK"])
        line("LAY", [r for r in settled_rows if r["side"] == "LAY"])
        print(f"\nNet P&L: £{tot:+.2f}   ({len(settled_rows)} bets, £{stake_sum:.2f} staked)")
    else:
        print("\nNo settled bets in that range.")

    print(f"\nJournal saved to {BETS_CSV} ({len(all_rows)} rows)")


if __name__ == "__main__":
    main()
