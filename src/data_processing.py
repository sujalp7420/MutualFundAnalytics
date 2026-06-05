# src/data_processing.py
"""Utility functions for loading and preprocessing Mutual Fund datasets.
All CSV files are located in the `data/` directory relative to the project root.
"""
import pandas as pd
import numpy as np
from pathlib import Path

def load_csv(filename: str) -> pd.DataFrame:
    """Load a CSV file from the data folder.
    Args:
        filename: Name of the CSV file (e.g., '02_nav_history.csv').
    Returns:
        DataFrame with parsed dates.
    """
    data_path = Path(__file__).resolve().parents[1] / "data" / filename
    df = pd.read_csv(data_path)
    # Attempt to parse date columns automatically
    for col in df.columns:
        if "date" in col.lower() or "dt" in col.lower():
            try:
                df[col] = pd.to_datetime(df[col])
            except Exception:
                pass
    return df

def preprocess_nav(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare NAV history data.
    Expected columns: ['scheme_id', 'date', 'nav']
    """
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values(['scheme_id', 'date'])
    return df

def compute_daily_returns(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate daily percentage returns per scheme.
    Returns a DataFrame with columns ['scheme_id', 'date', 'daily_return'].
    """
    df = df.copy()
    df['daily_return'] = df.groupby('scheme_id')['nav'].pct_change()
    return df[['scheme_id', 'date', 'daily_return']]

def load_monthly_sip() -> pd.DataFrame:
    """Load monthly SIP inflow data and ensure a proper datetime index."""
    df = load_csv('04_monthly_sip_inflows.csv')
    if 'month' in df.columns:
        df['month'] = pd.to_datetime(df['month'], format='%Y-%m')
    return df

def compute_category_heatmap(df: pd.DataFrame) -> pd.DataFrame:
    """Pivot category inflow data into a matrix suitable for heatmap.
    Expected columns: ['category', 'month', 'net_inflow']
    """
    df = df.copy()
    df['month'] = pd.to_datetime(df['month'])
    pivot = df.pivot_table(index='category', columns='month', values='net_inflow', aggfunc='sum').fillna(0)
    return pivot

def compute_correlation_matrix(nav_df: pd.DataFrame, scheme_ids: list) -> pd.DataFrame:
    """Compute pair‑wise correlation of daily returns for selected schemes.
    Args:
        nav_df: NAV history DataFrame (output of preprocess_nav).
        scheme_ids: List of scheme identifiers to include.
    Returns:
        Correlation matrix DataFrame indexed by scheme_id.
    """
    returns = compute_daily_returns(nav_df)
    selected = returns[returns['scheme_id'].isin(scheme_ids)]
    # Pivot to wide format: rows=dates, cols=schemes
    wide = selected.pivot(index='date', columns='scheme_id', values='daily_return')
    corr = wide.corr()
    return corr

def load_portfolio_holdings() -> pd.DataFrame:
    """Load sector allocation holdings data.
    Expected columns: ['fund_id', 'sector', 'weight']
    """
    return load_csv('09_portfolio_holdings.csv')
