"""
Position Reconciliation Tool
=============================
Compares two end-of-day price sources for the same set of positions and flags
discrepancies ("breaks") that exceed a configurable tolerance.

Context: Investment operations teams receive end-of-day pricing from multiple
vendors — an internal portfolio management system (PMS) and a custodian bank
(e.g. State Street, BNY Mellon). Both should report the same closing price for
the same date, but diverge due to rounding conventions, stale feeds, corporate
action handling differences, or vendor data quality issues. This tool automates
the line-by-line comparison and surfaces only the exceptions that need review.

Source A: Simulates the internal PMS feed (yesterday's official closing price
          from Yahoo Finance, used as the authoritative baseline).
Source B: Simulates the custodian feed for the same date — same underlying
          price, with small random noise added to represent real-world vendor
          discrepancies (rounding, delayed ticks, decimal truncation).
"""

import random
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta


TICKERS = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "JPM", "V", "BRK-B"]

# Tolerance: breaks are flagged only when the two sources disagree by more than
# this percentage. 0.5% is typical for equities ops; tighten to 0.01% for
# fixed income where pricing precision requirements are much stricter.
PRICE_TOLERANCE_PCT = 0.5

# Maximum random noise applied to Source B to simulate custodian feed variance.
# Keeps differences realistic — most positions will be within tolerance.
MAX_CUSTODIAN_NOISE_PCT = 1.5

RANDOM_SEED = 42


def fetch_reference_prices(tickers):
    """Fetch the most recent closing price for each ticker (Source A baseline)."""
    end = datetime.today()
    start = end - timedelta(days=10)

    prices = {}
    for ticker in tickers:
        hist = yf.Ticker(ticker).history(start=start, end=end)
        if hist.empty:
            prices[ticker] = None
            continue
        prices[ticker] = round(float(hist["Close"].iloc[-1]), 2)
    return prices


def simulate_custodian_feed(reference_prices, max_noise_pct, seed):
    """
    Simulate a custodian's end-of-day feed for the same pricing date.

    In production this would be replaced by a real custodian file (CSV, SWIFT
    MT535, or API response). The noise distribution here models common causes
    of real-world breaks: decimal rounding differences, minor feed latency, and
    vendor-specific price adjustment conventions.
    """
    rng = random.Random(seed)
    custodian = {}
    for ticker, price in reference_prices.items():
        if price is None:
            custodian[ticker] = None
            continue
        noise_pct = rng.uniform(-max_noise_pct, max_noise_pct)
        custodian[ticker] = round(price * (1 + noise_pct / 100), 2)
    return custodian


def reconcile(source_a, source_b, tolerance_pct):
    rows = []
    for ticker in source_a:
        price_a = source_a.get(ticker)
        price_b = source_b.get(ticker)

        if price_a is None or price_b is None:
            rows.append({
                "ticker": ticker,
                "pms_price": price_a,
                "custodian_price": price_b,
                "abs_diff": None,
                "pct_diff": None,
                "status": "MISSING_DATA",
            })
            continue

        abs_diff = round(price_b - price_a, 4)
        pct_diff = round((abs_diff / price_a) * 100, 4) if price_a != 0 else None
        status = "BREAK" if abs(pct_diff) > tolerance_pct else "OK"

        rows.append({
            "ticker": ticker,
            "pms_price": price_a,
            "custodian_price": price_b,
            "abs_diff": abs_diff,
            "pct_diff": pct_diff,
            "status": status,
        })

    return pd.DataFrame(rows)


def write_summary(df, path):
    breaks = df[df["status"] == "BREAK"]
    missing = df[df["status"] == "MISSING_DATA"]
    ok = df[df["status"] == "OK"]

    lines = []
    lines.append("RECONCILIATION SUMMARY")
    lines.append("=" * 40)
    lines.append(f"Generated:               {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Pricing date:            {(datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')} (most recent close)")
    lines.append(f"Total positions checked: {len(df)}")
    lines.append(f"Matched (OK):            {len(ok)}")
    lines.append(f"Breaks (> {PRICE_TOLERANCE_PCT}%):         {len(breaks)}")
    lines.append(f"Missing data:            {len(missing)}")
    lines.append("")

    if not breaks.empty:
        lines.append("BREAK DETAILS  — escalate for review")
        lines.append("-" * 40)
        for _, row in breaks.iterrows():
            lines.append(
                f"  {row['ticker']:6s}  PMS = ${row['pms_price']:.2f}  |  "
                f"Custodian = ${row['custodian_price']:.2f}  |  "
                f"Diff = {row['pct_diff']:+.4f}%"
            )
    else:
        lines.append("No breaks detected beyond tolerance threshold.")

    with open(path, "w") as f:
        f.write("\n".join(lines))

    print("\n".join(lines))


def main():
    print("Fetching reference prices (internal PMS feed)...")
    source_a = fetch_reference_prices(TICKERS)

    print("Simulating custodian end-of-day feed for the same pricing date...")
    source_b = simulate_custodian_feed(source_a, MAX_CUSTODIAN_NOISE_PCT, RANDOM_SEED)

    print("Running reconciliation...\n")
    report = reconcile(source_a, source_b, PRICE_TOLERANCE_PCT)

    report.to_csv("reconciliation_report.csv", index=False)
    write_summary(report, "reconciliation_summary.txt")

    print("\nFiles written: reconciliation_report.csv, reconciliation_summary.txt")


if __name__ == "__main__":
    main()
