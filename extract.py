import os
import json
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel
import time
from google.genai import errors

load_dotenv()
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
OUTPUT_DIR = Path("outputs")
MODEL = "gemini-3.5-flash"


class LineItem(BaseModel):
    label_in_document: str
    value: float
    pdf_page: int
    printed_page: str


class RawFinancials(BaseModel):
    unit: str
    # Income statement
    revenue_current: LineItem
    revenue_prior: LineItem
    profit_before_tax: LineItem
    finance_costs: LineItem
    finance_income: LineItem
    net_profit: LineItem
    net_profit_attributable_to_owners: LineItem
    # Cash flow statement
    depreciation_amortisation: list[LineItem]
    operating_cash_flow: LineItem
    cash_and_cash_equivalents: LineItem
    escrow_in_cash_equivalents: Optional[LineItem] = None
    # Balance sheet
    total_assets: LineItem
    total_liabilities: Optional[LineItem] = None
    total_equity: LineItem
    equity_attributable_to_owners: LineItem
    borrowings: list[LineItem]
    current_assets: Optional[LineItem] = None
    current_liabilities: Optional[LineItem] = None


PROMPT = (
    "From the consolidated financial statements of {company} for fiscal year "
    "{year}, extract the requested line items for the current year. Do NOT "
    "calculate, combine or estimate anything: only copy values exactly as "
    "printed. Report every value as a positive number (ignore parentheses), "
    "except operating_cash_flow, which must be negative if it is a net outflow. "
    "Write the unit exactly as 'AED thousand'. "
    "For depreciation_amortisation, list every depreciation and amortisation "
    "line from the adjustments section of the consolidated statement of cash "
    "flows, one entry per line. "
    "For borrowings, list every borrowing, bank loan and sukuk line (both "
    "current and non-current) from the consolidated statement of financial "
    "position, one entry per line. Do not include lease liabilities. "
    "For cash_and_cash_equivalents, use the closing figure at the bottom of the "
    "consolidated statement of cash flows. "
    "For escrow_in_cash_equivalents, find the note on cash and bank balances and "
    "report only the escrow amount that the note says is INCLUDED in cash and "
    "cash equivalents. Ignore escrow held in restricted balances that are "
    "excluded from cash and cash equivalents. Return null if not disclosed. "
    "If the statement of financial position does not print a total for "
    "current assets, current liabilities or total liabilities, return null for "
    "that field. Never add these up yourself. "
    "For every item, give its label exactly as printed, the physical PDF page "
    "and the printed page number."
)



def extract_raw(pdf_path: str, company_name: str, year: int) -> dict:
    """Extract raw line items from a PDF, reusing a saved result if one exists."""
    cache_file = OUTPUT_DIR / f"{Path(pdf_path).stem}.json"

    if cache_file.exists():
        print(f"Using cached extraction: {cache_file}")
        return json.loads(cache_file.read_text())

    pdf_file = client.files.upload(file=pdf_path)

    for attempt in range(1, 6):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=[pdf_file, PROMPT.format(company=company_name, year=year)],
                config={
                    "response_mime_type": "application/json",
                    "response_schema": RawFinancials,
                },
            )
            break
        except errors.ServerError as e:
            print(f"Server error: {str(e)[:200]}")
            wait = 20 * attempt
            
            print(f"Gemini is busy (attempt {attempt}/5). Retrying in {wait}s...")
            time.sleep(wait)
    else:
        raise RuntimeError("Gemini unavailable after 5 attempts. Try again later.")

    data = json.loads(response.text)
    data["company"] = company_name
    data["fiscal_year"] = year
    data["model"] = MODEL
    OUTPUT_DIR.mkdir(exist_ok=True)
    cache_file.write_text(json.dumps(data, indent=2))
    return data