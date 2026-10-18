
import json
import os
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
NARRATOR_DIR = BASE_DIR / "narrator"
FINDINGS_PATH = NARRATOR_DIR / "findings.json"
SAMPLE_PATH = NARRATOR_DIR / "sample_output.txt"

SYSTEM_INSTRUCTION = """
You are a senior data analyst writing for Mamaearth's regional ops and finance heads.

Write a concise, business-focused report with exactly three labeled sections:
Situation, Complication, and Resolution.

Use only facts and figures supplied in the user's findings JSON.
Do not invent statistics, causes, targets, or unsupported explanations.
Preserve the supplied numbers exactly in meaning.
Explain the business implications and practical next steps.
Clearly distinguish observed patterns from proven causes.
"""

def generate_scr_narrative(findings: dict) -> dict:
    """Generate a narrative with Gemini. Return a structured result."""
    try:
        from google import genai
        from google.genai import types

        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            return {
                "status": "error",
                "narrative": None,
                "message": "GEMINI_API_KEY is not set."
            }

        client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=20000)
        )

        # The prompt is built dynamically from the supplied findings.
        user_prompt = (
            "Write the requested Situation, Complication, and Resolution "
            "report using only this findings JSON:\n\n"
            + json.dumps(findings, indent=2, ensure_ascii=False)
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.0,
                max_output_tokens=500
            )
        )

        narrative = response.text
        if not narrative or not narrative.strip():
            return {
                "status": "error",
                "narrative": None,
                "message": "Gemini returned an empty narrative."
            }

        usage = getattr(response, "usage_metadata", None)
        tokens = getattr(usage, "total_token_count", None) if usage else None

        return {
            "status": "success",
            "narrative": narrative.strip(),
            "tokens": tokens
        }

    except Exception as err:
        # Do not expose a raw exception object to the caller.
        return {
            "status": "error",
            "narrative": None,
            "message": str(err)
        }


def generate_scr_narrative_offline(findings: dict) -> dict:
    """Create a deterministic narrative without a key or network request."""
    try:
        revenue = findings["cleaned_total_revenue_inr"]
        raw_revenue = findings["raw_total_revenue_inr"]
        duplicate_delta = findings["duplicate_reconciliation_delta_inr"]
        payment_rates = findings["return_rate_by_payment"]
        risk = findings["highest_risk_segment"]
        peak = findings["true_peak_month"]
        inflated = findings["outlier_inflated_month"]

        month_name = {
            "2026-01": "January 2026",
            "2026-02": "February 2026",
            "2026-03": "March 2026",
            "2026-04": "April 2026",
            "2026-05": "May 2026",
            "2026-06": "June 2026",
        }.get(peak["month"], peak["month"])

        narrative = f"""Situation
The cleaned dataset records total revenue of ₹{revenue:,.2f}, compared with raw SQL revenue of ₹{raw_revenue:,.2f}. The observed return rates are COD {payment_rates["COD"]:.1f}%, CARD {payment_rates["CARD"]:.1f}%, and UPI {payment_rates["UPI"]:.1f}%. After outlier review, {month_name} is the peak month with revenue of ₹{peak["revenue_inr"]:,.2f}.

Complication
The raw-to-cleaned revenue difference is ₹{duplicate_delta:,.2f}, reconciled to the five duplicate orders removed during cleaning. The highest-risk observed segment is {risk["payment_method"]} in Tier-{risk["city_tier"]} cities, with a return rate of {risk["return_rate_pct"]:.1f}%. January's apparent revenue of ₹{inflated["apparent_revenue_inr"]:,.2f} falls to ₹{inflated["corrected_revenue_inr"]:,.2f} after excluding the flagged bulk-order outliers. These patterns identify areas for investigation; they do not by themselves prove the causes of returns.

Resolution
Prioritise investigation of COD orders from Tier-2 cities, review the customer and operational journey for returned COD orders, and monitor payment-method return rates over time. Report monthly revenue both with and without flagged outliers so bulk orders do not obscure the underlying trend. Preserve the duplicate-removal reconciliation when reporting cleaned revenue."""
        return {
            "status": "success",
            "narrative": narrative,
            "tokens": 0
        }
    except Exception as err:
        return {
            "status": "error",
            "narrative": None,
            "message": str(err)
        }


def check_numeric_accuracy(narrative: str) -> bool:
    """Check all required figures, allowing comma/no-comma number formats."""
    normalised = narrative.replace(",", "")
    checks = [
        ("Cleaned revenue 97,358.30", ["97358.30", "97358.3"]),
        ("COD return rate 44.4%", ["44.4"]),
        ("Highest-risk return rate 54.5%", ["54.5"]),
        ("Duplicate reconciliation 2,501.90", ["2501.90", "2501.9"]),
        ("March peak revenue 20,318.90",
         ["March", "20318.90"]),
    ]

    all_passed = True
    for label, required in checks:
        passed = all(term.lower() in normalised.lower() for term in required)
        print(f"{'PASS' if passed else 'FAIL'}: {label}")
        all_passed = all_passed and passed

    return all_passed


def main():
    if not FINDINGS_PATH.exists():
        raise FileNotFoundError(
            f"Missing {FINDINGS_PATH}. Run analysis/clean_and_eda.py first."
        )

    with FINDINGS_PATH.open("r", encoding="utf-8") as file:
        findings = json.load(file)

    # Try Gemini only when a key is configured; otherwise use offline mode.
    if os.environ.get("GEMINI_API_KEY"):
        result = generate_scr_narrative(findings)
        if result["status"] != "success":
            print("Online generation failed; using offline fallback.")
            print("Reason:", result.get("message", "Unknown error"))
            result = generate_scr_narrative_offline(findings)
    else:
        print("GEMINI_API_KEY not set; using offline narrative.")
        result = generate_scr_narrative_offline(findings)

    if result["status"] != "success":
        raise RuntimeError(
            "Narrative generation failed: " + result.get("message", "Unknown error")
        )

    narrative = result["narrative"]
    print("\n" + narrative + "\n")

    accuracy_passed = check_numeric_accuracy(narrative)
    print("Numeric accuracy:", "PASSED" if accuracy_passed else "FAILED")

    SAMPLE_PATH.write_text(
        narrative
        + "\n\nNumeric accuracy check: "
        + ("PASSED" if accuracy_passed else "FAILED")
        + "\n",
        encoding="utf-8"
    )
    print(f"Sample output saved to: {SAMPLE_PATH}")

    if not accuracy_passed:
        raise AssertionError("Required numeric accuracy checks failed.")


if __name__ == "__main__":
    main()
