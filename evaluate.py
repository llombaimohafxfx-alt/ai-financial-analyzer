import json
from pathlib import Path

TOLERANCE = 0.5  # allows tiny rounding differences (in AED thousand)


def get_value(raw: dict, field: str):
    """Return a field's value; for lists (e.g. several borrowing lines), return their sum."""
    item = raw.get(field)
    if item is None:
        return None
    if isinstance(item, list):
        return sum(i["value"] for i in item)
    return item["value"]


def main():
    truth = json.loads(Path("ground_truth.json").read_text())
    correct = 0
    total = 0

    for stem, expected_fields in truth.items():
        cache_file = Path("outputs") / f"{stem}.json"
        if not cache_file.exists():
            print(f"[SKIP] {stem}: no extraction yet (run analyze.py first)")
            continue

        raw = json.loads(cache_file.read_text())
        print(f"\n{stem} (model: {raw.get('model', 'unknown')})")

        for field, expected in expected_fields.items():
            got = get_value(raw, field)
            ok = got is not None and abs(got - expected) <= TOLERANCE
            total += 1
            correct += ok
            mark = "OK  " if ok else "FAIL"
            print(f"  [{mark}] {field}: expected {expected:,.0f}, got {got}")

    if total:
        print(f"\nAccuracy: {correct}/{total} = {correct / total:.1%}")


if __name__ == "__main__":
    main()