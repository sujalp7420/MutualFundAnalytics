import pandas as pd
import numpy as np

# Load files
nav = pd.read_csv("data/raw/02_nav_history.csv")
tr = pd.read_csv("data/raw/08_investor_transactions.csv")
perf = pd.read_csv("data/raw/07_scheme_performance.csv")
fm = pd.read_csv("data/raw/01_fund_master.csv")
aum = pd.read_csv("data/raw/03_aum_by_fund_house.csv")

print("=== nav_history ===")
print("Nulls:\n", nav.isnull().sum())
print("Duplicates count:", nav.duplicated().sum())
print("Negative or Zero NAV count:", (nav['nav'] <= 0).sum())
print("Unique amfi_codes:", nav['amfi_code'].nunique())
print("Total rows:", len(nav))

print("\n=== investor_transactions ===")
print("Nulls:\n", tr.isnull().sum())
print("Duplicates count:", tr.duplicated().sum())
print("Transaction types unique:", tr['transaction_type'].unique())
print("KYC status unique:", tr['kyc_status'].unique())
print("Amount <= 0 count:", (tr['amount_inr'] <= 0).sum())
print("Date format examples:", tr['transaction_date'].head(5).tolist())

print("\n=== scheme_performance ===")
print("Nulls:\n", perf.isnull().sum())
print("Expense ratio column name:", [c for c in perf.columns if "expense" in c.lower()])
print("Expense ratio ranges:", perf['expense_ratio_pct'].min(), "to", perf['expense_ratio_pct'].max())
print("Any NaN or extreme return values?")
for c in perf.columns:
    if any(k in c.lower() for k in ["return", "alpha", "beta", "sharpe", "sortino", "std_dev", "max_drawdown"]):
        print(f"Col {c}: nulls = {perf[c].isnull().sum()}, min = {perf[c].min()}, max = {perf[c].max()}")
