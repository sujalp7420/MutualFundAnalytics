"""
Utilities to fetch live NAV data from mfapi.in and save to data/raw
"""

import requests
from pathlib import Path
import pandas as pd
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def create_session_with_retries(total=3, backoff_factor=0.5):
    session = requests.Session()
    retry = Retry(
        total=total,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        backoff_factor=backoff_factor,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def fetch_scheme_nav(
    code: int, out_path: Path, session: requests.Session = None, timeout: int = 20
):
    """Fetch NAV history for a single scheme code and save as CSV."""
    if session is None:
        session = create_session_with_retries()
    url = f"https://api.mfapi.in/mf/{code}"
    r = session.get(url, timeout=timeout)
    r.raise_for_status()
    data = r.json()
    if "data" in data:
        df = pd.DataFrame(data["data"])
        df.to_csv(out_path, index=False)
        return {"status": "saved", "rows": len(df)}
    else:
        return {"status": "no_data"}


def fetch_all_navs(raw_path: Path, hdfc_code: int = 125497, key_schemes: dict = None):
    """Fetch HDFC and key schemes NAVs and save to raw_path.

    Returns a dict summarizing results.
    """
    raw_path = Path(raw_path)
    raw_path.mkdir(parents=True, exist_ok=True)
    session = create_session_with_retries()
    summary = {}

    # HDFC
    try:
        out = raw_path / "hdfc_top_100_direct.csv"
        res = fetch_scheme_nav(hdfc_code, out, session=session)
        summary["hdfc"] = res
    except Exception as e:
        summary["hdfc"] = {"status": "error", "error": str(e)}

    # Key schemes
    if key_schemes is None:
        key_schemes = {
            "SBI_Bluechip": 119551,
            "ICICI_Bluechip": 120503,
            "Nippon_Large_Cap": 118632,
            "Axis_Bluechip": 119092,
            "Kotak_Bluechip": 120841,
        }
    summary["key_schemes"] = {}
    for name, code in key_schemes.items():
        out = raw_path / f"{name.lower()}_nav.csv"
        try:
            if out.exists():
                summary["key_schemes"][name] = {"status": "exists", "rows": None}
                continue
            res = fetch_scheme_nav(code, out, session=session)
            summary["key_schemes"][name] = res
        except Exception as e:
            summary["key_schemes"][name] = {"status": "error", "error": str(e)}

    return summary


if __name__ == "__main__":
    # simple CLI behaviour
    import argparse

    parser = argparse.ArgumentParser(description="Fetch live NAVs and save to data/raw")
    parser.add_argument("--raw", default="data/raw", help="Raw data folder")
    args = parser.parse_args()
    print(fetch_all_navs(args.raw))
