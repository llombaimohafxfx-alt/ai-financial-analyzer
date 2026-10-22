import json
from extract import extract_raw

# Ratios do not depend on currency or scale; absolute amounts do.
SCALE_TO_MILLIONS = {"units": 1e-6, "thousands": 1e-3, "millions": 1.0}
TO_AED = {"AED": 1.0, "SAR": 3.6725 / 3.75}  # both currencies are pegged to the US dollar

COMPANIES = [
    ("reports/aldar_2025.pdf", "Aldar Properties", 2025),
    ("reports/emaar_2025.pdf", "Emaar Properties", 2025),
    ("reports/deyaar_2025.pdf", "Deyaar Development", 2025),
    ("reports/union_2025.pdf", "Union Properties", 2025),
    ("reports/rak_2025.pdf", "RAK Properties", 2025),
    ("reports/daralarkan_2025.pdf", "Dar Al Arkan", 2025),
]


def total(items: list) -> float:
    return sum(item["value"] for item in items)


def compute_metrics(raw: dict) -> dict:
    """All arithmetic happens here, in code, never in the AI."""
    revenue = raw["revenue_current"]["value"]
    revenue_prior = raw["revenue_prior"]["value"]
    net_profit = raw["net_profit"]["value"]

    da_total = total(raw["depreciation_amortisation"])
    finance_income = raw["finance_income"]["value"] if raw.get("finance_income") else 0
    net_finance_cost = raw["finance_costs"]["value"] - finance_income
    ebitda = raw["profit_before_tax"]["value"] + net_finance_cost + da_total

    borrowings = total(raw["borrowings"])
    cash = raw["cash_and_cash_equivalents"]["value"]
    net_debt = borrowings - cash

    metrics = {
        "company": raw["company"],
        "fiscal_year": raw["fiscal_year"],
        "source_currency": raw["currency"],
        "source_scale": raw["scale"],
        "revenue_growth_pct": round((revenue / revenue_prior - 1) * 100, 2),
        "ebitda": ebitda,
        "ebitda_margin_pct": round(ebitda / revenue * 100, 2),
        "net_margin_pct": round(net_profit / revenue * 100, 2),
        "total_borrowings": borrowings,
        "cash": cash,
        "net_debt": net_debt,
        "net_debt_to_ebitda": round(net_debt / ebitda, 2),
        "debt_to_equity": round(borrowings / raw["total_equity"]["value"], 2),
        "roe_pct": round(
            raw["net_profit_attributable_to_owners"]["value"]
            / raw["equity_attributable_to_owners"]["value"] * 100, 2
        ),
        "cash_conversion": round(raw["operating_cash_flow"]["value"] / net_profit, 2),
    }

    escrow_item = raw.get("escrow_in_cash_equivalents")
    if escrow_item:
        net_debt_excl_escrow = borrowings - (cash - escrow_item["value"])
        metrics["escrow_cash"] = escrow_item["value"]
        metrics["net_debt_excl_escrow"] = net_debt_excl_escrow
        metrics["net_debt_to_ebitda_excl_escrow"] = round(net_debt_excl_escrow / ebitda, 2)
    else:
        metrics["net_debt_excl_escrow"] = "no escrow in cash equivalents"

    if raw.get("current_assets") and raw.get("current_liabilities"):
        metrics["current_ratio"] = round(
            raw["current_assets"]["value"] / raw["current_liabilities"]["value"], 2
        )
    else:
        metrics["current_ratio"] = "not presented in report"

    if raw.get("total_liabilities"):
        metrics["balance_check_gap"] = (
            raw["total_assets"]["value"]
            - raw["total_liabilities"]["value"]
            - raw["total_equity"]["value"]
        )
    else:
        metrics["balance_check_gap"] = "total liabilities not printed"

    # Convert absolute amounts to AED millions so companies can be compared.
    factor = SCALE_TO_MILLIONS[raw["scale"]] * TO_AED[raw["currency"]]
    for key in ["ebitda", "total_borrowings", "cash", "net_debt",
                "escrow_cash", "net_debt_excl_escrow"]:
        if isinstance(metrics.get(key), (int, float)):
            metrics[key] = round(metrics[key] * factor, 1)
    metrics["amounts_in"] = "AED millions"

    return metrics


if __name__ == "__main__":
    for pdf_path, name, year in COMPANIES:
        raw = extract_raw(pdf_path, name, year)
        print(json.dumps(compute_metrics(raw), indent=2))