# AI Financial Statement Analyzer — Gulf Real Estate Developers

A Python tool that reads company annual reports (PDF), extracts raw financial
line items with an LLM, and computes leverage, profitability and cash-quality
metrics in code — with a page citation for every figure and an automated
accuracy test against hand-verified values.

Applied to six listed GCC developers (FY2025): Aldar, Emaar, Deyaar, Union
Properties, RAK Properties (UAE) and Dar Al Arkan (Saudi Arabia).

Results table: [results.md](results.md)

## How it works

1. **Extract (`extract.py`)** — each PDF is sent to Google Gemini with a strict
   JSON schema. The model only *copies* line items as printed (label, value,
   physical PDF page, printed page). It never calculates.
2. **Compute (`analyze.py`)** — Python computes every metric: EBITDA, adjusted
   EBITDA, net debt (with and without escrow), net debt / EBITDA, ROE, cash
   conversion, and a balance-sheet identity check (assets = liabilities + equity).
3. **Evaluate (`evaluate.py`)** — compares extractions against a ground-truth
   file of 30 values I verified by hand, blind, before running the model.
4. **Report (`report.py`)** — builds the comparison table from cached results.

Extractions are cached, so changing a formula never requires calling the API again.

## Key design decisions

**The AI copies, Python calculates.** In v1 the model computed EBITDA itself and
once reported two different EBITDA figures in the same answer, updating only one
margin. Moving all arithmetic into code makes results reproducible and auditable.

**Escrow-adjusted net debt.** In the UAE, buyers' payments for off-plan
properties sit in escrow accounts that can only fund the related project.
Several developers include this cash in "cash and cash equivalents", which makes
leverage look lower than it is. The tool extracts the escrow amount, decides
whether it is included using the cash reconciliation table (not the narrative
text, which can contradict it), stores the exact sentence from the report as
evidence, and reports net debt both ways.

**Fail visibly, not silently.** When the model cannot find an escrow disclosure,
the tool reports "NOT FOUND – verify manually" instead of assuming there is
none. Unknown currencies also raise an error instead of guessing an exchange rate.

**Adjusted EBITDA.** Reported EBITDA includes property revaluation gains,
disposal gains and associates' results. Adjusted EBITDA removes four categories
(fair value, property disposals, associates/JVs, property impairments) —
broadly the approach Aldar uses in its own investor materials, applied
identically to all companies.

**Comparable units.** The model reports each statement's currency and scale;
Python converts absolute amounts to AED millions (SAR converted at the fixed
USD-peg cross rate). Ratios are unaffected by currency.

**Traceability.** Every extraction records the model version that actually
answered (model aliases were silently redirected to newer versions during the
project).

## Accuracy

Ground truth: 30 values (revenue, net profit, cash, borrowings, escrow × 6
companies), verified by hand against the PDFs before seeing the model's output.

| Run | Result |
|---|---|
| First run, untuned | 28/30 = 93.3% |
| After escrow redesign (same companies) | 29/30 = 96.7% |
| Final run, gemini-3.8-flash (6 companies) | 30/30 = 100% |

RAK and Dar Al Arkan are flagged "Not found – verify": a manual check of their
cash notes confirmed neither discloses escrow balances.

Core figures (revenue, profit, cash, borrowings) were correct in every run. All
errors were escrow judgements on scanned PDFs. The second and third results are
measured on the same companies used to design the fixes, so they overstate
real-world accuracy; a fair test needs companies the tool has never seen.

## Findings (FY2025)

- **Escrow changes the leverage story.** Aldar's net debt / EBITDA is 0.98x as
  reported but 2.03x excluding escrow cash. Emaar's apparent AED 42.8bn net cash
  is close to zero once escrow is excluded.
- **Deyaar:** ~89% of its cash and cash equivalents is escrow (note 12). The first
  model missed this disclosure on the scanned PDF and the tool flagged it for
  manual review; the final model found it. Excluding escrow, Deyaar moves from
  AED 1.7bn net cash to AED 174m net debt.
- **Earnings quality varies widely.** Non-recurring items are 3% of Emaar's
  EBITDA, 10% of RAK's, 12% of Aldar's, 14% of Dar Al Arkan's and 39% of Deyaar's.
  **Union Properties reports a 76% EBITDA margin, but 99.8% of its EBITDA comes
  from property disposals and revaluations: its adjusted margin is 0.2%.**
- **Dar Al Arkan** has negative operating cash flow and the highest leverage of
  the group (3.4x net debt / EBITDA), reflecting heavy land and development
  investment.

## Limitations and next steps

- Single fiscal year — no trends yet. Next: three years per company.
- Small sample (6 companies); accuracy on unseen reports is unmeasured.
- On scanned PDFs a model can miss notes deep in the document (the first model
  missed Deyaar's escrow note); results depend on the model version.
- The ground truth does not cover D&A or adjustment items: switching models
  changed RAK's EBITDA by 2.4% (the new figure matches a manual check) without
  the test detecting it.
- Free-tier API limits and outages; retries and caching mitigate but do not remove this.
- Adjusted EBITDA uses a fixed definition; a company's own adjusted figure may differ.

## How to run

Python 3.12 (on Intel Macs, `cryptography<46` is pinned because newer versions
ship no x86 macOS wheels).

    python3.12 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    # .env: GEMINI_API_KEY=your_key   (free key at aistudio.google.com/apikey)
    # put annual-report PDFs in reports/
    python3 analyze.py
    python3 evaluate.py
    python3 report.py