"""
Position Reconciliation Tool
=============================
Compares two datasets representing "positions" (e.g., an internal ledger
vs. a custodian/market data feed) and flags discrepancies ("breaks")
beyond a configurable tolerance.
"""

import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta


TICKERS = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "JPM", "V", "BRK-B"]
PRICE_TOLERANCE_PCT = 0.5
DATE_A_OFFSET_DAYS = 1
DATE_B_OFFSET_DAYS = 0


def fetch_snapshot(tickers, days_back):
    end = datetime.today()
    start = end - timedelta(days=15)

    records = {}
    for ticker in tickers:
        hist = yf.Ticker(ticker).history(start=start, end=end)
        if hist.empty:
            records[ticker] = None
            continue
        idx = max(len(hist) - 1 - days_back, 0)
        records[ticker] = round(hist["Close"].iloc[idx], 2)
    return records


def reconcile(source_a, source_b, tolerance_pct):
    rows = []
    for ticker in source_a:
        price_a = source_a.get(ticker)
        price_b = source_b.get(ticker)

        if price_a is None or price_b is None:
            rows.append({
                "ticker": ticker,
                "source_a_price": price_a,
                "source_b_price": price_b,
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
            "source_a_price": price_a,
            "source_b_price": price_b,
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
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Total positions checked: {len(df)}")
    lines.append(f"Matched (OK): {len(ok)}")
    lines.append(f"Breaks (exceeds tolerance): {len(breaks)}")
    lines.append(f"Missing data: {len(missing)}")
    lines.append("")

    if not breaks.empty:
        lines.append("BREAK DETAILS")
        lines.append("-" * 40)
        for _, row in breaks.iterrows():
            lines.append(
                f"  {row['ticker']}: Source A = {row['source_a_price']}, "
                f"Source B = {row['source_b_price']}, "
                f"Diff = {row['pct_diff']}%  -> escalate for review"
            )
    else:
        lines.append("No breaks detected beyond tolerance threshold.")

    with open(path, "w") as f:
        f.write("\n".join(lines))

    print("\n".join(lines))


def main():
    print("Fetching Source A (e.g., internal ledger snapshot)...")
    source_a = fetch_snapshot(TICKERS, DATE_A_OFFSET_DAYS)

    print("Fetching Source B (e.g., custodian/external feed snapshot)...")
    source_b = fetch_snapshot(TICKERS, DATE_B_OFFSET_DAYS)

    print("Running reconciliation...\n")
    report = reconcile(source_a, source_b, PRICE_TOLERANCE_PCT)

    report.to_csv("reconciliation_report.csv", index=False)
    write_summary(report, "reconciliation_summary.txt")

    print("\nFiles written: reconciliation_report.csv, reconciliation_summary.txt")


if __name__ == "__main__":
    main()
