import os
import json
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel

load_dotenv()
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
OUTPUT_DIR = Path("outputs")


class LineItem(BaseModel):
    label_in_document: str   # the line's name exactly as printed
    value: float
    pdf_page: int
    printed_page: str


class RawFinancials(BaseModel):
    company: str
    fiscal_year: int
    unit: str
    revenue_current: LineItem
    revenue_prior: LineItem
    profit_before_tax: LineItem
    finance_costs: LineItem
    finance_income: LineItem
    net_profit: LineItem
    depreciation_amortisation: list[LineItem]   # can be several lines; Python sums them


PROMPT = (
    "From the consolidated financial statements of {company} for fiscal year "
    "{year}, extract the requested line items. Do NOT calculate, combine or "
    "estimate anything: only copy values exactly as printed. Report every value "
    "as a positive number (ignore parentheses). Write the unit exactly as "
    "'AED thousand'. For depreciation_amortisation, list every depreciation and "
    "amortisation line from the adjustments section of the consolidated "
    "statement of cash flows, one entry per line. For every item, give its label "
    "exactly as printed, the physical PDF page and the printed page number."
)


def extract_raw(pdf_path: str, company_name: str, year: int) -> dict:
    """Extract raw line items from a PDF, reusing a saved result if one exists."""
    cache_file = OUTPUT_DIR / f"{Path(pdf_path).stem}.json"

    if cache_file.exists():
        print(f"Using cached extraction: {cache_file}")
        return json.loads(cache_file.read_text())

    pdf_file = client.files.upload(file=pdf_path)
    response = client.models.generate_content(
        model="gemini-flash-latest",
        contents=[pdf_file, PROMPT.format(company=company_name, year=year)],
        config={
            "response_mime_type": "application/json",
            "response_schema": RawFinancials,
        },
    )

    data = json.loads(response.text)
    OUTPUT_DIR.mkdir(exist_ok=True)
    cache_file.write_text(json.dumps(data, indent=2))
    return data
    