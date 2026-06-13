# Position Reconciliation Tool

A Python tool that automates a core investment operations task:
**comparing two data sources for the same set of positions and flagging
discrepancies ("breaks") that exceed a defined tolerance.**

## Why This Exists

Investment operations teams routinely reconcile data between internal
ledgers, custodian feeds, and market data providers. Manual line-by-line
comparison is slow and error-prone. This tool automates that comparison
and produces a clean exception report highlighting only what needs
human review.

## How It Works

1. Pulls real, public market price data for 10 large-cap tickers from
   Yahoo Finance (via `yfinance`) — representing two "snapshots" of the
   same positions (yesterday's close vs. today's close, simulating an
   internal record vs. an external feed).
2. Compares each position across both sources.
3. Calculates absolute and percentage differences.
4. Flags any position where the difference exceeds a configurable
   tolerance (default: 0.5%) as a **BREAK**.
5. Outputs:
   - `reconciliation_report.csv` — full line-by-line comparison
   - `reconciliation_summary.txt` — summary with break details

## Requirements

```
pip install yfinance pandas
```

## How to Run

```
python reconciler.py
```

## Sample Output

```
RECONCILIATION SUMMARY
========================================
Total positions checked: 10
Matched (OK): 3
Breaks (exceeds tolerance): 7

BREAK DETAILS
----------------------------------------
  TSLA: Source A = 399.15, Source B = 406.43, Diff = 1.82%  -> escalate for review
  JPM: Source A = 313.49, Source B = 320.72, Diff = 2.31%  -> escalate for review
```

## Extending This Tool

- Replace the Yahoo Finance snapshots with real internal ledger exports
  vs. custodian statements for production use.
- Adjust `PRICE_TOLERANCE_PCT` to match operational thresholds.
- Add email/Slack alerts for breaks.

## About

Built by [Charvee Patel](https://github.com/charveepat) — MS Finance (Data
Analytics), UIUC Gies College of Business. Demonstrates automated data
reconciliation and exception reporting relevant to investment operations
and FP&A workflows.
