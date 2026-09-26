# DSA 405 — P2: House PTR PDF audit and cleaning log

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/StrokeOfLuck/dsa405-part-2/blob/main/notebooks/DSA405_002_FA26_P2_sryan3.ipynb)

This is a **separate class project**. It copies 2025 source files, builds two transaction CSVs with the [House PTR scraper](https://github.com/StrokeOfLuck/house-ptr-scraper)'s original parser and ticker resolver, then audits the differences. It does not alter the scraper repository.

## Review progress

**[Open the visual progress preview](https://strokeofluck.github.io/dsa405-part-2/docs/index.html#audit)** — source-PDF excerpts, approved review decisions, the approved provenance brief, and the remaining submission checklist.

[Review decision record](REVIEW_PROGRESS.md). The notebook has now executed successfully with saved outputs: 7,667 rows, 66 final columns, 66 dictionary entries and 19 logged decisions. The approved $2,000 correction is applied to one row with old values preserved. Sean still needs to review the self-assessment, confirm Bench Check scheduling and submit to Moodle.

- **[Read the executed notebook](https://strokeofluck.github.io/dsa405-part-2/docs/P2-notebook.html)**
- **[Review the self-assessment draft](SELF_ASSESSMENT_DRAFT.md)** (proposed scores, not yet confirmed by Sean)

## Visual walkthrough

[![Open the visual walkthrough — follow a real PDF to CSV with clickable explanations and highlighted code](docs/assets/walkthrough-button.svg)](https://strokeofluck.github.io/dsa405-part-2/docs/index.html)

Follow a random 2025 PTR from its PDF page to a downloadable CSV containing **all rows from that filing**. The button draws from all **515 archived PDFs**, with no dropdown. Of these, 449 produced 7,667 transaction rows; the other 66 show an explicit fallback result without inventing a transaction or CSV. The archive is a pinned snapshot, not a live list of every filing currently available.

1. The selected filing's member, ID, and row count fill the selection box.
2. The PDF inspector highlights the actual physical row. Select a column to see its clipping rectangle, embedded text, and text after the parser's character/whitespace cleanup.
3. Follow that transaction through Stage 3 fields, Stage 4 ticker decisions, and Part 2 date checks.
4. Read the complete source file or notebook cell in the left panel. The relevant function and line are highlighted; code-block buttons expose every notebook cell in its matching step.
5. Download the selected filing's CSV. The notebook's `p2.to_csv(...)` writes the full-year file; the walkthrough's download is a filtered copy.

The walkthrough uses a synchronized split view: complete source code on the left, PDF and results on the right. Choose a pipeline step to show its code and visual together. Click a PDF field to highlight the clipping function, or use the code-block buttons to inspect other functions and notebook cells for that step. The source-file selector exposes all ten complete files and the original-source link opens GitHub or Colab. On narrow screens the code and visuals stack. Third-party library implementations are not bundled.

Geometry is observed at the exact point where the pinned parser accepts a new transaction after duplicate handling. `scripts/trace_geometry.py` adds an in-memory observer without editing the upstream source or changing its parsing decisions. The builder reruns that parser and checks the observed fields against the rebuilt CSV before publishing a highlight. Continuations can contribute additional text to the final transaction. Coordinates use PDF points from the top-left; the illustrated code substitutes the selected rectangle's numeric values.

After the full 2025 rebuild, regenerate the static examples with:

```bash
python scripts/build_pipeline_demo.py
python scripts/validate_pipeline_demo.py
python -m http.server 8000 --directory docs
```

Open `http://localhost:8000/`. The builder writes `docs/data/examples.json` (index and code), 515 individual records under `docs/data/filings/`, 515 page images, and 449 per-filing CSVs. Each image shows the selected transaction's page, which may be later than page one. The browser fetches only the selected record and image, then caches the record for that session. A `?filing=20033604` link opens a specific filing. Validation checks every asset, row count, field highlight, code line, notebook cell, and CSV audit value. Source PDFs and pipeline CSVs remain unchanged.

## Where the data comes from

The source is the official U.S. House periodic transaction disclosure PDFs. This repository now preserves the complete pinned 2025 source snapshot directly in `data/raw/`: **515 unmodified PDFs** in `data/raw/2025_pdfs/`, the House disclosure index `data/raw/2025FD.xml`, `data/raw/2025_pdf_manifest.csv`, and `data/raw/SOURCES.md`. The manifest records each PDF's filename, size, SHA-256, and pinned scraper commit. The 515 PDFs total about 51 MB.

The raw files were copied byte-for-byte from scraper commit `510945b2b1d600dd90b183858b86419926b81e65`. Project code never writes to `data/raw/`. When the notebook runs, `scripts/rebuild_2025.py` verifies the committed PDFs against the manifest and copies them into `data/work/01_pdfs/2025/` before parsing. The pinned scraper repository is still fetched for the parser source code, but the raw dataset itself is contained in this repository.

## Run

**Colab:** Click the button above, then choose **Runtime → Run all**. The notebook clones this P2 repo into the Colab session, installs its dependencies, verifies the committed `data/raw/` snapshot, copies those files into its working folder, runs the pinned PDF parser and ticker resolver, and displays the audit. This is a full-year CPU run and can take several minutes. If the runtime stops, running it again can resume from the parser checkpoint.

**Local:** Use Python 3.10+ and Git. From the repo root:

```bash
python -m pip install -r requirements.txt
python scripts/rebuild_2025.py
```

Then open `notebooks/DSA405_002_FA26_P2_sryan3.ipynb` and run all cells. It will reuse the checked files and parser checkpoint. Run the notebook from a restarted kernel before submission.

## Generated files

- `data/work/04_transactions/transactions_raw.csv`: V8.1 extraction from 2025 PDFs.
- `data/work/04_transactions/transactions_resolved.csv`: V8.2 after ticker and asset cleanup. In this 2025 batch the resolver added classifications and audit columns but changed **zero** of the six compared values.
- `data/clean/house_ptr_2025_p2.csv`: V8.2 plus three date-audit fields, two pre-P2 amount backups and the approved correction to filing 20033320, transaction 1 ($2,000 exact amount).
- `data/work/06_public/house_ptr_transactions_latest.csv` and `house_ptr_transactions_web.csv`: standalone published outputs from this P2 copy.
- `data/work/05_status/checkpoint.csv` and `data/work/04_transactions/needs_fallback.csv`: extraction status and PDFs that need fallback review.

Generated files are ignored by Git and recreated by the notebook. `source_year = 2025` means the **filing index year**, not necessarily the transaction year. The notebook logs Stage 3 parsing decisions, Stage 4 classifications, selected manual retention decisions and the single-row P2 correction with exact counts and reversal instructions. It found 640 raw date text fields with extra PDF text but zero disagreements between the leading raw date and the resolved transaction date. V8.1 values remain beside V8.2 results. It does not claim that Stage 3 PDF extraction is error-free; review flagged cases against the linked source PDFs.

## Submission

Inspect the audit exceptions and a sample of original PDFs, document any manual changes in the numbered cleaning log, save executed notebook outputs, and submit the notebook and repo link with the course's self-scored rubric. P2 uses one source; committee rosters and joins remain for P3.

## Current validation and remaining review

The saved notebook was executed from a fresh Python kernel. The initial run rebuilt all 515 PDFs in a fresh working folder; the final run reused that parser checkpoint while rerunning every notebook cell. The notebook checks raw-file hashes before/after, row keys, column accounting, the CSV round-trip, and that only two original value cells changed. Software versions are recorded in the final output. Execution was local on Windows, not independently repeated in Colab.

The reviewed PDF copies were hash-matched to the committed archive. These are targeted source checks, not an accuracy estimate for the whole dataset. One unresolved missing-range amount case remains flagged. Preserve the original review flags as history; the P2 log records human decisions separately.

The walkthrough demonstrates the original parsing stages and the corrected final P2 output. Individual filing CSV downloads match the executed notebook's `data/clean/house_ptr_2025_p2.csv`. No upstream scraper files were changed.

Raw PDFs originate at `https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/2025/<filing_id>.pdf`; the exact archive comes from scraper commit `510945b2b1d600dd90b183858b86419926b81e65` and was copied into this repository on September 25, 2026.

Required Moodle package: `DSA405_002_FA26_P2_sryan3.ipynb`, this repository link, and Sean's confirmed self-scored rubric. The HTML pages are supplementary. Bench Check scheduling and Moodle submission remain Sean's responsibility and have not been performed here.

The main walkthrough now includes the source-review evidence and checklist under **05 · Audit**, and the complete generated data dictionary under **06 · CSV**. The old review-page URL redirects there.

To refresh the same-page dictionary and cleaning log after rerunning the notebook, run `python scripts/export_p2_review.py` from the repository root. This copies the corrected full-year CSV and generated reference tables into `docs/data/`.

## Original flags and human review

`data/review/decisions.json` records the four confirmed decisions covering five rows. The notebook validates original flags and before-values, applies the approved correction, and generates the manual cleaning-log entries from these records. Original flags remain unchanged; human outcomes do not automatically clear unrelated issues. Of 206 flagged rows, three have recorded decisions and 203 remain unreviewed; two additional unflagged rows were checked.

Under **05 · Audit**, the website displays original flags alongside decisions, PDF evidence, before/after values and reversal instructions. Filters only change what is displayed; they do not save new decisions. The separate cleaning-log download button was removed; the required notebook log retains general cleaning steps too.

After running the notebook, run `python scripts/export_p2_review.py` to refresh the dictionary, original-flag reviews, and all individual filing CSVs from the same corrected dataset. Stage 3 teaching examples retain original parser values; final CSV previews/downloads contain the reviewed P2 values.
