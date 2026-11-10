# win_prob — win-probability model & live Betfair value finder

Predicts win probability for GB/IRE horse racing, benchmarks it against BSP, and
combines it with live Betfair exchange prices to flag **value** (back/lay/leave).

Built leak-free: features only use *past* races (via `shift` over horse_id), the
opening price is the only market input, and BSP/the result are used strictly as
targets — never as features.

## Scripts

| File | Purpose |
|---|---|
| `win_prob_model.py` | Builds the leak-free dataset, trains LightGBM, evaluates vs BSP. |
| `predict_today.py` | **Live predictions** — SL card → model → Betfair prices → actions. |
| `backtest_edge.py` | Backtests the +EV signal vs the morning price / BSP (out-of-sample). |
| `betfair_client.py` | Betfair exchange client (login + win-market back/lay prices). |

## Quick start — today's cards

```bash
cd ~/GiddyUpModel/giddyup
.venv/bin/python win_prob/predict_today.py
```

Options:

```bash
--date 2026-11-10     # a specific day (default: today)
--url  "https://www.sportinglife.com/racing/racecards/.../racecard/<id>/..."   # one race
--race 947823         # only that race id
--max-fair 20         # drop long-shots (fair odds above this; default 20)
--margin 0.05         # min edge before an action fires (default 5%)
```

## Output

```
--- Huntingdon 15:40 (race 947824) ---
Horse            Win%   Fair BF Back BF Lay   EV@BF  Action
Cayman Dancer   14.1%   7.08    8.20   8.60  +15.8%  TAKE PRICE
Blues Singer    18.2%   5.49    5.20   5.30   -5.2%  LEAVE
Gallivanted     23.5%   4.26    3.95   4.00   -7.3%  LAY
```

- **Win%** — model's win probability (normalised so each race sums to 100%).
- **Fair** — `1/win%`, the model's estimate of the *true* price. **This is the ideal price to bet at.**
- **BF Back / BF Lay** — live Betfair exchange prices (~2% margin, not the bookmaker's 15%).
- **EV@BF** — `win% × BF Back − 1` (positive = backing is +EV at the exchange).
- **Action**:
  - `TAKE PRICE` — back it: the exchange back price is ≥ fair + margin (value).
  - `LAY` — lay it: the exchange lay price is ≤ fair − margin (overpriced).
  - `LEAVE` — no edge.
  - `NO BF` — no Betfair market matched (check manually).

**Rule of thumb:** back only when **BF Back ≥ Fair** (or place a limit order at Fair).
The exchange is the fair benchmark — the bookmaker's ~15% margin is already gone.

## Backtest

```bash
.venv/bin/python win_prob/backtest_edge.py
```

Trains on 2010–2023, predicts 2024+ (never seen), then backs every `win% × morning − 1 > margin`
horse at the morning price. Summary: the model returns **~+8–13% ROI vs the morning
price** out-of-sample (before exchange commission), and its picks drift *less* than
the field — a real but modest edge.

## Train / retrain the model

```bash
.venv/bin/python win_prob/win_prob_model.py --rebuild
```

- Snapshot: `data/win_prob_snapshot.parquet` (cached; `--rebuild` re-extracts from Postgres).
- Split: train 2010–2023, validate 2024–2025 (early stopping), test 2026.
- Benchmark: de-overrounded BSP implied probability. Result ≈ **AUC 0.78 vs BSP 0.79**, leak-free.

## Adding new information (features)

New info enters at two touchpoints in `win_prob_model.py`:

1. **Add the column to the SQL `SELECT`** in `build_dataset()` (pull it out of Postgres).
2. **Add it to `FEATURES`** and compute it in `compute_features()`.

Critical rule: any field measured *after* the race (finishing position, RPR, beaten
distance, …) must be `.shift(1).over("horse_id")` — i.e. use the horse's **previous**
run — so the model only sees information available before today's race.

Then re-run `--rebuild` to re-extract and retrain.

## Data notes

- The DB was de-duplicated: ~144k duplicate races + 1.3M duplicate runners removed
  (backup in `racing.bak_races_dedup` / `bak_runners_dedup`).
- 2026 data is loaded by `backend-api/scripts/recover_data.py` (Sporting Life, through
  the previous day).
- Betfair credentials are in `~/GiddyUpModel/giddyup/.env` (`PG_DSN`, Betfair keys).
  The Betfair app key is a *delayed* key; `betfair_client.login()` uses the
  `login_interactive()` flow.

## Known limitations

- **Probabilities are isotonic-calibrated** (fit on 2024–2025, saved as `iso_calib.joblib`) to
  remove the favourite/longshot bias of binary win/loss training. Where the model still
  disagrees strongly with the exchange (e.g. a favourite the model rates below the market),
  that's a genuine opinion — but remember the model is ~equal to BSP, not better, so large
  disagreements are more likely model error than market inefficiency.
- A few runners show odd prices (e.g. a 4.5 when the model says 11) — those are
  SL↔Betfair horse-name matching collisions; eyeball them before betting.
- Some races/runners show `NO BF` — either the race has no Betfair win market, or the
  horse name didn't match the exchange selection. Worth a manual check.
