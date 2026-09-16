import os
import json
from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel

load_dotenv()
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])


# This defines the exact shape we want the AI's answer to come back in.
# Every extracted number carries its own citation with it.
from typing import Literal


class FinancialMetric(BaseModel):
    value: float
    unit: str
    pdf_page: int
    printed_page: str
    derivation: Literal["stated", "calculated"]  # was it printed as-is, or built from other figures?
    calculation_note: str  # if calculated: which line items and formula were used; if stated: leave empty


class FinancialSummary(BaseModel):
    company: str
    fiscal_year: int
    revenue_current_year: FinancialMetric
    revenue_prior_year: FinancialMetric
    ebitda_current_year: FinancialMetric
    ebitda_margin_current_year_pct: float
    net_profit_current_year: FinancialMetric   # <-- add this line


def extract_financials(pdf_path: str, company_name: str) -> dict:
    """Uploads a PDF and asks Gemini to extract revenue and EBITDA with citations."""

    pdf_file = client.files.upload(file=pdf_path)

    response = client.models.generate_content(
        model="gemini-flash-latest",
        contents=[
            pdf_file,
            f"Extract {company_name}'s total revenue (current and prior year) and "
            "EBITDA (current year) with margin, from the consolidated financial "
            "statements. For every figure, give the physical PDF page number and "
            "the page number printed on the page. For EBITDA specifically: state "
            "whether it appears as a printed line item ('stated') or was calculated "
            "by you from other line items ('calculated'), and if calculated, show "
            "exactly which line items and formula you used. Also extract net "
            "profit for the year (profit after tax) for the current year, with "
            "the same page citation requirements. Format all unit fields "
"exactly as 'AED thousand', regardless of how the document itself "
"abbreviates it."
        
        ],
        config={
            "response_mime_type": "application/json",
            "response_schema": FinancialSummary,
        },
    )

    return json.loads(response.text)


if __name__ == "__main__":
    aldar_data = extract_financials("reports/aldar_2025.pdf", "Aldar Properties")
    print(json.dumps(aldar_data, indent=2))

    emaar_data = extract_financials("reports/emaar_2025.pdf", "Emaar Properties")
    print(json.dumps(emaar_data, indent=2))