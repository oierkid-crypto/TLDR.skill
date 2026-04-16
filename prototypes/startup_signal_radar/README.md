# Startup Signal Radar v2

A cron-oriented user-needs radar for monitoring **X + Reddit** and surfacing structured signals for **2B / 2C / 2P** channels.

## Purpose

This product is now constrained to a persistent reporting workflow:

- scan **X** and **Reddit** daily
- store evidence, signals, and reports in local **SQLite**
- produce a **daily user-needs report** split into **2B / 2C / 2P**
- produce a **weekly Monday needs-insight report** from the prior week’s daily reports
- stay honest when evidence is weak: if there is no sufficiently strong signal, say so explicitly

## Current product capabilities

The current prototype already supports a meaningful local loop:

1. **Normalize** Reddit / X records into one canonical `NormalizedPost`
2. **Extract** rule-based pain, workflow, replacement intent, and AI-fit signals
3. **Route** signals into `2b`, `2c`, `2p`
4. **Assess** each surfaced signal with structured fields such as:
   - frequency count
   - cross-platform flag
   - supporting platforms
   - real-need judgment
   - confidence
   - why the need seems real
5. **Persist** evidence with stable cross-day identity instead of per-day duplication
6. **Audit** collection activity via `search_runs` and `search_hits` so repeated query hits are traceable
7. **Preserve** per-day signal history in `daily_signal_snapshots` while keeping a latest-signal view
8. **Render** user-needs-first daily and weekly report text
9. **Run** the flow from a cron-friendly CLI with safe same-day reruns (report replace, evidence upsert, run append)

## Directory layout

- `config/` — taxonomy, audience categories, and query templates
- `fixtures/` — local sample Reddit / X payloads used for deterministic iteration
- `src/` — extraction, routing, SQLite storage, daily/weekly radar logic, and CLI
- `output/` — generated report artifacts
- `state/` — legacy snapshot artifacts from the earlier fixture-only prototype

## Core outputs

### Daily report
Each daily report is split into:
- `2b`
- `2c`
- `2p`

Each surfaced signal is intended to include:
- summary of the need
- concrete evidence excerpts/content
- structured signal assessment
- honest null-result messaging when a channel lacks strong evidence

### Weekly report
Each weekly report summarizes the prior week’s recurring needs and strongest repeated patterns by channel.

## How to run

### Daily run
```bash
venv/bin/python prototypes/startup_signal_radar/src/cli.py daily \
  --date 2026-04-16 \
  --db prototypes/startup_signal_radar/output/radar.db \
  --taxonomy prototypes/startup_signal_radar/config/query_taxonomy.example.yaml
```

### Weekly run
```bash
venv/bin/python prototypes/startup_signal_radar/src/cli.py weekly \
  --week-label 2026-W16 \
  --start-date 2026-04-14 \
  --end-date 2026-04-20 \
  --db prototypes/startup_signal_radar/output/radar.db
```

## Validation

```bash
venv/bin/python -m pytest tests/prototypes -q
```

## Current limitations

- live network collection is not wired yet; current end-to-end runs still use local fixture-backed source data
- weekly summarization is intentionally simple and should be upgraded after more daily history accumulates
- routing is still explicit/rule-based rather than model-rich

## Non-goals for the current iteration

- engineering/progress reporting in the user-facing report
- pretending weak evidence is a strong demand signal
- expanding platform scope beyond X + Reddit before this loop is stable
