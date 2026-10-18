# Mamaearth Returns & Growth Intelligence Pipeline

## Project Overview

This capstone project builds a reproducible data analysis pipeline to investigate order revenue, product returns, customer segments, and monthly revenue trends.

The project uses SQL for structured reporting, Python for data cleaning and exploratory data analysis, visualizations for communicating results, and a narrative generator for business-facing findings.

## Repository Structure

```text
Capstone_Project_Vidhu_Bhatnagar/
├── README.md
├── data/
│   ├── customers.csv
│   ├── products.csv
│   └── orders.csv
├── sql/
│   ├── schema.sql
│   ├── seed_data.sql
│   └── reports.sql
├── analysis/
│   ├── clean_and_eda.py
│   └── visualize.py
├── visualizations/
│   ├── return_rate_by_payment.png
│   └── monthly_revenue_trend.png
└── narrator/
    ├── findings.json
    ├── generate_narrative.py
    └── sample_output.txt
```

## Requirements

- Python 3
- pandas
- matplotlib
- SQLite for the SQL layer
- Optional: `google-genai` and a Gemini API key for online narrative generation

In Google Colab, pandas and matplotlib are commonly available. If needed, install dependencies with:

```bash
pip install pandas matplotlib google-genai
```

## Execution Order

Run the layers in the following order so that each stage uses the outputs and assumptions of the preceding stage.

### Layer 1 — SQL reporting

1. Create or open a fresh SQLite database.
2. Execute `sql/schema.sql` to create the tables.
3. Execute `sql/seed_data.sql` to insert the supplied customers, products, and orders. This file contains the SQL `INSERT` statements and transaction commit; do not separately import the CSV files into this database.
4. Execute `sql/reports.sql` to produce the SQL reports.

The CSV files in `data/` are used separately by the Python analysis scripts in Layer 2.

**Important:** Run the schema and seed steps on a fresh database. The reporting script includes a table alteration, so rerunning it against the same database may require resetting the database first.

The SQL layer provides baseline reporting, including order totals, customer and product summaries, city-level return rates, and customer loyalty tiers.

### Layer 2 — Python cleaning, EDA, and visualizations

From the repository root, run:

```bash
python analysis/clean_and_eda.py
python analysis/visualize.py
```

`clean_and_eda.py` reads the CSV files from `data/`, standardizes payment methods, identifies and removes duplicate order records, handles missing values, calculates revenue, flags quantity outliers, analyzes return rates and customer segments, evaluates correlations, and analyzes monthly revenue.

The cleaning and analysis script writes `narrator/findings.json` dynamically. Do not manually type the analysis figures into this file.

`visualize.py` generates:

- `visualizations/return_rate_by_payment.png`
- `visualizations/monthly_revenue_trend.png`

The monthly revenue analysis distinguishes the apparent revenue trend from the trend after flagged bulk-order outliers are excluded.

### Layer 3 — Business narrative generation

Run:

```bash
python narrator/generate_narrative.py
```

The script reads `narrator/findings.json` and generates a business-facing narrative with three sections:

- **Situation** — the principal findings.
- **Complication** — the key risks and interpretation challenges.
- **Resolution** — suggested operational follow-up.

The script also checks required figures and saves its narrative and numeric accuracy result to `narrator/sample_output.txt`.

#### Online Gemini option

To use Gemini, configure `GEMINI_API_KEY` in the environment before running the script. Obtain a **free Gemini API key** through Google AI Studio and verify that your selected model is available under the free usage tier. Use the free tier only; do not use a paid-only API key or enable paid billing for this project. Free-tier availability and usage limits may vary.

The offline fallback remains available if you do not have a key or cannot access the free tier.

For example, in a shell where the key is already securely available:

```bash
export GEMINI_API_KEY="your-api-key"
python narrator/generate_narrative.py
```

Do not commit an API key to GitHub or place a real key directly in source code.

#### Offline fallback

If `GEMINI_API_KEY` is not configured, or if the Gemini request fails, the script uses its deterministic offline narrative. The offline path requires no API key and makes no network request. It is suitable for reproducing the narrative and running the numeric accuracy checks without depending on Gemini availability.

## Key Findings

The analysis of the supplied dataset found:

- Cleaned revenue: ₹97,358.30.
- Raw SQL revenue: ₹99,860.20.
- Revenue reconciliation difference: ₹2,501.90, matching the value of the five duplicate orders removed.
- Return rates: COD 44.4%, CARD 14.7%, and UPI 18.9%.
- Highest-risk observed segment: COD orders from Tier-2 cities, with a 54.5% return rate.
- After flagged quantity outliers are excluded, March 2026 is the peak month, with revenue of ₹20,318.90.

These are observed patterns in the supplied dataset. They should guide further investigation rather than be treated as proof of the causes of returns.

## Reproducibility Notes

- Run commands from the repository root.
- Keep the original CSV files in `data/`.
- Run the analysis script before the narrative generator so `findings.json` reflects the current data.
- The numeric accuracy check verifies required figures in the generated narrative.
- The offline fallback allows the final narrative step to run without an API key.
