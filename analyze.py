import json
from extract import extract_raw


def total(items: list) -> float:
    return sum(item["value"] for item in items)


def compute_metrics(raw: dict) -> dict:
    """All arithmetic happens here, in code, never in the AI."""
    revenue = raw["revenue_current"]["value"]
    revenue_prior = raw["revenue_prior"]["value"]
    net_profit = raw["net_profit"]["value"]

    da_total = total(raw["depreciation_amortisation"])
    net_finance_cost = raw["finance_costs"]["value"] - raw["finance_income"]["value"]
    ebitda = raw["profit_before_tax"]["value"] + net_finance_cost + da_total

    borrowings = total(raw["borrowings"])
    cash = raw["cash_and_cash_equivalents"]["value"]
    net_debt = borrowings - cash

    metrics = {
        "company": raw["company"],
        "fiscal_year": raw["fiscal_year"],
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
        free_cash = cash - escrow_item["value"]
        net_debt_excl_escrow = borrowings - free_cash
        metrics["escrow_cash"] = escrow_item["value"]
        metrics["net_debt_excl_escrow"] = net_debt_excl_escrow
        metrics["net_debt_to_ebitda_excl_escrow"] = round(net_debt_excl_escrow / ebitda, 2)
    else:
        metrics["net_debt_excl_escrow"] = "escrow not disclosed"

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

    return metrics


if __name__ == "__main__":
    companies = [
        ("reports/aldar_2025.pdf", "Aldar Properties", 2025),
        ("reports/emaar_2025.pdf", "Emaar Properties", 2025),
    ]
    for pdf_path, name, year in companies:
        raw = extract_raw(pdf_path, name, year)
        print(json.dumps(compute_metrics(raw), indent=2))
