## Key Design Decisions

**Stated vs. calculated figures.** Not every number a company reports is printed 
directly in its financial statements — EBITDA, in particular, almost never appears 
as its own line item. To handle this, the tool tags every extracted figure as either 
"stated" (read directly off the page) or "calculated" (built by combining other line 
items, such as Profit before tax, Finance costs, Finance income, and Depreciation & 
amortisation). 

**Physical vs. printed page numbers.** Annual reports typically carry two separate page 
numbering systems: the PDF's actual page position in the file, and the page number 
printed on the page itself, which often restarts partway through the document (for 
example, at the start of the financial statements section). The tool records both for 
every citation. The reasoning behind the distinctioon is to allow users to navigate straight to the page without complications. In one of the reports used here, the printed "page 11" was 
actually the 13th physical page of the file.

**Unadjusted EBITDA.** The EBITDA this tool calculates is unadjusted, it does not strip 
out one-off or non-cash items the way a company's own "Adjusted EBITDA" typically does. 
For example, one company's calculated EBITDA includes a large gain from revaluing 
investment properties, simply because that gain flows through "Profit before tax," which 
the calculation starts from. A company's own reported adjusted figure would usually 
exclude that kind of gain to better reflect core operating performance. Anyone using this tool's EBITDA output should treat it as 
a raw, formula-based estimate rather than a substitute for a company's own adjusted metrics.

## Accuracy Results

Every extracted figure was manually verified against the source PDF before being 
counted as correct — not just checked for internal consistency, but opened in the 
actual document at the cited page.

**8 out of 8 data points verified correct** (revenue current year, revenue prior year, 
EBITDA, and net profit, across Aldar Properties and Emaar Properties, FY2025).

Two of the calculated EBITDA figures also cross-validated against a separately 
reported summary EBITDA figure elsewhere in the same document, independent of the 
line-by-line calculation — both matched.

This is a small, deliberately narrow sample: two companies, one fiscal year, four 
metric types, concentrated on figures that sit on a single financial 
statement page. This is a small, deliberately narrow sample — two companies, one fiscal year, four 
metric types, all figures that sit cleanly on a single financial statement page. It 
shows the extraction and citation approach works on real reports, but it hasn't been 
tested on different report formats, other industries, or less standardized metrics 
like working capital or debt schedules.

## Limitations and Next Steps

This v1 intentionally covers a narrow scope. Not yet built:

- Working capital, debt/cash flow figures, and financial ratios (the other three 
  metric categories from the original project idea)
- Testing across more than two companies or report formats
- Adjusted EBITDA (stripping out one-off items like revaluation gains)
- Automated verification — all checking so far was done manually against the source PDFs
- Unit and formatting consistency is enforced by prompt instruction, not by code — 
  a more robust version would validate and normalize this programmatically

## How to Run It

Requires Python 3.12 (not 3.14 — some dependencies don't yet have Apple Silicon-only 
wheels for the newest Python version on Intel Macs).

1. Clone or download this project folder
2. Create and activate a virtual environment:
python3.12 -m venv venv
source venv/bin/activate
3. Install dependencies: `pip install -r requirements.txt`
4. Create a `.env` file with `GEMINI_API_KEY=your_key_here` (get a free key at 
   aistudio.google.com/apikey)
5. Place annual report PDFs in a `reports/` folder
6. Run: `python3 extract_financials.py`