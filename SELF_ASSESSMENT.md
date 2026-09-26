# DSA 405 P2: Sean Ryan’s self-scored rubric

**Student:** Sean Ryan (`sryan3`)  
**Confirmed:** September 26, 2026  
**Bench Check 1:** completed September 26, 2026, as reported by Sean.

These are Sean’s chosen self-assessment scores, confirmed in chat. They are not an instructor-awarded grade. Evidence is mapped to the [P2 rubric](https://github.com/jon-holt/DSA-405-Student/blob/main/course/DSA405_ProjectRubrics_FA26.md); the executed notebook is the primary submission.

| Criterion | Weight | Self-score | Evidence and judgment supporting the score |
|---|---:|---:|---|
| Diagnosis & data dictionary | ×2 | **4 — Excellent** | Notebook sections 1–2 show loaded/intended types, missingness counts and rates, distinct values, numeric ranges and categorical levels. All 66 final fields are documented. Defects checked for and not found are stated. The dictionary records the contradiction between the source’s explicit $2,000 amount and the original blank extraction. |
| Cleaning execution | ×2 | **4 — Excellent** | Section 3 records proportionate, source-supported choices: keep transactions with different quantities rather than deleting apparent duplicates; retain exact amounts rather than inventing range bounds; preserve the source-supported date; restore the explicit $2,000 value. All 7,667 rows remain. Before-values and original flags are preserved. |
| Cleaning log | ×3 | **4 — Excellent** | The 19 numbered entries include what changed, measured row/cell counts, reasons, information loss and reversal instructions. They cover human judgments as well as pipeline operations. The website’s review decisions and the notebook’s manual log entries use the same saved records. |
| Provenance brief | ×1 | **4 — Excellent** | Section 5 uses 166 words to explain the House Clerk source, why disclosures exist, the transaction-row meaning, filing-year scope, and what the data cannot establish. It distinguishes 449 parsed filings from 515 archived PDFs and explains the limitation for handwritten/scanned forms. |
| Tidy structure & reproducibility | ×2 | **4 — Excellent** | The PDF layout spreads transaction fields and continuation text across physical regions instead of consistent variable columns. Intentional geometry-based extraction produces one transaction per row with each field in a column. All eight notebook code cells have successful fresh-kernel outputs, accounting reconciles, and hashes verify raw-file preservation. The README documents source and run instructions; direct package versions and parser source are pinned. |

**Weighted mean:** `(4×2 + 4×2 + 4×3 + 4×1 + 4×2) / 10 = 4.0`.

**Self-assessed percentage:** `88 + (4.0 − 3) × 12 = 100%`.

## Limits retained with this assessment

These scores reflect the documented method and decisions; they do not claim that every transaction has been manually verified. Of 206 original parser-flagged rows, three have recorded human decisions and 203 remain unreviewed. Two additional unflagged rows were checked. One missing-range amount case and date warnings remain for review. The 66 PDFs without extracted rows remain archived. A fresh Colab installation has not been independently tested.

Sean confirmed the overall exceptions-and-limitations review on September 26, 2026. This does not claim individual review of the 203 remaining flagged rows. A final notebook check and Moodle submission remain outstanding. With more time, the next priorities would be additional PDF review of date and amount exceptions and an independent reproduction in another environment.

**AI assistance:** ChatGPT helped draft this evidence mapping. Sean selected and confirmed all five self-scores; the instructor determines the awarded grade.
