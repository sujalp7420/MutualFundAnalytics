# src/visualizations.py
"""Visualization helper functions for Mutual Fund EDA.
All functions return a Plotly Figure or a Matplotlib/Seaborn Axes object that can be displayed
in a Jupyter notebook and saved as PNG via the `export_png` helper.
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt
from pathlib import Path

# Global export directory (relative to project root)
EXPORT_DIR = Path(__file__).resolve().parents[2] / "reports" / "charts"
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

def export_png(fig, filename: str, width: int = 1200, height: int = 800, scale: int = 2):
    """Save a Plotly or Matplotlib figure as a high‑resolution PNG.
    Args:
        fig: Plotly Figure or Matplotlib Axes.
        filename: Base name without extension.
        width, height: pixel dimensions for Plotly figures.
        scale: multiplier for DPI (Matplotlib uses DPI=scale*100).
    """
    path = EXPORT_DIR / f"{filename}.png"
    if isinstance(fig, go.Figure):
        fig.write_image(str(path), width=width, height=height, scale=scale)
    else:
        # Assume Matplotlib Axes
        fig.figure.savefig(path, dpi=scale * 100, bbox_inches="tight")
    return path

# 1. NAV trend analysis
def plot_nav_trend(nav_df: pd.DataFrame, bull_start: str, bull_end: str, corr_start: str, corr_end: str):
    """Plot daily NAV for all schemes with shaded regions for bull run and correction.
    nav_df: wide DataFrame with Date index and scheme columns.
    bull_start/end, corr_start/end: date strings (YYYY‑MM‑DD).
    """
    fig = go.Figure()
    for col in nav_df.columns:
        fig.add_trace(go.Scatter(x=nav_df.index, y=nav_df[col], mode='lines', name=str(col), line=dict(width=1)))
    # Highlight bull run
    fig.add_vrect(x0=bull_start, x1=bull_end, fillcolor="#00bfa6", opacity=0.2, line_width=0, annotation_text="2023 Bull Run", annotation_position="top left")
    # Highlight correction
    fig.add_vrect(x0=corr_start, x1=corr_end, fillcolor="#ff7f0e", opacity=0.2, line_width=0, annotation_text="2024 Correction", annotation_position="top left")
    fig.update_layout(title="Daily NAV Trend (All Schemes)", xaxis_title="Date", yaxis_title="NAV", hovermode="x unified")
    return fig

# 2. AUM growth bar chart (Seaborn)
def plot_aum_growth(aum_df: pd.DataFrame, highlight_fund_house: str = "SBI"):
    """Grouped bar chart of AUM by fund house per year.
    aum_df must contain columns ['FundHouse', 'Year', 'AUM'].
    """
    plt.figure(figsize=(10, 6))
    palette = sns.color_palette("deep")
    ax = sns.barplot(data=aum_df, x="Year", y="AUM", hue="FundHouse", palette=palette)
    # Highlight SBI
    for patch, label in zip(ax.patches, ax.get_xticklabels()):
        if label.get_text() == highlight_fund_house:
            patch.set_edgecolor('gold')
            patch.set_linewidth(2)
    plt.title("AUM Growth by Fund House (2022‑2025)")
    plt.ylabel("AUM (₹ L Cr)")
    plt.legend(title="Fund House", bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    return ax

# 3. SIP inflow time‑series (Plotly)
def plot_sip_inflow(sip_df: pd.DataFrame, high_month: str, high_value: float):
    """Monthly SIP inflow line chart with annotation for all‑time high.
    sip_df must have columns ['Month', 'SIP_Inflow'] with Month as datetime.
    """
    fig = px.line(sip_df, x='Month', y='SIP_Inflow', title='Monthly SIP Inflow (Jan 2022 – Dec 2025)')
    fig.add_annotation(x=high_month, y=high_value,
                       text=f"All‑time high: ₹{high_value:,.0f} Cr",
                       showarrow=True, arrowhead=2, arrowsize=1,
                       bgcolor='white')
    fig.update_layout(xaxis_title='Month', yaxis_title='SIP Inflow (₹ Cr)')
    return fig

# 4. Category inflow heatmap (Seaborn)
def plot_category_heatmap(cat_df: pd.DataFrame):
    """Heatmap of net inflows by month (rows) and category (columns).
    cat_df must have columns ['Month', 'Category', 'NetInflows'].
    """
    pivot = cat_df.pivot(index='Month', columns='Category', values='NetInflows')
    plt.figure(figsize=(12, 8))
    sns.heatmap(pivot, cmap='viridis', linewidths=.5, linecolor='gray')
    plt.title('Category Inflow Heatmap')
    plt.xlabel('Category')
    plt.ylabel('Month')
    plt.tight_layout()
    ax = plt.gca()
    return ax

# 5. Investor demographics (pie + box)
def plot_age_distribution(demo_df: pd.DataFrame):
    """Pie chart of investor age‑group distribution.
    demo_df must contain column 'AgeGroup' with categorical values.
    """
    counts = demo_df['AgeGroup'].value_counts()
    fig = go.Figure(data=[go.Pie(labels=counts.index, values=counts.values, hole=0.4)])
    fig.update_layout(title='Investor Age‑Group Distribution')
    return fig

def plot_sip_by_agebox(demo_df: pd.DataFrame):
    """Box plot of SIP amount by age group.
    Expect columns 'AgeGroup' and 'SIP_Amount'.
    """
    plt.figure(figsize=(8,6))
    ax = sns.boxplot(data=demo_df, x='AgeGroup', y='SIP_Amount')
    plt.title('SIP Amount by Age Group')
    plt.ylabel('SIP Amount (₹ Cr)')
    plt.tight_layout()
    return ax

def plot_gender_pie(demo_df: pd.DataFrame):
    """Gender split pie chart.
    Column 'Gender' expected.
    """
    counts = demo_df['Gender'].value_counts()
    fig = go.Figure(data=[go.Pie(labels=counts.index, values=counts.values, hole=0.3)])
    fig.update_layout(title='Gender Split of Investors')
    return fig

# 6. Geographic distribution
def plot_sip_by_state(demo_df: pd.DataFrame):
    """Horizontal bar chart of SIP amount by state.
    Columns: 'State' and 'SIP_Amount'.
    """
    agg = demo_df.groupby('State')['SIP_Amount'].sum().sort_values()
    plt.figure(figsize=(10,8))
    ax = sns.barplot(x=agg.values, y=agg.index, palette='mako')
    plt.title('SIP Amount by State')
    plt.xlabel('SIP Amount (₹ Cr)')
    plt.tight_layout()
    return ax

def plot_city_tier_pie(tier_df: pd.DataFrame):
    """Pie chart comparing T30 vs B30 city tiers.
    Expect columns 'Tier' with values 'T30' or 'B30' and 'City'.
    """
    counts = tier_df['Tier'].value_counts()
    fig = go.Figure(data=[go.Pie(labels=counts.index, values=counts.values)])
    fig.update_layout(title='City Tier Distribution (T30 vs B30)')
    return fig

# 7. Folio count growth
def plot_folio_growth(folio_df: pd.DataFrame, milestones: dict):
    """Line chart of folio count over time with milestone markers.
    folio_df columns: ['Date', 'FolioCount'].
    milestones: dict of {"label": "YYYY‑MM"}.
    """
    fig = px.line(folio_df, x='Date', y='FolioCount', title='Folio Count Growth (2022‑2025)')
    for label, month in milestones.items():
        fig.add_vline(x=month, line_dash='dash', annotation_text=label, annotation_position='top left')
    fig.update_layout(xaxis_title='Date', yaxis_title='Folio Count (Cr)')
    return fig

# 8. NAV return correlation matrix (Plotly heatmap)
def plot_nav_correlation(corr_matrix: pd.DataFrame):
    """Heatmap of pairwise Pearson correlation of daily returns for selected funds.
    corr_matrix must be a symmetric DataFrame with fund codes as index/columns.
    """
    fig = go.Figure(data=go.Heatmap(z=corr_matrix.values,
                                    x=corr_matrix.columns,
                                    y=corr_matrix.index,
                                    colorscale='RdBu',
                                    zmid=0))
    fig.update_layout(title='NAV Return Correlation Matrix')
    return fig

# 9. Sector allocation donut (Plotly)
def plot_sector_allocation(sector_df: pd.DataFrame):
    """Donut chart of aggregate sector weights across all equity funds.
    sector_df columns: ['Sector', 'Weight'] where weight is percentage.
    """
    agg = sector_df.groupby('Sector')['Weight'].sum().reset_index()
    fig = go.Figure(data=[go.Pie(labels=agg['Sector'], values=agg['Weight'], hole=0.4)])
    fig.update_layout(title='Sector Allocation Across Equity Funds')
    return fig
