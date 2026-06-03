import pandas as pd

df_nav = pd.read_csv("data/raw/02_nav_history.csv")
df_nav["date"] = pd.to_datetime(df_nav["date"])

# Group by amfi_code and reindex to a complete daily date range
filled_dfs = []
for amfi, group in df_nav.groupby("amfi_code"):
    group = group.drop_duplicates(subset=["date"])
    min_date = group["date"].min()
    max_date = group["date"].max()
    full_dates = pd.date_range(start=min_date, end=max_date, freq="D")
    
    # Reindex
    group = group.set_index("date").reindex(full_dates)
    group.index.name = "date"
    group = group.reset_index()
    group["amfi_code"] = amfi
    # Forward-fill nav
    group["nav"] = group["nav"].ffill()
    
    filled_dfs.append(group)

df_nav_clean = pd.concat(filled_dfs, ignore_index=True)
print("Original row count:", len(df_nav))
print("Cleaned/Filled row count:", len(df_nav_clean))
print("Any missing/NaN navs after ffill?", df_nav_clean["nav"].isna().sum())
print("First 10 rows for amfi 119551 after filling:")
print(df_nav_clean[df_nav_clean["amfi_code"] == 119551].head(10))
