
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

# --------------------------------------------------
# SET UP PROJECT PATHS
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "visualizations"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------
# LOAD THE ORIGINAL CSV FILES
# --------------------------------------------------

customers = pd.read_csv(DATA_DIR / "customers.csv")
products = pd.read_csv(DATA_DIR / "products.csv")
orders = pd.read_csv(DATA_DIR / "orders.csv")

# --------------------------------------------------
# CLEAN THE ORDERS DATA
# --------------------------------------------------

# Standardize payment method names
orders["payment_method"] = (
    orders["payment_method"].str.strip().str.upper()
)

# Remove duplicate transactions using the natural key
duplicate_columns = [
    "customer_id",
    "product_id",
    "order_date",
    "quantity",
    "discount_pct",
    "payment_method",
    "rating",
    "returned",
]

orders_clean = orders.drop_duplicates(
    subset=duplicate_columns,
    keep="first"
).copy()

# Fill missing values using the project's cleaning rules
orders_clean["discount_pct"] = (
    orders_clean["discount_pct"].fillna(0)
)

rating_median = orders_clean["rating"].median()

orders_clean["rating"] = (
    orders_clean["rating"].fillna(rating_median)
)

# --------------------------------------------------
# MERGE DATA AND CALCULATE ORDER VALUE
# --------------------------------------------------

orders_merged = orders_clean.merge(
    products,
    on="product_id",
    how="left"
)

orders_merged = orders_merged.merge(
    customers,
    on="customer_id",
    how="left"
)

orders_merged["order_value"] = (
    orders_merged["quantity"]
    * orders_merged["price"]
    * (1 - orders_merged["discount_pct"] / 100)
)

# --------------------------------------------------
# CHART 1: RETURN RATE BY PAYMENT METHOD
# --------------------------------------------------

payment_return_analysis = (
    orders_merged.groupby("payment_method")["returned"]
    .agg(["count", "mean"])
)

payment_return_analysis["return_rate_pct"] = (
    payment_return_analysis["mean"] * 100
).round(1)

plot_data = payment_return_analysis.sort_values(
    by="return_rate_pct",
    ascending=False
)

plt.figure(figsize=(8, 5))

bars = plt.bar(
    plot_data.index,
    plot_data["return_rate_pct"]
)

plt.bar_label(bars, fmt="%.1f%%", padding=4)

plt.title("COD Returns at 44.4% — Nearly 3x the Card Return Rate")
plt.xlabel("Payment Method")
plt.ylabel("Return Rate (%)")

plt.tight_layout()

return_chart_path = OUTPUT_DIR / "return_rate_by_payment.png"

plt.savefig(
    return_chart_path,
    dpi=300,
    bbox_inches="tight"
)

plt.close()

print("Saved:", return_chart_path)

# --------------------------------------------------
# CHART 2: MONTHLY REVENUE, EXCLUDING OUTLIERS
# --------------------------------------------------

# Flag the two quantity outliers identified in the analysis
outlier_order_ids = ["O0011", "O0098"]

orders_merged["is_outlier"] = orders_merged["order_id"].isin(
    outlier_order_ids
)

orders_merged["order_date"] = pd.to_datetime(
    orders_merged["order_date"]
)

orders_merged["year_month"] = (
    orders_merged["order_date"].dt.to_period("M").astype(str)
)

orders_without_outliers = orders_merged.loc[
    ~orders_merged["is_outlier"]
].copy()

monthly_revenue_corrected = (
    orders_without_outliers.groupby("year_month")["order_value"]
    .sum()
    .round(2)
)

true_peak_month = monthly_revenue_corrected.idxmax()

plt.figure(figsize=(9, 5))

plt.plot(
    monthly_revenue_corrected.index,
    monthly_revenue_corrected.values,
    marker="o"
)

for month, revenue in monthly_revenue_corrected.items():
    plt.annotate(
        f"₹{revenue:,.0f}",
        (month, revenue),
        textcoords="offset points",
        xytext=(0, 8),
        ha="center"
    )

plt.title(
    f"Monthly Revenue Trend — {true_peak_month} Is the True Peak"
)
plt.xlabel("Month")
plt.ylabel("Revenue (₹)")
plt.xticks(rotation=45)

plt.tight_layout()

monthly_chart_path = OUTPUT_DIR / "monthly_revenue_trend.png"

plt.savefig(
    monthly_chart_path,
    dpi=300,
    bbox_inches="tight"
)

plt.close()

print("Saved:", monthly_chart_path)
print("True peak month:", true_peak_month)
print(
    f"True peak revenue: "
    f"₹{monthly_revenue_corrected.max():,.2f}"
)

print("\nAll visualizations generated successfully.")
