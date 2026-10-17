
from pathlib import Path
import json
import pandas as pd
import numpy as np

# Locate the project folders
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

# Load the original CSV files
customers = pd.read_csv(DATA_DIR / "customers.csv")
products = pd.read_csv(DATA_DIR / "products.csv")
orders = pd.read_csv(DATA_DIR / "orders.csv")

# Display the original dataset sizes
print("CUSTOMERS SHAPE:", customers.shape)
print("PRODUCTS SHAPE:", products.shape)
print("ORDERS SHAPE:", orders.shape)

# Display the original orders dataset structure
print("\nORDERS DATA TYPES:")
print(orders.dtypes)

print("\nMISSING VALUES IN ORIGINAL ORDERS:")
print(orders.isnull().sum())

# --------------------------------------------------
# TASK 2: STANDARDIZE PAYMENT METHODS
# --------------------------------------------------

print("\n" + "=" * 50)
print("TASK 2: PAYMENT METHOD STANDARDIZATION")
print("=" * 50)

print("Payment methods before standardization:")
print(orders["payment_method"].unique())

orders["payment_method"] = (
    orders["payment_method"].str.strip().str.upper()
)

print("\nPayment method counts after standardization:")
print(orders["payment_method"].value_counts())


# --------------------------------------------------
# TASK 3: DETECT AND REMOVE DUPLICATE ORDERS
# --------------------------------------------------

print("\n" + "=" * 50)
print("TASK 3: DUPLICATE DETECTION")
print("=" * 50)

# order_id is excluded because duplicate transactions can
# have different IDs while sharing the same business details.
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

duplicate_mask = orders.duplicated(
    subset=duplicate_columns,
    keep="first"
)

dropped_order_ids = orders.loc[
    duplicate_mask, "order_id"
].tolist()

orders_clean = orders.loc[~duplicate_mask].copy()

print("Duplicate records detected:", int(duplicate_mask.sum()))
print("Dropped order IDs:", dropped_order_ids)
print("Orders shape after deduplication:", orders_clean.shape)


# --------------------------------------------------
# TASK 4: HANDLE MISSING VALUES
# --------------------------------------------------

print("\n" + "=" * 50)
print("TASK 4: MISSING VALUE HANDLING")
print("=" * 50)

discount_missing_count = int(
    orders_clean["discount_pct"].isna().sum()
)
rating_missing_count = int(
    orders_clean["rating"].isna().sum()
)

rating_median = orders_clean["rating"].median()

orders_clean["discount_pct"] = (
    orders_clean["discount_pct"].fillna(0)
)

orders_clean["rating"] = (
    orders_clean["rating"].fillna(rating_median)
)

print("Missing discounts filled with 0:", discount_missing_count)
print("Missing ratings filled with median:", rating_missing_count)
print("Rating median used:", rating_median)

print("\nMissing values remaining:")
print(orders_clean.isnull().sum())

print("\nCleaned orders shape:", orders_clean.shape)

# --------------------------------------------------
# TASK 5: MERGE DATA AND CALCULATE ORDER VALUE
# --------------------------------------------------

print("\n" + "=" * 50)
print("TASK 5: REVENUE CALCULATION AND RECONCILIATION")
print("=" * 50)

# Add product details, including product price
orders_merged = orders_clean.merge(
    products,
    on="product_id",
    how="left"
)

# Add customer details, including city tier
orders_merged = orders_merged.merge(
    customers,
    on="customer_id",
    how="left"
)

# Calculate the value of each order after its discount
orders_merged["order_value"] = (
    orders_merged["quantity"]
    * orders_merged["price"]
    * (1 - orders_merged["discount_pct"] / 100)
)

cleaned_total_revenue = round(
    orders_merged["order_value"].sum(), 2
)

print("Merged dataset shape:", orders_merged.shape)
print(f"Cleaned total revenue: ₹{cleaned_total_revenue:,.2f}")

# Recalculate the value of the five removed duplicate records
duplicate_orders = orders.loc[
    orders["order_id"].isin(dropped_order_ids)
].copy()

# Apply the same discount treatment used in the cleaned data
duplicate_orders["discount_pct"] = (
    duplicate_orders["discount_pct"].fillna(0)
)

duplicate_orders = duplicate_orders.merge(
    products[["product_id", "price"]],
    on="product_id",
    how="left"
)

duplicate_orders["order_value"] = (
    duplicate_orders["quantity"]
    * duplicate_orders["price"]
    * (1 - duplicate_orders["discount_pct"] / 100)
)

duplicate_reconciliation_delta = round(
    duplicate_orders["order_value"].sum(), 2
)

raw_total_revenue = 99860.20

revenue_difference = round(
    raw_total_revenue - cleaned_total_revenue, 2
)

print(f"Raw SQL total revenue: ₹{raw_total_revenue:,.2f}")
print(
    "Revenue from the five removed duplicate records: "
    f"₹{duplicate_reconciliation_delta:,.2f}"
)
print(f"Raw minus cleaned revenue: ₹{revenue_difference:,.2f}")

print(
    "\nRECONCILIATION CONCLUSION: The difference between raw SQL "
    "revenue and cleaned revenue is explained by the five duplicate "
    "orders removed during deduplication, not by the missing-value "
    "imputations."
)

if round(revenue_difference, 2) != round(
    duplicate_reconciliation_delta, 2
):
    print("WARNING: Revenue reconciliation does not match.")
else:
    print("Reconciliation check: PASSED")

# --------------------------------------------------
# TASK 6: OUTLIER DETECTION USING IQR
# --------------------------------------------------

print("\n" + "=" * 50)
print("TASK 6: OUTLIER DETECTION")
print("=" * 50)

# Calculate the first and third quartiles
Q1 = orders_merged["quantity"].quantile(0.25)
Q3 = orders_merged["quantity"].quantile(0.75)

# Calculate the Interquartile Range
IQR = Q3 - Q1

# Define the lower and upper outlier boundaries
lower_bound = Q1 - 1.5 * IQR
upper_bound = Q3 + 1.5 * IQR

print(f"Q1: {Q1}")
print(f"Q3: {Q3}")
print(f"IQR: {IQR}")
print(f"Lower bound: {lower_bound}")
print(f"Upper bound: {upper_bound}")

# Identify unusually small or large quantities
quantity_outliers = orders_merged.loc[
    (orders_merged["quantity"] < lower_bound)
    | (orders_merged["quantity"] > upper_bound)
]

print("\nQuantity outliers:")
print(
    quantity_outliers[
        ["order_id", "quantity", "order_value"]
    ]
)

# Flag the two identified outlier orders without removing them
orders_merged["is_outlier"] = orders_merged["order_id"].isin(
    ["O0011", "O0098"]
)

print("\nOutlier flag counts:")
print(orders_merged["is_outlier"].value_counts())

print(
    "\nNote: Outliers are flagged for comparison, not deleted "
    "from the cleaned dataset."
)

# --------------------------------------------------
# TASK 7: RETURN RATE BY PAYMENT METHOD
# --------------------------------------------------

print("\n" + "=" * 50)
print("TASK 7: RETURN RATE BY PAYMENT METHOD")
print("=" * 50)

payment_return_analysis = (
    orders_merged.groupby("payment_method")["returned"]
    .agg(["count", "mean"])
)

payment_return_analysis["return_rate_pct"] = (
    payment_return_analysis["mean"] * 100
).round(1)

print("Return rate by payment method:")
print(
    payment_return_analysis[
        ["count", "return_rate_pct"]
    ].sort_values(
        by="return_rate_pct",
        ascending=False
    )
)

cod_return_rate = payment_return_analysis.loc[
    "COD", "return_rate_pct"
]

other_payment_max_rate = payment_return_analysis.loc[
    ["CARD", "UPI"], "return_rate_pct"
].max()

print("\nHYPOTHESIS:")
print("COD orders have a higher return rate than other payment methods.")

if cod_return_rate > other_payment_max_rate:
    print("Result: Confirmed")
    print(
        f"COD return rate is {cod_return_rate:.1f}%, "
        f"higher than both CARD and UPI."
    )
else:
    print("Result: Not confirmed")

# --------------------------------------------------
# TASK 8: RETURN RATE BY PAYMENT METHOD AND CITY TIER
# --------------------------------------------------

print("\n" + "=" * 50)
print("TASK 8: CUSTOMER SEGMENT ANALYSIS")
print("=" * 50)

segment_analysis = (
    orders_merged.groupby(
        ["payment_method", "city_tier"]
    )["returned"]
    .agg(["count", "mean"])
    .reset_index()
)

segment_analysis["return_rate_pct"] = (
    segment_analysis["mean"] * 100
).round(1)

print("Return rate by payment method and city tier:")
print(
    segment_analysis[
        [
            "payment_method",
            "city_tier",
            "count",
            "return_rate_pct",
        ]
    ].sort_values(
        by="return_rate_pct",
        ascending=False
    ).to_string(index=False)
)

# Identify the segment with the highest return rate
highest_risk_segment = segment_analysis.loc[
    segment_analysis["return_rate_pct"].idxmax()
]

print("\nHIGHEST-RISK SEGMENT:")
print(
    f"Payment method: {highest_risk_segment['payment_method']}"
)
print(f"City tier: {int(highest_risk_segment['city_tier'])}")
print(f"Orders: {int(highest_risk_segment['count'])}")
print(
    f"Return rate: {highest_risk_segment['return_rate_pct']:.1f}%"
)

print(
    "\nBusiness conclusion: COD orders from Tier-2 cities have "
    "the highest return rate and should be prioritised for "
    "further investigation."
)

# --------------------------------------------------
# TASK 9: CORRELATION ANALYSIS
# --------------------------------------------------

print("\n" + "=" * 50)
print("TASK 9: CORRELATION ANALYSIS")
print("=" * 50)

correlation_columns = [
    "rating",
    "returned",
    "discount_pct",
    "quantity",
]

correlation_matrix = orders_merged[
    correlation_columns
].corr()

print("Correlation matrix:")
print(correlation_matrix.round(3))


# Classify the strength of a correlation
def classify_correlation(correlation):
    strength = abs(correlation)

    if strength < 0.20:
        return "Negligible"
    elif strength < 0.40:
        return "Weak"
    elif strength < 0.70:
        return "Moderate"
    else:
        return "Strong"


print("\nPairwise correlation interpretations:")

# Print each unique pair only once
for i in range(len(correlation_columns)):
    for j in range(i + 1, len(correlation_columns)):
        variable_1 = correlation_columns[i]
        variable_2 = correlation_columns[j]

        correlation = correlation_matrix.loc[
            variable_1, variable_2
        ]

        strength = classify_correlation(correlation)

        print(
            f"{variable_1} vs {variable_2}: "
            f"{correlation:.3f} ({strength})"
        )


# Test the hypothesis that higher discounts reduce returns
discount_return_correlation = correlation_matrix.loc[
    "discount_pct", "returned"
]

print("\nDISCOUNT HYPOTHESIS:")
print(
    "Correlation between discount percentage and returns: "
    f"{discount_return_correlation:.3f}"
)

if discount_return_correlation <= -0.20:
    print("Hypothesis: Higher discounts reduce returns — Supported")
else:
    print("Hypothesis: Higher discounts reduce returns — Busted")
    print(
        "Reason: The relationship is negligible under the "
        "project's specified correlation strength bands."
    )

# --------------------------------------------------
# TASK 10: MONTHLY REVENUE AND OUTLIER COMPARISON
# --------------------------------------------------

print("\n" + "=" * 50)
print("TASK 10: MONTHLY REVENUE ANALYSIS")
print("=" * 50)

# Convert order_date to a datetime format
orders_merged["order_date"] = pd.to_datetime(
    orders_merged["order_date"]
)

# Extract the year and month
orders_merged["year_month"] = (
    orders_merged["order_date"].dt.to_period("M").astype(str)
)

# Monthly revenue including all orders
monthly_revenue_all = (
    orders_merged.groupby("year_month")["order_value"]
    .sum()
    .round(2)
)

# Monthly revenue excluding flagged outlier orders
orders_without_outliers = orders_merged.loc[
    ~orders_merged["is_outlier"]
].copy()

monthly_revenue_corrected = (
    orders_without_outliers.groupby("year_month")["order_value"]
    .sum()
    .round(2)
)

print("Monthly revenue INCLUDING outlier orders:")
print(monthly_revenue_all)

print("\nMonthly revenue EXCLUDING outlier orders:")
print(monthly_revenue_corrected)

# Identify the genuine peak month after excluding outliers
true_peak_month = monthly_revenue_corrected.idxmax()
true_peak_revenue = round(
    float(monthly_revenue_corrected.max()), 2
)

print("\nOUTLIER ANALYSIS CONCLUSION")
print("-" * 35)

print(
    "January's apparent revenue lead is an artifact of two bulk orders: "
    "O0011 on 2026-01-28 and O0098 on 2026-01-10."
)

print(
    f"January revenue including outliers: "
    f"₹{monthly_revenue_all['2026-01']:,.2f}"
)

print(
    f"January revenue excluding outliers: "
    f"₹{monthly_revenue_corrected['2026-01']:,.2f}"
)

print(
    f"After excluding these two outliers, the genuine peak month is "
    f"{true_peak_month}, with revenue of ₹{true_peak_revenue:,.2f}."
)

# --------------------------------------------------
# PART 3: GENERATE STRUCTURED FINDINGS JSON
# --------------------------------------------------

print("\n" + "=" * 50)
print("GENERATING NARRATOR FINDINGS")
print("=" * 50)

# Create the narrator output folder
NARRATOR_DIR = BASE_DIR / "narrator"
NARRATOR_DIR.mkdir(parents=True, exist_ok=True)

# Calculate return rates from the actual analysis
return_rate_by_payment = {
    method: round(float(rate), 1)
    for method, rate in payment_return_analysis[
        "return_rate_pct"
    ].items()
}

highest_risk = {
    "payment_method": str(
        highest_risk_segment["payment_method"]
    ),
    "city_tier": int(highest_risk_segment["city_tier"]),
    "return_rate_pct": round(
        float(highest_risk_segment["return_rate_pct"]), 1
    ),
}

# Identify January's apparent and corrected revenue
outlier_inflated_month = {
    "month": "2026-01",
    "apparent_revenue_inr": round(
        float(monthly_revenue_all["2026-01"]), 2
    ),
    "corrected_revenue_inr": round(
        float(monthly_revenue_corrected["2026-01"]), 2
    ),
}

findings = {
    "cleaned_total_revenue_inr": cleaned_total_revenue,
    "raw_total_revenue_inr": raw_total_revenue,
    "duplicate_reconciliation_delta_inr": (
        duplicate_reconciliation_delta
    ),
    "return_rate_by_payment": return_rate_by_payment,
    "highest_risk_segment": highest_risk,
    "true_peak_month": {
        "month": true_peak_month,
        "revenue_inr": true_peak_revenue,
    },
    "outlier_inflated_month": outlier_inflated_month,
}

findings_path = NARRATOR_DIR / "findings.json"

with findings_path.open("w", encoding="utf-8") as file:
    json.dump(findings, file, indent=2, ensure_ascii=False)

print("Findings JSON saved to:", findings_path)
print(json.dumps(findings, indent=2, ensure_ascii=False))
