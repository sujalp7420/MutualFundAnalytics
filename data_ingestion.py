"""
Data ingestion script: load CSVs, inspect, analyze fund_master, validate AMFI codes.
Uses `live_nav_fetch` for optional NAV fetching.
"""

import argparse
import json
from pathlib import Path
from datetime import datetime
import pandas as pd

from live_nav_fetch import fetch_all_navs


def load_and_inspect(raw_path: Path, expected_files: list):
    raw_path = Path(raw_path)
    available = []
    missing = []
    for f in expected_files:
        if (raw_path / f).exists():
            available.append(f)
        else:
            missing.append(f)

    print(f"Files expected: {len(expected_files)}")
    print(f"Available: {len(available)}")
    print(f"Missing: {len(missing)}")
    if missing:
        for m in missing:
            print("  -", m)

    loaded_frames = {}
    anomalies = {}
    for name in available:
        path = raw_path / name
        print("\n" + "=" * 80)
        print("Loading", name)
        try:
            df = pd.read_csv(path)
            loaded_frames[name.replace(".csv", "")] = df
            print("Shape:", df.shape)
            print("\nDtypes:")
            print(df.dtypes)
            print("\nHead:")
            print(df.head())
            nulls = int(df.isnull().sum().sum())
            dupes = int(df.duplicated().sum())
            mem_mb = float(df.memory_usage(deep=True).sum() / 1024**2)
            print("\nNulls:", nulls)
            print("Duplicates:", dupes)
            anomalies[name.replace(".csv", "")] = {
                "nulls": nulls,
                "duplicates": dupes,
                "memory_mb": mem_mb,
                "shape": df.shape,
            }
        except Exception as e:
            print("ERROR reading", name, e)
            anomalies[name.replace(".csv", "")] = {"error": str(e)}

    return loaded_frames, anomalies, available, missing


def analyze_fund_master(loaded_frames: dict):
    report = {}
    if "01_fund_master" in loaded_frames:
        df_fm = loaded_frames["01_fund_master"]
        fund_house_col = next(
            (c for c in df_fm.columns if "fund" in c.lower() and "house" in c.lower()),
            None,
        )
        category_col = next((c for c in df_fm.columns if "category" in c.lower()), None)
        subcat_col = next(
            (c for c in df_fm.columns if "sub" in c.lower() and "cat" in c.lower()),
            None,
        )
        risk_col = next((c for c in df_fm.columns if "risk" in c.lower()), None)
        code_col = next(
            (
                c
                for c in df_fm.columns
                if "amfi" in c.lower()
                or ("scheme" in c.lower() and "code" in c.lower())
            ),
            None,
        )
        report["rows"] = int(df_fm.shape[0])
        if fund_house_col:
            report["unique_fund_houses"] = int(df_fm[fund_house_col].nunique())
            report["fund_houses_sample"] = (
                df_fm[fund_house_col].dropna().unique()[:10].tolist()
            )
        if category_col:
            report["unique_categories"] = int(df_fm[category_col].nunique())
            report["categories_sample"] = (
                df_fm[category_col].dropna().unique()[:10].tolist()
            )
        if subcat_col:
            report["unique_subcategories"] = int(df_fm[subcat_col].nunique())
        if risk_col:
            report["risk_grades"] = df_fm[risk_col].dropna().unique().tolist()
        report["code_column"] = code_col
        if code_col:
            codes = df_fm[code_col].dropna().astype(str).unique().tolist()
            report["sample_codes"] = codes[:10]
            report["total_codes"] = len(codes)
    else:
        print("fund_master not loaded; skipping analysis")
    return report


def validate_amfi(loaded_frames: dict):
    summary = {"matched": None}
    if "01_fund_master" in loaded_frames and "02_nav_history" in loaded_frames:
        df_fm = loaded_frames["01_fund_master"]
        df_nav = loaded_frames["02_nav_history"]
        fm_code_col = next(
            (
                c
                for c in df_fm.columns
                if "amfi" in c.lower()
                or ("scheme" in c.lower() and "code" in c.lower())
            ),
            None,
        )
        nav_code_col = next(
            (
                c
                for c in df_nav.columns
                if "amfi" in c.lower()
                or ("scheme" in c.lower() and "code" in c.lower())
            ),
            None,
        )
        if fm_code_col and nav_code_col:
            fm_codes = set(df_fm[fm_code_col].dropna().astype(str).unique())
            nav_codes = set(df_nav[nav_code_col].dropna().astype(str).unique())
            missing_in_nav = sorted(list(fm_codes - nav_codes))
            extra_in_nav = sorted(list(nav_codes - fm_codes))
            summary["matched"] = len(fm_codes & nav_codes)
            summary["missing_in_nav_history_count"] = len(missing_in_nav)
            summary["extra_in_nav_history_count"] = len(extra_in_nav)
            summary["missing_sample"] = missing_in_nav[:10]
            summary["extra_sample"] = extra_in_nav[:10]
        else:
            summary["error"] = "Could not find AMFI code columns in one or both files"
    else:
        summary["error"] = "fund_master or nav_history not loaded"
    return summary


def main():
    parser = argparse.ArgumentParser(description="Data ingestion and validation")
    parser.add_argument("--raw", default="data/raw", help="Raw data folder")
    parser.add_argument(
        "--fetch-nav", action="store_true", help="Fetch live NAVs after loading"
    )
    args = parser.parse_args()

    expected_files = [
        "01_fund_master.csv",
        "02_nav_history.csv",
        "03_aum_by_fund_house.csv",
        "04_monthly_sip_inflows.csv",
        "05_category_inflows.csv",
        "06_industry_folio_count.csv",
        "07_scheme_performance.csv",
        "08_investor_transactions.csv",
        "09_portfolio_holdings.csv",
        "10_benchmark_indices.csv",
    ]

    raw = Path(args.raw)
    loaded_frames, anomalies, available, missing = load_and_inspect(raw, expected_files)

    nav_summary = None
    if args.fetch_nav:
        print("\nFetching live NAVs...")
        nav_summary = fetch_all_navs(raw)
        print("NAV fetch summary:", nav_summary)

    fm_report = analyze_fund_master(loaded_frames)
    amfi_summary = validate_amfi(loaded_frames)

    summary = {
        "timestamp": datetime.utcnow().isoformat(),
        "expected_files": expected_files,
        "available_files": available,
        "missing_files": missing,
        "anomalies": anomalies,
        "api_fetch": nav_summary,
        "fund_master_report": fm_report,
        "amfi_validation": amfi_summary,
    }

    outpath = Path("data/processed") / "data_quality_summary.json"
    outpath.parent.mkdir(parents=True, exist_ok=True)
    with open(outpath, "w") as f:
        json.dump(summary, f, indent=2, default=str)

    print("\nData quality summary saved to", outpath)


if __name__ == "__main__":
    main()
