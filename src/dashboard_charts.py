import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# ==========================================
# CONFIG
# ==========================================

DB_PATH = "data/processed/mutualfunds.db"

OUTPUT_DIR = Path("dashboard/screenshots")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

conn = sqlite3.connect(DB_PATH)

# ==========================================
# 1. INDUSTRY AUM TREND
# ==========================================

def create_aum_trend():

    query = """
    SELECT
        d.date,
        SUM(a.aum_crore) AS total_aum
    FROM fact_aum a
    JOIN dim_date d
        ON a.date_id = d.date_id
    GROUP BY d.date
    ORDER BY d.date
    """

    df = pd.read_sql(query, conn)

    df["date"] = pd.to_datetime(df["date"])

    plt.figure(figsize=(12,6))

    plt.plot(
        df["date"],
        df["total_aum"],
        marker="o"
    )

    plt.title("Industry AUM Trend")
    plt.xlabel("Date")
    plt.ylabel("AUM (Crore ₹)")
    plt.grid(True)

    plt.tight_layout()

    plt.savefig(
        OUTPUT_DIR / "Industry_Overview.png",
        dpi=300
    )

    plt.close()

    print("✓ Industry Overview generated")


# ==========================================
# 2. FUND PERFORMANCE
# ==========================================

def create_fund_performance():

    query = """
    SELECT
        f.scheme_name,
        p.return_3yr_pct,
        p.std_dev_ann_pct,
        p.aum_crore
    FROM fact_performance p
    JOIN dim_fund f
        ON p.fund_id = f.fund_id
    """

    df = pd.read_sql(query, conn)

    plt.figure(figsize=(12,8))

    plt.scatter(
        df["return_3yr_pct"],
        df["std_dev_ann_pct"],
        s=df["aum_crore"] / 100,
        alpha=0.6
    )

    plt.xlabel("3 Year Return (%)")
    plt.ylabel("Risk (Std Dev %)")
    plt.title("Fund Performance: Return vs Risk")

    plt.grid(True)

    plt.tight_layout()

    plt.savefig(
        OUTPUT_DIR / "Fund_Performance.png",
        dpi=300
    )

    plt.close()

    print("✓ Fund Performance generated")


# ==========================================
# 3. INVESTOR ANALYTICS
# ==========================================

def create_investor_analytics():

    query = """
    SELECT
        state,
        SUM(amount_inr) AS total_amount
    FROM fact_transactions
    GROUP BY state
    ORDER BY total_amount DESC
    LIMIT 15
    """

    df = pd.read_sql(query, conn)

    plt.figure(figsize=(12,7))

    plt.bar(
        df["state"],
        df["total_amount"]
    )

    plt.xticks(rotation=45)

    plt.title("Transaction Amount by State")
    plt.xlabel("State")
    plt.ylabel("Amount (₹)")

    plt.tight_layout()

    plt.savefig(
        OUTPUT_DIR / "Investor_Analytics.png",
        dpi=300
    )

    plt.close()

    print("✓ Investor Analytics generated")


# ==========================================
# 4. SIP MARKET TREND
# ==========================================

def create_sip_market_trend():

    query = """
    SELECT
        d.year,
        d.month,
        SUM(t.amount_inr) AS sip_amount
    FROM fact_transactions t
    JOIN dim_date d
        ON t.date_id = d.date_id
    WHERE t.transaction_type = 'SIP'
    GROUP BY d.year, d.month
    ORDER BY d.year, d.month
    """

    df = pd.read_sql(query, conn)

    df["period"] = (
        df["year"].astype(str)
        + "-"
        + df["month"].astype(str).str.zfill(2)
    )

    plt.figure(figsize=(14,6))

    plt.bar(
        df["period"],
        df["sip_amount"]
    )

    plt.xticks(rotation=90)

    plt.title("Monthly SIP Inflows")
    plt.xlabel("Month")
    plt.ylabel("SIP Amount (₹)")

    plt.tight_layout()

    plt.savefig(
        OUTPUT_DIR / "SIP_Market_Trends.png",
        dpi=300
    )

    plt.close()

    print("✓ SIP Market Trend generated")


# ==========================================
# MAIN
# ==========================================

if __name__ == "__main__":

    print("Generating dashboard charts...\n")

    create_aum_trend()
    create_fund_performance()
    create_investor_analytics()
    create_sip_market_trend()

    conn.close()

    print("\n✓ All charts generated successfully")