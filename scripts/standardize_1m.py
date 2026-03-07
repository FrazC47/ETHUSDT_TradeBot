import pandas as pd

# Read 1w to get correct column order
df_w = pd.read_csv('/root/.openclaw/workspaces/currency_trading/data/ETHUSDT_1w_indicators.csv')
w_cols = list(df_w.columns)

# Read 1M
df_m = pd.read_csv('/root/.openclaw/workspaces/currency_trading/data/ETHUSDT_1M_indicators.csv')
m_cols = list(df_m.columns)

print(f"1w columns: {len(w_cols)}")
print(f"1M columns: {len(m_cols)}")
print()

# Find columns in 1M not in 1w
extra_in_m = [c for c in m_cols if c not in w_cols]
print(f"Extra in 1M: {extra_in_m}")
print()

# Find columns in 1w not in 1m  
missing_in_m = [c for c in w_cols if c not in m_cols]
print(f"Missing in 1M: {missing_in_m}")
print()

# For columns that exist in both, keep 1w order
common_cols = [c for c in w_cols if c in m_cols]
print(f"Common columns: {len(common_cols)}")

# Reorder 1M to match 1w column order (keeping only common columns)
df_m_standard = df_m[common_cols].copy()

print(f"After standardization: {len(df_m_standard.columns)} columns")
print(f"Rows: {len(df_m_standard)}")

# Save
df_m_standard.to_csv('/root/.openclaw/workspaces/currency_trading/data/ETHUSDT_1M_indicators.csv', index=False)
print()
print("Saved standardized 1M file (106 columns)")
