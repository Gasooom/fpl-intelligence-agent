# Fantasy Decision Intelligence

A deterministic decision-intelligence system that turns real Fantasy Premier League data into an explainable, evaluated gameweek action plan — built and served as a production-shaped FastAPI backend.


**The deterministic engine is the sole decision authority.** No LLM ever
decides starting XI, bench, captain, vice-captain, sell candidates, buy
candidates, transfers, risk, or confidence. Every recommendation is the
output of transparent, testable, reproducible rules over real data — never
a model's guess.

The system also does not stop at prediction. It records what it recommended
*before* a gameweek is played, then compares that record against real FPL
results afterward — so it can answer a question most "AI sports tools"
never even attempt:

> **Did the decision actually work?**

## What it does

Given an FPL entry ID, it answers:

- Who should start, and who sits on the bench?
- Who should be captain and vice-captain?
- Who should be sold, and who should replace them?
- What's the single strongest transfer to make this gameweek?
- What actually happened last time, versus what was predicted?

Every answer ships with structured evidence — the metrics that produced it,
not a canned explanation.

## How it works

```
Official FPL API
      ↓
Data / Metrics            (form, points-per-90, xGI/90, fixture difficulty)
      ↓
Projection + Risk + Confidence
      ↓
Squad + Transfer Intelligence
      ↓
Gameweek Decision           (starting XI, captain, ranked transfers, evidence)
      ↓
FastAPI
      ↓
UI / API
```

Three concepts stay deliberately separate rather than being collapsed into
one score:

| Concept | Question it answers |
|---|---|
| **Projection** | What output do we expect? |
| **Risk** | How reliable/available is that output? |
| **Confidence** | How strong is the evidence behind it? |
| **Decision** | What should the manager actually do? |

Then, once a gameweek is played:

```
Decision Snapshot  (written pre-gameweek, write-once)
      ↓
Real FPL Results   (official post-gameweek data)
      ↓
Evaluation         (expected vs. actual, prediction error)
```

Expected values always come from the original snapshot — not recomputed
from today's data. Actual values always come from real FPL results. There
are no simulated outcomes and no fabricated accuracy metrics.

## Deterministic Decision Engine

- **Starting XI / bench**: a bounded formation search (valid GK/DEF/MID/FWD
  combinations, 3-per-team limit) over the manager's own 15 picks — not the
  full ~650-player pool.
- **Captain / vice-captain**: ranked by a captaincy score combining
  projection, form, and fixture ease; the top pick's points count twice
  toward the projected gameweek total, exactly as FPL scores it.
- **Transfer intelligence**: every current squad player is scored for sale
  risk; the wider player pool is ranked with a single efficient pass (no
  combinatorial search) and paired against sell candidates within FPL's
  team-limit constraints. The engine surfaces one best single transfer plus
  ranked alternatives — each an independent one-transfer option, not a
  bundled plan.
- **Explainable by construction**: every score is a sum of named, inspectable
  components, so every recommendation's reasons are generated from the same
  numbers that produced the decision.

## Explainability

Every recommendation carries structured evidence based on the metrics that
produced it — never a hardcoded, per-player explanation:

```
Coppola → Bogle

- Higher expected points
- Better recent form
- Lower risk
- Stronger minutes confidence
- Better points-per-price value
```

## Evaluation

```
Prediction → Decision Snapshot → Real FPL Results → Expected vs. Actual → Prediction Error
```

Before a gameweek is played, the engine's recommendation is written once to
a local store and never overwritten — a faithful record of what was
actually recommended, immune to later data drift (form, prices, and
projections all keep moving after the fact). Once the gameweek finishes,
that snapshot is compared against official FPL results to produce:

- Whether the captain call was correct
- Starting XI vs. bench actual points, and the prediction error against the
  snapshot's expected total
- Expected vs. actual improvement for the recommended transfer
- Per-player prediction error across the full recorded squad

If a gameweek hasn't finished, or was never snapshotted, the API says so
explicitly rather than guessing.

## Architecture

```
Official FPL API
      ↓
Data / Metrics
      ↓
Projection + Risk + Confidence
      ↓
Squad + Transfer Intelligence
      ↓
Gameweek Decision
      ↓
FastAPI
      ↓
UI / API
```

## Example

Real output from the live API, gameweek 3:

```
Best transfer:  Coppola → Bogle
                +8.08 expected points

Captain:        João Pedro
                7.17 expected points · 14.34 effective points (2x)

Starting XI:    47.70 expected points
Projected gameweek total: 54.87 expected points
```

## Tech Stack

Python · FastAPI · Pydantic · SQLite · pytest · Ruff · mypy · Official FPL API

## Testing

**331 automated tests**, almost entirely deterministic and offline, covering:

- Decision logic — starting XI, bench, captaincy, must-play rules
- Projection, risk, and confidence scoring
- Transfer intelligence — sell/buy ranking, pairing, priority tiers, budget
- API contracts — request validation, error mapping, response schemas
- Decision snapshots and their write-once guarantee
- Evaluation — captain outcome, expected-vs-actual, per-player prediction
  error
- Edge cases — tiny sample sizes, missing results, tied outcomes

```
.venv/Scripts/python.exe -m pytest -q
```

## Running locally

```bash
python -m venv .venv
.venv/Scripts/activate                 # Windows (source .venv/bin/activate on macOS/Linux)

pip install -e ".[dev]"
.venv/Scripts/python.exe -m pytest -q
.venv/Scripts/python.exe -m uvicorn app.main:app --reload

# Demo page:  http://127.0.0.1:8000/
curl "http://127.0.0.1:8000/api/v1/decision/8731757"
```

No API key required — the FPL data source is public.

## Design principles

1. **The deterministic engine is the sole decision authority.** No LLM ever
   decides starting XI, captaincy, bench, transfers, risk, or confidence.
2. **Never optimize over the full player pool.** Squad decisions are bounded
   to the manager's own 15 picks; the wider pool is ranked with a single
   efficient pass, never a combinatorial search.
3. **Every recommendation carries evidence**, generated from the metrics
   that produced it.
4. **A decision is only evaluated against what genuinely happened.** No
   simulated results, no fabricated accuracy metrics — if the data to
   evaluate honestly doesn't exist yet, the API says so.

## Limitations

- Early-season, low-minute samples can inflate per-90 projections; the buy
  pool guards against this with a minimum-minutes floor, but a manager's
  own early-season squad members can still carry the same caveat.
- Budget awareness is informational (surfaced per transfer), not enforced —
  FPL's public API doesn't reliably expose enough live state to enforce it
  with confidence.
- Evaluation starts from zero history: only gameweeks snapshotted after this
  feature shipped can be evaluated. No aggregate metrics (e.g. captain
  success rate) are exposed yet — a single gameweek isn't a meaningful
  sample.

## Future direction

An optional LLM layer could narrate an already-computed decision in prose —
it would receive the final structured decision and explain it, never decide
it, invent a metric, or override a result.
