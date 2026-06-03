"""
Clean datasets, design SQLite schema, load cleaned data into SQLite, run analytical queries.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from sqlalchemy import create_engine, text, event
import sqlite3

RAW = Path("data/raw")
PROCESSED = Path("data/processed")
PROCESSED.mkdir(parents=True, exist_ok=True)
DB_PATH = PROCESSED / "mutualfunds.db"


# 1. Clean nav_history.csv
def clean_nav_history(df_nav: pd.DataFrame) -> pd.DataFrame:
    df = df_nav.copy()
    
    # Parse dates
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    
    # Ensure nav is numeric and > 0
    df["nav"] = pd.to_numeric(df["nav"], errors="coerce")
    df = df[df["nav"] > 0]
    
    # Remove exact duplicates
    df = df.drop_duplicates()
    
    # Sort
    df = df.sort_values(["amfi_code", "date"]).reset_index(drop=True)
    
    # Forward-fill missing NAVs for holidays/weekends per AMFI code
    filled_dfs = []
    for amfi, group in df.groupby("amfi_code"):
        group = group.drop_duplicates(subset=["date"])
        min_date = group["date"].min()
        max_date = group["date"].max()
        if pd.isna(min_date) or pd.isna(max_date):
            continue
        # Generate complete date range for the fund's timeline
        full_dates = pd.date_range(start=min_date, end=max_date, freq="D")
        group = group.set_index("date").reindex(full_dates)
        group.index.name = "date"
        group = group.reset_index()
        group["amfi_code"] = amfi
        group["nav"] = group["nav"].ffill()
        filled_dfs.append(group)
        
    if filled_dfs:
        df = pd.concat(filled_dfs, ignore_index=True)
        
    return df


# 2. Clean investor_transactions.csv
def clean_transactions(df_tr: pd.DataFrame) -> pd.DataFrame:
    df = df_tr.copy()
    
    # Fix date formats
    df["transaction_date"] = pd.to_datetime(df["transaction_date"], errors="coerce")
    df = df.dropna(subset=["transaction_date"])
    
    # Standardise transaction_type
    def map_tx(x):
        if pd.isna(x):
            return np.nan
        s = str(x).strip().lower()
        if "sip" in s:
            return "SIP"
        if "lump" in s or "one time" in s or "onet" in s:
            return "Lumpsum"
        if "red" in s or "redeem" in s:
            return "Redemption"
        return "Unknown"
        
    df["transaction_type"] = df["transaction_type"].apply(map_tx)
    df = df[df["transaction_type"] != "Unknown"]
    
    # Validate amount > 0
    df["amount_inr"] = pd.to_numeric(df["amount_inr"], errors="coerce")
    df = df[df["amount_inr"] > 0]
    
    # Check/map KYC status
    def map_kyc(x):
        if pd.isna(x):
            return "Unknown"
        s = str(x).strip().lower()
        if "verify" in s or "verified" in s:
            return "Verified"
        if "pend" in s or "pending" in s:
            return "Pending"
        if "rej" in s or "failed" in s or "rejected" in s:
            return "Rejected"
        return "Unknown"
        
    df["kyc_status"] = df["kyc_status"].apply(map_kyc)
    
    # Ensure amfi_code is clean
    df["amfi_code"] = pd.to_numeric(df["amfi_code"], errors="coerce")
    df = df.dropna(subset=["amfi_code"])
    df["amfi_code"] = df["amfi_code"].astype(int)
    
    return df.reset_index(drop=True)


# 3. Clean scheme_performance.csv
def clean_scheme_performance(df_perf: pd.DataFrame) -> pd.DataFrame:
    df = df_perf.copy()
    
    # Columns to coerce to numeric
    metric_cols = [
        "return_1yr_pct",
        "return_3yr_pct",
        "return_5yr_pct",
        "benchmark_3yr_pct",
        "alpha",
        "beta",
        "sharpe_ratio",
        "sortino_ratio",
        "std_dev_ann_pct",
        "max_drawdown_pct",
        "expense_ratio_pct"
    ]
    
    for col in metric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            
    # Flag anomalies (returns extremely high/low or missing)
    anomaly_mask = pd.Series(False, index=df.index)
    return_cols = ["return_1yr_pct", "return_3yr_pct", "return_5yr_pct"]
    for col in return_cols:
        if col in df.columns:
            anomaly_mask = anomaly_mask | df[col].isna() | (df[col].abs() > 100.0)
            
    df["anomaly_flag"] = anomaly_mask.astype(int)
    
    # Check expense_ratio range (0.1% - 2.5%)
    if "expense_ratio_pct" in df.columns:
        df["expense_flag"] = (~df["expense_ratio_pct"].between(0.1, 2.5)).astype(int)
    else:
        df["expense_flag"] = 0
        
    return df


# 4. SQLite Schema (CREATE TABLE statements)
SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS fact_aum;
DROP TABLE IF EXISTS fact_performance;
DROP TABLE IF EXISTS fact_transactions;
DROP TABLE IF EXISTS fact_nav;
DROP TABLE IF EXISTS dim_date;
DROP TABLE IF EXISTS dim_fund;

CREATE TABLE dim_fund (
  fund_id INTEGER PRIMARY KEY AUTOINCREMENT,
  amfi_code TEXT UNIQUE,
  scheme_name TEXT,
  fund_house TEXT,
  category TEXT,
  sub_category TEXT,
  plan TEXT,
  launch_date TEXT,
  benchmark TEXT,
  expense_ratio_pct REAL,
  exit_load_pct REAL,
  min_sip_amount REAL,
  min_lumpsum_amount REAL,
  fund_manager TEXT,
  risk_grade TEXT,
  sebi_category_code TEXT
);

CREATE TABLE dim_date (
  date_id INTEGER PRIMARY KEY AUTOINCREMENT,
  date TEXT UNIQUE,
  year INTEGER,
  month INTEGER,
  day INTEGER,
  quarter INTEGER
);

CREATE TABLE fact_nav (
  nav_id INTEGER PRIMARY KEY AUTOINCREMENT,
  fund_id INTEGER,
  date_id INTEGER,
  nav REAL,
  FOREIGN KEY(fund_id) REFERENCES dim_fund(fund_id),
  FOREIGN KEY(date_id) REFERENCES dim_date(date_id)
);

CREATE TABLE fact_transactions (
  tx_id INTEGER PRIMARY KEY AUTOINCREMENT,
  investor_id TEXT,
  fund_id INTEGER,
  date_id INTEGER,
  transaction_type TEXT,
  amount_inr REAL,
  kyc_status TEXT,
  state TEXT,
  city TEXT,
  city_tier TEXT,
  age_group TEXT,
  gender TEXT,
  annual_income_lakh REAL,
  payment_mode TEXT,
  FOREIGN KEY(fund_id) REFERENCES dim_fund(fund_id),
  FOREIGN KEY(date_id) REFERENCES dim_date(date_id)
);

CREATE TABLE fact_performance (
  perf_id INTEGER PRIMARY KEY AUTOINCREMENT,
  fund_id INTEGER,
  return_1yr_pct REAL,
  return_3yr_pct REAL,
  return_5yr_pct REAL,
  benchmark_3yr_pct REAL,
  alpha REAL,
  beta REAL,
  sharpe_ratio REAL,
  sortino_ratio REAL,
  std_dev_ann_pct REAL,
  max_drawdown_pct REAL,
  aum_crore REAL,
  expense_ratio_pct REAL,
  morningstar_rating INTEGER,
  anomaly_flag INTEGER DEFAULT 0,
  expense_flag INTEGER DEFAULT 0,
  FOREIGN KEY(fund_id) REFERENCES dim_fund(fund_id)
);

CREATE TABLE fact_aum (
  aum_id INTEGER PRIMARY KEY AUTOINCREMENT,
  fund_house TEXT,
  date_id INTEGER,
  aum_crore REAL,
  num_schemes INTEGER,
  FOREIGN KEY(date_id) REFERENCES dim_date(date_id)
);
"""


def create_db_and_schema(db_path: Path):
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    cur.executescript(SCHEMA_SQL)
    conn.commit()
    conn.close()


def build_dim_fund(df_fm: pd.DataFrame, engine):
    df = df_fm.copy()
    df["amfi_code"] = df["amfi_code"].astype(str)
    
    # Rename fields to match schema
    df_dim = df.rename(columns={
        "risk_category": "risk_grade"
    })
    
    dim_cols = [
        "amfi_code", "scheme_name", "fund_house", "category", "sub_category",
        "plan", "launch_date", "benchmark", "expense_ratio_pct", "exit_load_pct",
        "min_sip_amount", "min_lumpsum_amount", "fund_manager", "risk_grade", "sebi_category_code"
    ]
    df_dim = df_dim[dim_cols].drop_duplicates()
    
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM dim_fund"))
    df_dim.to_sql("dim_fund", engine, if_exists="append", index=False)
    
    with engine.connect() as conn:
        res = conn.execute(text("SELECT fund_id, amfi_code FROM dim_fund"))
        mapping = {str(row._mapping["amfi_code"]): int(row._mapping["fund_id"]) for row in res}
    return mapping


def build_dim_date(dates, engine):
    ds = pd.to_datetime(list(dates)).drop_duplicates().sort_values()
    df = pd.DataFrame({"date": ds.strftime("%Y-%m-%d")})
    df["year"] = ds.year
    df["month"] = ds.month
    df["day"] = ds.day
    df["quarter"] = ds.quarter
    
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM dim_date"))
    df.to_sql("dim_date", engine, if_exists="append", index=False)
    
    with engine.connect() as conn:
        res = conn.execute(text("SELECT date_id, date FROM dim_date"))
        mapping = {row._mapping["date"]: int(row._mapping["date_id"]) for row in res}
    return mapping


# Load all datasets into SQLite
def load_into_sqlite(clean_nav, clean_tx, clean_perf, df_aum):
    engine = create_engine(f"sqlite:///{DB_PATH}")
    
    # Register listener to enforce foreign keys on SQLite connection
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
        
    create_db_and_schema(DB_PATH)
    
    # 1. dim_fund
    df_fm = pd.read_csv(RAW / "01_fund_master.csv")
    fund_map = build_dim_fund(df_fm, engine)
    
    # 2. dim_date
    dates = set(pd.to_datetime(clean_nav["date"]).dt.strftime("%Y-%m-%d").unique())
    dates.update(pd.to_datetime(clean_tx["transaction_date"]).dt.strftime("%Y-%m-%d").unique())
    if "date" in df_aum.columns:
        dates.update(pd.to_datetime(df_aum["date"]).dt.strftime("%Y-%m-%d").unique())
    date_map = build_dim_date(dates, engine)
    
    # 3. fact_nav
    nav_rows = []
    for _, r in clean_nav.iterrows():
        amfi = str(r["amfi_code"])
        fund_id = fund_map.get(amfi)
        date_key = pd.to_datetime(r["date"]).strftime("%Y-%m-%d")
        date_id = date_map.get(date_key)
        if fund_id and date_id:
            nav_rows.append({
                "fund_id": fund_id,
                "date_id": date_id,
                "nav": float(r["nav"])
            })
    df_nav_load = pd.DataFrame(nav_rows)
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM fact_nav"))
    df_nav_load.to_sql("fact_nav", engine, if_exists="append", index=False)
    
    # 4. fact_transactions
    tx_rows = []
    for _, r in clean_tx.iterrows():
        amfi = str(r["amfi_code"])
        fund_id = fund_map.get(amfi)
        date_key = pd.to_datetime(r["transaction_date"]).strftime("%Y-%m-%d")
        date_id = date_map.get(date_key)
        if fund_id and date_id:
            tx_rows.append({
                "investor_id": r.get("investor_id"),
                "fund_id": fund_id,
                "date_id": date_id,
                "transaction_type": r.get("transaction_type"),
                "amount_inr": float(r.get("amount_inr")),
                "kyc_status": r.get("kyc_status"),
                "state": r.get("state"),
                "city": r.get("city"),
                "city_tier": r.get("city_tier"),
                "age_group": r.get("age_group"),
                "gender": r.get("gender"),
                "annual_income_lakh": float(r.get("annual_income_lakh")) if pd.notna(r.get("annual_income_lakh")) else None,
                "payment_mode": r.get("payment_mode")
            })
    df_tx_load = pd.DataFrame(tx_rows)
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM fact_transactions"))
    df_tx_load.to_sql("fact_transactions", engine, if_exists="append", index=False)
    
    # 5. fact_performance
    perf_rows = []
    for _, r in clean_perf.iterrows():
        amfi = str(r["amfi_code"])
        fund_id = fund_map.get(amfi)
        if fund_id:
            perf_rows.append({
                "fund_id": fund_id,
                "return_1yr_pct": float(r.get("return_1yr_pct")) if pd.notna(r.get("return_1yr_pct")) else None,
                "return_3yr_pct": float(r.get("return_3yr_pct")) if pd.notna(r.get("return_3yr_pct")) else None,
                "return_5yr_pct": float(r.get("return_5yr_pct")) if pd.notna(r.get("return_5yr_pct")) else None,
                "benchmark_3yr_pct": float(r.get("benchmark_3yr_pct")) if pd.notna(r.get("benchmark_3yr_pct")) else None,
                "alpha": float(r.get("alpha")) if pd.notna(r.get("alpha")) else None,
                "beta": float(r.get("beta")) if pd.notna(r.get("beta")) else None,
                "sharpe_ratio": float(r.get("sharpe_ratio")) if pd.notna(r.get("sharpe_ratio")) else None,
                "sortino_ratio": float(r.get("sortino_ratio")) if pd.notna(r.get("sortino_ratio")) else None,
                "std_dev_ann_pct": float(r.get("std_dev_ann_pct")) if pd.notna(r.get("std_dev_ann_pct")) else None,
                "max_drawdown_pct": float(r.get("max_drawdown_pct")) if pd.notna(r.get("max_drawdown_pct")) else None,
                "aum_crore": float(r.get("aum_crore")) if pd.notna(r.get("aum_crore")) else None,
                "expense_ratio_pct": float(r.get("expense_ratio_pct")) if pd.notna(r.get("expense_ratio_pct")) else None,
                "morningstar_rating": int(r.get("morningstar_rating")) if pd.notna(r.get("morningstar_rating")) else None,
                "anomaly_flag": int(r.get("anomaly_flag", 0)),
                "expense_flag": int(r.get("expense_flag", 0))
            })
    df_perf_load = pd.DataFrame(perf_rows)
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM fact_performance"))
    df_perf_load.to_sql("fact_performance", engine, if_exists="append", index=False)
    
    # 6. fact_aum
    aum_rows = []
    for _, r in df_aum.iterrows():
        date_key = pd.to_datetime(r["date"]).strftime("%Y-%m-%d")
        date_id = date_map.get(date_key)
        if date_id:
            aum_rows.append({
                "fund_house": r.get("fund_house"),
                "date_id": date_id,
                "aum_crore": float(r.get("aum_crore")),
                "num_schemes": int(r.get("num_schemes"))
            })
    df_aum_load = pd.DataFrame(aum_rows)
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM fact_aum"))
    df_aum_load.to_sql("fact_aum", engine, if_exists="append", index=False)
    
    # Row counts verification
    with engine.connect() as conn:
        nav_count = conn.execute(text("SELECT COUNT(*) as c FROM fact_nav")).fetchone()[0]
        tx_count = conn.execute(text("SELECT COUNT(*) as c FROM fact_transactions")).fetchone()[0]
        perf_count = conn.execute(text("SELECT COUNT(*) as c FROM fact_performance")).fetchone()[0]
        aum_count = conn.execute(text("SELECT COUNT(*) as c FROM fact_aum")).fetchone()[0]
        
    print("\n[ROW COUNT VERIFICATION]")
    print(f"fact_nav: Cleaned df={len(clean_nav)}, SQLite={nav_count}")
    print(f"fact_transactions: Cleaned df={len(clean_tx)}, SQLite={tx_count}")
    print(f"fact_performance: Cleaned df={len(clean_perf)}, SQLite={perf_count}")
    print(f"fact_aum: Raw df={len(df_aum)}, SQLite={aum_count}")
    
    return engine


# Analytical queries definition
QUERIES = [
    (
        "1. Top 5 funds by AUM",
        """
        SELECT df.scheme_name, fp.aum_crore 
        FROM fact_performance fp 
        JOIN dim_fund df ON fp.fund_id = df.fund_id 
        ORDER BY fp.aum_crore DESC 
        LIMIT 5;
        """
    ),
    (
        "2. Average NAV per month for each fund (sample)",
        """
        SELECT df.scheme_name, dd.year, dd.month, ROUND(AVG(f.nav), 4) as avg_nav 
        FROM fact_nav f 
        JOIN dim_fund df ON f.fund_id = df.fund_id 
        JOIN dim_date dd ON f.date_id = dd.date_id 
        GROUP BY df.scheme_name, dd.year, dd.month 
        ORDER BY df.scheme_name, dd.year, dd.month 
        LIMIT 10;
        """
    ),
    (
        "3. SIP YoY Growth",
        """
        WITH sip_by_year AS (
          SELECT dd.year, SUM(ft.amount_inr) as total_sip
          FROM fact_transactions ft
          JOIN dim_date dd ON ft.date_id = dd.date_id
          WHERE ft.transaction_type = 'SIP'
          GROUP BY dd.year
        )
        SELECT 
          curr.year, 
          curr.total_sip as current_year_sip,
          prev.total_sip as previous_year_sip,
          ROUND(((curr.total_sip - prev.total_sip) * 100.0 / prev.total_sip), 2) as yoy_growth_pct
        FROM sip_by_year curr
        LEFT JOIN sip_by_year prev ON curr.year = prev.year + 1
        ORDER BY curr.year;
        """
    ),
    (
        "4. Transactions by State",
        """
        SELECT state, COUNT(*) as tx_count, SUM(amount_inr) as total_amount 
        FROM fact_transactions 
        GROUP BY state 
        ORDER BY tx_count DESC 
        LIMIT 10;
        """
    ),
    (
        "5. Funds with expense_ratio < 1%",
        """
        SELECT df.scheme_name, fp.expense_ratio_pct 
        FROM fact_performance fp 
        JOIN dim_fund df ON fp.fund_id = df.fund_id 
        WHERE fp.expense_ratio_pct < 1.0 
        ORDER BY fp.expense_ratio_pct ASC;
        """
    ),
    (
        "6. Top 5 funds by 3-year return",
        """
        SELECT df.scheme_name, fp.return_3yr_pct 
        FROM fact_performance fp 
        JOIN dim_fund df ON fp.fund_id = df.fund_id 
        ORDER BY fp.return_3yr_pct DESC 
        LIMIT 5;
        """
    ),
    (
        "7. Total transactions, amount, and average size by Gender",
        """
        SELECT gender, COUNT(*) as tx_count, SUM(amount_inr) as total_amount, ROUND(AVG(amount_inr), 2) as avg_amount 
        FROM fact_transactions 
        GROUP BY gender;
        """
    ),
    (
        "8. Average expense ratio by category",
        """
        SELECT df.category, COUNT(*) as fund_count, ROUND(AVG(fp.expense_ratio_pct), 2) as avg_expense_ratio 
        FROM fact_performance fp 
        JOIN dim_fund df ON fp.fund_id = df.fund_id 
        GROUP BY df.category 
        ORDER BY avg_expense_ratio DESC;
        """
    ),
    (
        "9. KYC status breakdown by City Tier",
        """
        SELECT city_tier, kyc_status, COUNT(*) as tx_count 
        FROM fact_transactions 
        GROUP BY city_tier, kyc_status 
        ORDER BY city_tier, tx_count DESC;
        """
    ),
    (
        "10. Top 5 dates with highest total transaction volume",
        """
        SELECT dd.date, COUNT(*) as tx_count, SUM(ft.amount_inr) as total_amount 
        FROM fact_transactions ft 
        JOIN dim_date dd ON ft.date_id = dd.date_id 
        GROUP BY dd.date 
        ORDER BY total_amount DESC 
        LIMIT 5;
        """
    )
]


def run_queries(engine):
    with engine.connect() as conn:
        print("\n=== RUNNING ANALYTICAL QUERIES ===")
        for title, q in QUERIES:
            print(f"\n-- {title}")
            try:
                res = conn.execute(text(q)).fetchall()
                for row in res[:10]:
                    print(dict(row._mapping))
                print(f"Total rows returned: {len(res)}")
            except Exception as e:
                print("Query error:", e)


if __name__ == "__main__":
    print("Loading raw CSV files...")
    df_nav = pd.read_csv(RAW / "02_nav_history.csv")
    df_tr = pd.read_csv(RAW / "08_investor_transactions.csv")
    df_perf = pd.read_csv(RAW / "07_scheme_performance.csv")
    df_aum = pd.read_csv(RAW / "03_aum_by_fund_house.csv")
    
    print("Cleaning nav_history...")
    clean_nav = clean_nav_history(df_nav)
    
    print("Cleaning investor_transactions...")
    clean_tx = clean_transactions(df_tr)
    
    print("Cleaning scheme_performance...")
    clean_perf = clean_scheme_performance(df_perf)
    
    # Save cleaned files to processed directory
    clean_nav.to_csv(PROCESSED / "nav_history_cleaned.csv", index=False)
    clean_tx.to_csv(PROCESSED / "investor_transactions_cleaned.csv", index=False)
    clean_perf.to_csv(PROCESSED / "scheme_performance_cleaned.csv", index=False)
    print("Cleaned CSVs saved to", PROCESSED)
    
    # Load into SQLite
    print("Loading data into SQLite...")
    engine = load_into_sqlite(clean_nav, clean_tx, clean_perf, df_aum)
    
    # Run SQL Queries
    run_queries(engine)
