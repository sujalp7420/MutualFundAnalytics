"""
Mutual Fund Data Analysis - Enhanced Data Ingestion Script
With retry logic, better error handling, and comprehensive logging
"""

import pandas as pd
import numpy as np
import os
import json
import requests
from pathlib import Path
from datetime import datetime
from time import sleep
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Setup paths
RAW_DATA_PATH = Path("data/raw")
PROCESSED_DATA_PATH = Path("data/processed")


# Configure requests with retry strategy
def create_session_with_retries(retries=3, backoff_factor=0.5, timeout=20):
    """Create a requests session with retry logic"""
    session = requests.Session()

    retry_strategy = Retry(
        total=retries,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        backoff_factor=backoff_factor,
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    return session


print("=" * 80)
print("MUTUAL FUND DATA INGESTION - ENHANCED VERSION")
print("=" * 80)
print(f"Timestamp: {datetime.now()}\n")

# ============================================================================
# TASK 3: Load and Explore CSV Datasets
# ============================================================================
print("\n" + "=" * 80)
print("TASK 3: LOADING AND EXPLORING CSV DATASETS")
print("=" * 80)

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

available_csvs = []
missing_csvs = []

for csv_file in expected_csvs:
    csv_path = RAW_DATA_PATH / csv_file
    if csv_path.exists():
        available_csvs.append(csv_file)
    else:
        missing_csvs.append(csv_file)

print(f"\nAvailable CSV files: {len(available_csvs)}/{len(expected_csvs)}")
if available_csvs:
    for csv_file in available_csvs:
        print(f"  ✓ {csv_file}")

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

        print(f"✓ Shape: {df.shape}")
        print(f"✓ Columns: {list(df.columns)[:5]}...")
        print(f"✓ Memory: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
        print(f"✓ Null values: {df.isnull().sum().sum()}")
        print(f"✓ Duplicates: {df.duplicated().sum()}")

        # Data types
        print(f"\nData Types:")
        for col, dtype in df.dtypes.items()[:5]:
            print(f"  - {col}: {dtype}")

        print(f"\nFirst 3 rows:")
        print(df.head(3).to_string())

        anomalies[csv_file.replace(".csv", "")] = {
            "null_count": int(df.isnull().sum().sum()),
            "duplicate_count": int(df.duplicated().sum()),
            "memory_mb": float(df.memory_usage(deep=True).sum() / 1024**2),
            "shape": df.shape,
        }

    except Exception as e:
        print(f"✗ ERROR loading {csv_file}: {str(e)}")
        anomalies[csv_file.replace(".csv", "")] = {"error": str(e)}

if missing_csvs:
    print(f"\n⚠️  Missing CSV files ({len(missing_csvs)}):")
    for csv_file in missing_csvs[:5]:
        print(f"  ✗ {csv_file}")
    if len(missing_csvs) > 5:
        print(f"  ... and {len(missing_csvs) - 5} more")

# ============================================================================
# TASK 4: Fetch Live NAV from mfapi.in with Retry Logic
# ============================================================================
print("\n" + "=" * 80)
print("TASK 4: FETCHING LIVE NAV FROM MFAPI.IN")
print("=" * 80)

session = create_session_with_retries(retries=3, timeout=20)
hdfc_scheme_code = 125497
url = f"https://api.mfapi.in/mf/{hdfc_scheme_code}"

try:
    print(f"\nFetching NAV for HDFC Top 100 Direct (Code: {hdfc_scheme_code})")
    print(f"URL: {url}")

    response = session.get(url, timeout=20)
    response.raise_for_status()

    data = response.json()
    print(f"✓ Status: SUCCESS")

    if "meta" in data:
        print(f"\nMetadata:")
        for key, value in data["meta"].items():
            print(f"  - {key}: {value}")

    if "data" in data:
        nav_data = data["data"]
        df_nav = pd.DataFrame(nav_data)
        hdfc_csv_path = RAW_DATA_PATH / "hdfc_top_100_direct.csv"
        df_nav.to_csv(hdfc_csv_path, index=False)
        print(f"\n✓ Saved: {hdfc_csv_path}")
        print(f"✓ Records: {len(df_nav)}")

except requests.exceptions.Timeout:
    print(f"⚠️  TIMEOUT: API took too long to respond")
except requests.exceptions.RequestException as e:
    print(f"✗ ERROR: {str(e)[:100]}")
except Exception as e:
    print(f"✗ ERROR: {str(e)[:100]}")

# ============================================================================
# TASK 5: Fetch NAV for 5 Key Schemes with Retry
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
schemes_fetched = 0

for scheme_name, scheme_code in key_schemes.items():
    try:
        url = f"https://api.mfapi.in/mf/{scheme_code}"
        print(
            f"\n[{key_schemes[scheme_name] - min(key_schemes.values()) + 1}/{len(key_schemes)}] {scheme_name}"
        )

        response = session.get(url, timeout=20)
        response.raise_for_status()

        data = response.json()
        scheme_nav_data[scheme_name] = data

        if "meta" in data:
            print(f"  ✓ Fund House: {data['meta'].get('fund_house', 'N/A')}")
            print(f"  ✓ Type: {data['meta'].get('scheme_type', 'N/A')}")

        if "data" in data:
            df_scheme = pd.DataFrame(data["data"])
            csv_filename = (
                RAW_DATA_PATH / f"{scheme_name.lower().replace(' ', '_')}_nav.csv"
            )
            df_scheme.to_csv(csv_filename, index=False)
            print(f"  ✓ Saved: {len(df_scheme)} records")
            schemes_fetched += 1

        sleep(0.5)  # Rate limiting

    except requests.exceptions.Timeout:
        print(f"  ⚠️  TIMEOUT after retry")
    except Exception as e:
        print(f"  ✗ ERROR: {str(e)[:60]}")

print(f"\nSchemes fetched successfully: {schemes_fetched}/{len(key_schemes)}")

# ============================================================================
# TASK 6: Explore Fund Master
# ============================================================================
print("\n" + "=" * 80)
print("TASK 6: EXPLORING FUND MASTER")
print("=" * 80)

if "fund_master" in data_frames:
    df_fm = data_frames["fund_master"]

    print(f"\nFund Master Analysis:")
    print(f"Shape: {df_fm.shape}")

    # Find relevant columns
    fund_house_col = next(
        (
            col
            for col in df_fm.columns
            if "fund" in col.lower() and "house" in col.lower()
        ),
        None,
    )
    category_col = next(
        (col for col in df_fm.columns if "category" in col.lower()), None
    )
    risk_col = next((col for col in df_fm.columns if "risk" in col.lower()), None)

    if fund_house_col:
        print(f"\nFund Houses ({df_fm[fund_house_col].nunique()}):")
        print(f"  {df_fm[fund_house_col].value_counts().head().to_dict()}")

    if category_col:
        print(f"\nCategories ({df_fm[category_col].nunique()}):")
        print(f"  {df_fm[category_col].unique()[:5]}")

    if risk_col:
        print(f"\nRisk Grades ({df_fm[risk_col].nunique()}):")
        print(f"  {df_fm[risk_col].value_counts().to_dict()}")

else:
    print("⚠️  fund_master.csv not loaded. Skipping analysis.")

# ============================================================================
# TASK 7 & 8: Data Quality Summary
# ============================================================================
print("\n" + "=" * 80)
print("TASK 7 & 8: DATA QUALITY SUMMARY")
print("=" * 80)

data_quality_summary = {
    "timestamp": datetime.now().isoformat(),
    "csv_files": {
        "loaded": len(available_csvs),
        "missing": len(missing_csvs),
        "total_expected": len(expected_csvs),
    },
    "api_data": {
        "hdfc_fetched": os.path.exists(RAW_DATA_PATH / "hdfc_top_100_direct.csv"),
        "schemes_fetched": schemes_fetched,
        "schemes_total": len(key_schemes),
    },
    "data_anomalies": anomalies,
}

summary_path = PROCESSED_DATA_PATH / "data_quality_summary.json"
with open(summary_path, "w") as f:
    json.dump(data_quality_summary, f, indent=2, default=str)

print(f"\n✓ Summary saved: {summary_path}")
print(json.dumps(data_quality_summary, indent=2, default=str))

print("\n" + "=" * 80)
print("✓ DATA INGESTION COMPLETE")
print("=" * 80)
print(f"Total CSV files loaded: {len(available_csvs)}")
print(f"Total API records: {schemes_fetched} schemes")
print(f"Output location: {PROCESSED_DATA_PATH}")
