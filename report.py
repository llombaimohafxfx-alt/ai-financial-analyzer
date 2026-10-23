import json
from pathlib import Path
from analyze import compute_metrics, COMPANIES

ROWS = [
    ("Revenue growth", "revenue_growth_pct", "%"),
    ("EBITDA margin (reported)", "ebitda_margin_pct", "%"),
    ("EBITDA margin (adjusted)", "adjusted_ebitda_margin_pct", "%"),
    ("Non-recurring share of EBITDA", "non_recurring_share_of_ebitda_pct", "%"),
    ("Net margin", "net_margin_pct", "%"),
    ("Net debt / EBITDA (reported)", "net_debt_to_ebitda", "x"),
    ("Net debt / EBITDA (excl. escrow)", "net_debt_to_ebitda_excl_escrow", "x"),
    ("Debt / equity", "debt_to_equity", "x"),
    ("ROE", "roe_pct", "%"),
    ("Cash conversion (OCF / net profit)", "cash_conversion", "x"),
]


def escrow_status(m: dict) -> str:
    v = m["net_debt_excl_escrow"]
    if isinstance(v, (int, float)):
        return "In cash (adjusted)"
    if v.startswith("escrow disclosed"):
        return "Excluded by company"
    return "Not found - verify"


def fmt(value, unit: str) -> str:
    if isinstance(value, (int, float)):
        return f"{value:.1f}{unit}" if unit == "%" else f"{value:.2f}{unit}"
    return "-"


def main():
    names, metrics, models = [], [], []
    for pdf_path, name, year in COMPANIES:
        cache = Path("outputs") / f"{Path(pdf_path).stem}.json"
        if not cache.exists():
            print(f"[SKIP] {name}: not extracted yet")
            continue
        raw = json.loads(cache.read_text())
        names.append(name)
        metrics.append(compute_metrics(raw))
        models.append(f"{name}: {raw.get('model', 'unknown')}")

    lines = [
        "| Metric | " + " | ".join(names) + " |",
        "|---|" + "---|" * len(names),
    ]
    for label, key, unit in ROWS:
        cells = [fmt(m.get(key), unit) for m in metrics]
        lines.append(f"| {label} | " + " | ".join(cells) + " |")
    lines.append("| Escrow treatment | " + " | ".join(escrow_status(m) for m in metrics) + " |")

    table = "\n".join(lines)
    footer = "\n\nFY2025. Ratios computed in Python from AI-extracted line items.\nModel per company: " + "; ".join(models)
    Path("results.md").write_text("# Comparison of Gulf developers\n\n" + table + footer + "\n")
    print(table)
    print("\nSaved to results.md")


if __name__ == "__main__":
    main()