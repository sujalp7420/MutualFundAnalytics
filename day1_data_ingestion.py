"""
Mutual Fund Data Analysis - Day 1: Data Ingestion and Exploration
This script loads CSVs, fetches live NAV data, and validates data quality
"""

import pandas as pd
import numpy as np
import os
import json
import requests
from pathlib import Path
from datetime import datetime

# Setup paths
RAW_DATA_PATH = Path("data/raw")
PROCESSED_DATA_PATH = Path("data/processed")

print("=" * 80)
print("MUTUAL FUND DATA INGESTION - DAY 1")
print("=" * 80)
print(f"Timestamp: {datetime.now()}\n")

# ============================================================================
# TASK 3: Load and Explore CSV Datasets
# ============================================================================
print("\n" + "=" * 80)
print("TASK 3: LOADING AND EXPLORING CSV DATASETS")
print("=" * 80)

# Expected CSV files (looking for common mutual fund related CSVs)
expected_csvs = [
    "fund_master.csv",
    "nav_history.csv",
    "scheme_details.csv",
    "aum_history.csv",
    "expense_ratio.csv",
    "fund_returns.csv",
    "portfolio_holdings.csv",
    "fund_categories.csv",
    "scheme_codes.csv",
    "historical_nav.csv",
]

# Check for available CSVs
available_csvs = []
missing_csvs = []

for csv_file in expected_csvs:
    csv_path = RAW_DATA_PATH / csv_file
    if csv_path.exists():
        available_csvs.append(csv_file)
    else:
        missing_csvs.append(csv_file)

print(f"\nAvailable CSV files: {len(available_csvs)}")
if available_csvs:
    for csv_file in available_csvs:
        print(f"  ✓ {csv_file}")
else:
    print("  No CSV files found in data/raw/")

if missing_csvs:
    print(f"\nMissing CSV files: {len(missing_csvs)}")
    print("Please place the following CSV files in data/raw/:")
    for csv_file in missing_csvs:
        print(f"  ✗ {csv_file}")

# Load and explore available CSVs
data_frames = {}
anomalies = {}

for csv_file in available_csvs:
    csv_path = RAW_DATA_PATH / csv_file
    try:
        print(f"\n{'-' * 80}")
        print(f"Loading: {csv_file}")
        print(f"{'-' * 80}")

        df = pd.read_csv(csv_path)
        data_frames[csv_file.replace(".csv", "")] = df

        print(f"Shape: {df.shape}")
        print(f"\nData Types:\n{df.dtypes}")
        print(f"\nFirst 5 rows:")
        print(df.head())

        # Check for anomalies
        print(f"\nData Quality Checks:")
        print(f"  - Null values: {df.isnull().sum().sum()}")
        print(f"  - Duplicates: {df.duplicated().sum()}")
        print(f"  - Memory usage: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")

        # Record anomalies
        anomalies[csv_file.replace(".csv", "")] = {
            "null_count": df.isnull().sum().sum(),
            "duplicate_count": df.duplicated().sum(),
            "memory_mb": df.memory_usage(deep=True).sum() / 1024**2,
        }

    except Exception as e:
        print(f"ERROR loading {csv_file}: {str(e)}")
        anomalies[csv_file.replace(".csv", "")] = {"error": str(e)}

# ============================================================================
# TASK 4: Fetch Live NAV from mfapi.in
# ============================================================================
print("\n" + "=" * 80)
print("TASK 4: FETCHING LIVE NAV FROM MFAPI.IN")
print("=" * 80)

# Fetch HDFC Top 100 Direct (125497)
hdfc_scheme_code = 125497
url = f"https://api.mfapi.in/mf/{hdfc_scheme_code}"

try:
    print(f"\nFetching NAV for HDFC Top 100 Direct (Code: {hdfc_scheme_code})")
    print(f"URL: {url}")

    response = requests.get(url, timeout=10)
    response.raise_for_status()

    data = response.json()

    print(f"Status: SUCCESS")
    print(f"Response Keys: {data.keys()}")

    if "meta" in data:
        print(f"\nMetadata:")
        for key, value in data["meta"].items():
            print(f"  {key}: {value}")

    # Extract NAV data and save as CSV
    if "data" in data:
        nav_data = data["data"]
        df_nav = pd.DataFrame(nav_data)

        # Save to raw CSV
        hdfc_csv_path = RAW_DATA_PATH / "hdfc_top_100_direct.csv"
        df_nav.to_csv(hdfc_csv_path, index=False)
        print(f"\nSaved NAV data: {hdfc_csv_path}")
        print(f"Records: {len(df_nav)}")
        print(f"Columns: {list(df_nav.columns)}")
        print(f"\nFirst 5 records:")
        print(df_nav.head())

except requests.exceptions.RequestException as e:
    print(f"ERROR: Failed to fetch data: {str(e)}")
except json.JSONDecodeError as e:
    print(f"ERROR: Failed to parse JSON response: {str(e)}")
except Exception as e:
    print(f"ERROR: {str(e)}")

# ============================================================================
# TASK 5: Fetch NAV for 5 Key Schemes
# ============================================================================
print("\n" + "=" * 80)
print("TASK 5: FETCHING NAV FOR 5 KEY SCHEMES")
print("=" * 80)

key_schemes = {
    "SBI Bluechip": 119551,
    "ICICI Bluechip": 120503,
    "Nippon Large Cap": 118632,
    "Axis Bluechip": 119092,
    "Kotak Bluechip": 120841,
}

scheme_nav_data = {}

for scheme_name, scheme_code in key_schemes.items():
    try:
        url = f"https://api.mfapi.in/mf/{scheme_code}"
        print(f"\nFetching: {scheme_name} (Code: {scheme_code})")

        response = requests.get(url, timeout=10)
        response.raise_for_status()

        data = response.json()
        scheme_nav_data[scheme_name] = data

        if "meta" in data:
            print(f"  ✓ Fund House: {data['meta'].get('fund_house', 'N/A')}")
            print(f"  ✓ Scheme Type: {data['meta'].get('scheme_type', 'N/A')}")
            print(f"  ✓ Latest NAV: {data['meta'].get('nav', 'N/A')}")

        if "data" in data:
            df_scheme = pd.DataFrame(data["data"])
            csv_filename = (
                RAW_DATA_PATH / f"{scheme_name.lower().replace(' ', '_')}_nav.csv"
            )
            df_scheme.to_csv(csv_filename, index=False)
            print(f"  ✓ Saved: {csv_filename} ({len(df_scheme)} records)")

    except Exception as e:
        print(f"  ✗ ERROR: {str(e)}")

# ============================================================================
# TASK 6: Explore Fund Master
# ============================================================================
print("\n" + "=" * 80)
print("TASK 6: EXPLORING FUND MASTER")
print("=" * 80)

if "fund_master" in data_frames:
    df_fm = data_frames["fund_master"]

    print(f"\nDataset Shape: {df_fm.shape}")
    print(f"Columns: {list(df_fm.columns)}\n")

    # Unique fund houses
    if "Fund_House" in df_fm.columns or "fund_house" in df_fm.columns:
        col = "Fund_House" if "Fund_House" in df_fm.columns else "fund_house"
        unique_houses = df_fm[col].nunique()
        print(f"Unique Fund Houses: {unique_houses}")
        print(f"Fund Houses: {df_fm[col].unique()[:10]}...")

    # Categories
    if "Category" in df_fm.columns or "category" in df_fm.columns:
        col = "Category" if "Category" in df_fm.columns else "category"
        print(f"\nUnique Categories: {df_fm[col].nunique()}")
        print(f"Categories: {df_fm[col].unique()}")

    # Sub-categories
    if "Sub_Category" in df_fm.columns or "sub_category" in df_fm.columns:
        col = "Sub_Category" if "Sub_Category" in df_fm.columns else "sub_category"
        print(f"\nUnique Sub-Categories: {df_fm[col].nunique()}")
        print(f"Sub-Categories: {df_fm[col].unique()[:10]}...")

    # Risk grades
    if "Risk_Grade" in df_fm.columns or "risk_grade" in df_fm.columns:
        col = "Risk_Grade" if "Risk_Grade" in df_fm.columns else "risk_grade"
        print(f"\nUnique Risk Grades: {df_fm[col].nunique()}")
        print(f"Risk Grades: {df_fm[col].unique()}")

    # AMFI code structure
    if (
        "AMFI_Code" in df_fm.columns
        or "amfi_code" in df_fm.columns
        or "Scheme_Code" in df_fm.columns
    ):
        code_col = None
        for col in ["AMFI_Code", "amfi_code", "Scheme_Code", "scheme_code"]:
            if col in df_fm.columns:
                code_col = col
                break

        if code_col:
            print(f"\nAMFI Code Structure Analysis:")
            print(f"Total Unique Codes: {df_fm[code_col].nunique()}")
            print(f"Sample Codes: {df_fm[code_col].head(10).tolist()}")
            print(f"Code Range: {df_fm[code_col].min()} to {df_fm[code_col].max()}")

else:
    print("fund_master.csv not found. Please upload it to data/raw/")

# ============================================================================
# TASK 7 & 8: Validate AMFI Codes and Data Quality
# ============================================================================
print("\n" + "=" * 80)
print("TASK 7 & 8: DATA QUALITY VALIDATION")
print("=" * 80)

data_quality_summary = {
    "timestamp": datetime.now().isoformat(),
    "csv_files_loaded": len(available_csvs),
    "csv_files_missing": len(missing_csvs),
    "anomalies": anomalies,
    "api_calls": {
        "hdfc_top_100": (
            "success"
            if RAW_DATA_PATH / "hdfc_top_100_direct.csv"
            in list(RAW_DATA_PATH.glob("*"))
            else "failed"
        ),
        "key_schemes": len(scheme_nav_data),
    },
}

# Check AMFI code consistency (if both files exist)
if "fund_master" in data_frames and "nav_history" in data_frames:
    df_fm = data_frames["fund_master"]
    df_nav = data_frames["nav_history"]

    # Find AMFI code columns
    fm_code_col = None
    nav_code_col = None

    for col in ["AMFI_Code", "amfi_code", "Scheme_Code"]:
        if col in df_fm.columns:
            fm_code_col = col
            break

    for col in ["AMFI_Code", "amfi_code", "Scheme_Code"]:
        if col in df_nav.columns:
            nav_code_col = col
            break

    if fm_code_col and nav_code_col:
        fm_codes = set(df_fm[fm_code_col].unique())
        nav_codes = set(df_nav[nav_code_col].unique())

        missing_in_nav = fm_codes - nav_codes
        extra_in_nav = nav_codes - fm_codes

        print(f"\nAMFI Code Validation:")
        print(f"  Codes in fund_master: {len(fm_codes)}")
        print(f"  Codes in nav_history: {len(nav_codes)}")
        print(f"  Missing in nav_history: {len(missing_in_nav)}")
        print(f"  Extra in nav_history: {len(extra_in_nav)}")

        if missing_in_nav:
            print(f"\n  Sample missing codes: {list(missing_in_nav)[:5]}")

# Save data quality summary
print("\n" + "=" * 80)
print("DATA QUALITY SUMMARY")
print("=" * 80)
print(json.dumps(data_quality_summary, indent=2, default=str))

# Save summary to file
summary_path = PROCESSED_DATA_PATH / "data_quality_summary.json"
with open(summary_path, "w") as f:
    json.dump(data_quality_summary, f, indent=2, default=str)
print(f"\nSummary saved to: {summary_path}")

print("\n" + "=" * 80)
print("DATA INGESTION COMPLETE")
print("=" * 80)
