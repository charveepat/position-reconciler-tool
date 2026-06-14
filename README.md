# Position Reconciliation Tool

A Python tool that automates a core investment operations workflow:
comparing end-of-day prices from two independent sources — an internal
portfolio management system (PMS) and a custodian bank — and flagging
discrepancies ("breaks") that exceed a defined tolerance threshold.

## The problem it solves

Investment operations teams receive end-of-day pricing from multiple
vendors every night. The internal PMS and the custodian (e.g. State Street,
BNY Mellon) should report the same closing price for the same date, but
they frequently diverge due to:

- Rounding and decimal truncation differences between systems
- Stale or delayed feed ticks from one vendor
- Corporate action adjustments applied inconsistently
- Currency conversion timing differences

Manual line-by-line comparison across hundreds of positions is slow and
error-prone. This tool automates that comparison and produces a clean
exception report — only what needs human review gets surfaced.

## How it works

1. Fetches the most recent official closing price for a configurable set
   of tickers from Yahoo Finance, representing the **internal PMS feed**
   (Source A).
2. Simulates a **custodian end-of-day feed** (Source B) for the same
   pricing date by applying small random noise to the same baseline prices.
   This models the realistic variance caused by rounding conventions, minor
   feed latency, and vendor-specific price adjustment logic. In production,
   this feed would be replaced by the actual custodian file (CSV, SWIFT
   MT535, or API response).
3. Reconciles each position: calculates the absolute and percentage
   difference between the two sources.
4. Flags any position where the difference exceeds the tolerance threshold
   (default: 0.5%) as a **BREAK** requiring escalation.
5. Outputs:
   - `reconciliation_report.csv` — full line-by-line comparison
   - `reconciliation_summary.txt` — summary with break details

## Key design choices

- **Same pricing date, two sources**: both feeds represent the same
  end-of-day snapshot. Differences are data quality issues, not market
  movement — which is exactly the scenario ops teams reconcile against.
- **Configurable tolerance**: `PRICE_TOLERANCE_PCT` can be tightened (e.g.
  0.01% for fixed income) or relaxed depending on asset class and firm
  policy.
- **Seeded noise**: `RANDOM_SEED` makes custodian simulation reproducible
  across runs, useful for testing and demonstration.

## Requirements

```
pip install yfinance pandas
```

## How to run

```
python reconciler.py
```

## Sample output

```
RECONCILIATION SUMMARY
========================================
Generated:               2025-06-14 09:30:00
Pricing date:            2025-06-13 (most recent close)
Total positions checked: 10
Matched (OK):            6
Breaks (> 0.5%):         4
Missing data:            0

BREAK DETAILS  — escalate for review
----------------------------------------
  TSLA    PMS = $399.15  |  Custodian = $403.21  |  Diff = +1.0165%
  JPM     PMS = $313.49  |  Custodian = $310.82  |  Diff = -0.8516%
```

## Extending for production

- Replace `simulate_custodian_feed()` with a parser for your custodian's
  actual delivery format (CSV export, SWIFT MT535, FTP file, or REST API).
- Replace `fetch_reference_prices()` with your PMS data export or
  internal database query.
- Adjust `PRICE_TOLERANCE_PCT` to match your firm's operational threshold.
- Route BREAK records to an email or Slack alert for same-day resolution.

## About

Built by [Charvee Patel](https://github.com/charveepat) — MS Finance (Data
Analytics), UIUC Gies College of Business. Demonstrates automated data
reconciliation and exception reporting relevant to investment operations,
fund accounting, and FP&A workflows.
