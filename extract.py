import os
import json
import time
from pathlib import Path
from typing import Optional, Literal
from dotenv import load_dotenv
from google import genai
from google.genai import errors
from pydantic import BaseModel

load_dotenv()
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
OUTPUT_DIR = Path("outputs")
MODEL = "gemini-3.5-flash"


class LineItem(BaseModel):
    label_in_document: str
    value: float
    pdf_page: int
    printed_page: str


class EscrowDisclosure(BaseModel):
    amount: float                       # in the statements' scale
    included_in_cash_equivalents: bool  # decided from the reconciliation table
    evidence_quote: str                 # exact sentence or table line from the report
    pdf_page: int
    printed_page: str


class RawFinancials(BaseModel):
    currency: str
    scale: Literal["units", "thousands", "millions"]
    # Income statement
    revenue_current: LineItem
    revenue_prior: LineItem
    profit_before_tax: LineItem
    finance_costs: LineItem
    finance_income: Optional[LineItem] = None
    net_profit: LineItem
    net_profit_attributable_to_owners: LineItem
    # Cash flow statement
    depreciation_amortisation: list[LineItem]
    operating_cash_flow: LineItem
    cash_and_cash_equivalents: LineItem
    escrow: Optional[EscrowDisclosure] = None
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
    "For currency, give the ISO code of the presentation currency (e.g. AED, "
    "SAR). For scale, state whether amounts are presented in units, thousands "
    "or millions, as the column headers of the statements say. Keep every "
    "value exactly as printed, in that scale. "
    "For net_profit, use the total profit for the year after tax, not gross "
    "profit and not profit from continuing operations only. "
    "If there is no separate finance income line, return null for "
    "finance_income. "
    "For depreciation_amortisation, list every depreciation and amortisation "
    "line from the adjustments section of the consolidated statement of cash "
    "flows, one entry per line. "
    "For cash_and_cash_equivalents, use the closing figure at the bottom of the "
    "consolidated statement of cash flows, not the balance sheet cash figure. "
    "For escrow, read the note on cash and bank balances. If it discloses cash "
    "held in escrow accounts from customer advances on property sales, report "
    "the amount (converted to the statements' scale if the note uses a "
    "different scale), copy the exact sentence or table line that discloses it "
    "as evidence_quote, and set included_in_cash_equivalents. To decide "
    "inclusion, use the reconciliation from cash and bank balances to cash and "
    "cash equivalents: escrow is included only if the cash and cash "
    "equivalents total is NOT reduced by the escrow amount. If the wording of "
    "the note and the reconciliation disagree, follow the reconciliation. "
    "Ignore escrow held on behalf of third parties that is not part of the "
    "group's bank balances. If no escrow is disclosed, return null. "
    "For borrowings, list every borrowing, bank loan and sukuk line (both "
    "current and non-current) from the consolidated statement of financial "
    "position, one entry per line. Do not include lease liabilities or bank "
    "overdrafts. "
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

    # Python, not the AI, decides which escrow figure the analysis uses.
    escrow = data.get("escrow")
    if escrow and escrow["included_in_cash_equivalents"]:
        data["escrow_in_cash_equivalents"] = {
            "label_in_document": escrow["evidence_quote"],
            "value": escrow["amount"],
            "pdf_page": escrow["pdf_page"],
            "printed_page": escrow["printed_page"],
        }
    else:
        data["escrow_in_cash_equivalents"] = None

    data["company"] = company_name
    data["fiscal_year"] = year
    data["model"] = MODEL
    OUTPUT_DIR.mkdir(exist_ok=True)
    cache_file.write_text(json.dumps(data, indent=2))
    return data