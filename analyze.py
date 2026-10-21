import json
from extract import extract_raw


def compute_metrics(raw: dict) -> dict:
    """All arithmetic happens here, in code, never in the AI."""
    revenue = raw["revenue_current"]["value"]
    revenue_prior = raw["revenue_prior"]["value"]
    da_total = sum(item["value"] for item in raw["depreciation_amortisation"])
    net_finance_cost = raw["finance_costs"]["value"] - raw["finance_income"]["value"]
    ebitda = raw["profit_before_tax"]["value"] + net_finance_cost + da_total

    return {
        "company": raw["company"],
        "fiscal_year": raw["fiscal_year"],
        "revenue_growth_pct": round((revenue / revenue_prior - 1) * 100, 2),
        "da_total": da_total,
        "ebitda": ebitda,
        "ebitda_margin_pct": round(ebitda / revenue * 100, 2),
        "net_margin_pct": round(raw["net_profit"]["value"] / revenue * 100, 2),
    }


if __name__ == "__main__":
    companies = [
        ("reports/aldar_2025.pdf", "Aldar Properties", 2025),
        ("reports/emaar_2025.pdf", "Emaar Properties", 2025),
    ]
    for pdf_path, name, year in companies:
        raw = extract_raw(pdf_path, name, year)
        print(json.dumps(compute_metrics(raw), indent=2))
        