#!/usr/bin/env python3
"""Morning report: compare the model's picks vs your actual betting P&L.

Reads the settled model predictions (predictions_settled.csv) and your Betfair
journal (bets.csv), and reports side-by-side:
  - model BACK picks: hit-rate + ROI at BSP
  - model LAY picks : lose-rate + ROI
  - your BACK bets   : P&L + ROI
  - your LAY bets    : P&L + ROI

This is the "does following the model beat my own judgement" signal.
"""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def load_preds():
    back, lay = [], []
    p = ROOT / "predictions_settled.csv"
    if not p.exists():
        return back, lay
    for r in csv.DictReader(p.open()):
        if r["won"] == "" or r["action"] not in ("TAKE PRICE", "LAY"):
            continue
        won = int(r["won"])
        bsp = float(r["bsp"]) if r["bsp"] else None
        (back if r["action"] == "TAKE PRICE" else lay).append((won, bsp))
    return back, lay


def load_bets():
    back, lay = [], []
    b = ROOT / "bets.csv"
    if not b.exists():
        return back, lay
    for r in csv.DictReader(b.open()):
        if r["status"] != "SETTLED":
            continue
        (back if r["side"] == "BACK" else lay).append(float(r["profit"]))
    return back, lay


def main():
    model_back, model_lay = load_preds()
    user_back, user_lay = load_bets()

    print("=" * 60)
    print("MORNING REPORT — model vs your betting")
    print("=" * 60)

    # model back picks
    if model_back:
        n = len(model_back)
        wins = sum(1 for w, _ in model_back if w == 1)
        roi = sum((bsp - 1 if w == 1 else -1.0) for w, bsp in model_back if bsp) / n * 100
        print(f"\nMODEL back picks : {n:3d}  hit {wins/n*100:4.1f}%  ROI@BSP {roi:+6.1f}%")
    else:
        print("\nMODEL back picks : no settled data yet")

    # model lay picks
    if model_lay:
        n = len(model_lay)
        loses = sum(1 for w, _ in model_lay if w == 0)
        roi = sum((1.0 if w == 0 else -(bsp - 1)) for w, bsp in model_lay if bsp) / n * 100
        print(f"MODEL lay picks  : {n:3d}  lose {loses/n*100:4.1f}%  ROI@BSP {roi:+6.1f}%")
    else:
        print("MODEL lay picks  : no settled data yet")

    # user back bets
    if user_back:
        n = len(user_back)
        stake = n  # flat-ish; P&L already in £
        print(f"\nYOUR back bets   : {n:3d}  P&L £{sum(user_back):+7.2f}")
    else:
        print("\nYOUR back bets   : none logged")

    # user lay bets
    if user_lay:
        n = len(user_lay)
        print(f"YOUR lay bets    : {n:3d}  P&L £{sum(user_lay):+7.2f}")
    else:
        print("YOUR lay bets    : none logged")

    print("\n" + "-" * 60)
    print("Verdict: if MODEL ROI > YOUR P&L consistently, follow the model.")
    print("If YOUR P&L > MODEL, your judgement is adding value — feed that back.")


if __name__ == "__main__":
    main()
