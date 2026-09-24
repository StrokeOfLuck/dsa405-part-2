# DSA 405 — P2: House PTR PDF audit and cleaning log

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/StrokeOfLuck/dsa405-part-2/blob/main/notebooks/DSA405_002_FA26_P2_sryan3.ipynb)

This is a **separate class project**. It copies 2025 source files, builds two transaction CSVs with the [House PTR scraper](https://github.com/StrokeOfLuck/house-ptr-scraper)'s original parser and ticker resolver, then audits the differences. It does not alter the scraper repository.

## Visual walkthrough

[`docs/index.html`](docs/index.html) follows one real PTR from its PDF page through raw extracted text, Stage 3 transaction fields, Stage 4 ticker review, Part 2 date checks, and a downloadable CSV containing **all rows from that filing**. The Random filing button selects among eight fixed examples from the 2025 batch. The walkthrough is a reproducible snapshot, not a live scraper.

After the full 2025 rebuild, regenerate the static examples with:

```bash
python scripts/build_pipeline_demo.py
python -m http.server 8000 --directory docs
```

Open `http://localhost:8000/`. The script writes `docs/data/examples.json`, eight per-filing CSVs, and first-page images. It reads verified working PDFs and CSVs without changing source files. GitHub Pages can serve the `docs/` folder from the `main` branch.

## Where the data comes from

The source is the official U.S. House periodic transaction disclosure PDFs. `data/raw/2025_pdf_manifest.csv` records the filename, size, SHA-256, and pinned scraper commit for each of **515 archived 2025 PDFs**. The source code and archived files are fetched from scraper commit `510945b2b1d600dd90b183858b86419926b81e65`. The 2025 disclosure XML index is also copied. The files total about 51 MB.

To keep this assignment repo small, the 515 PDFs are copied **when the notebook runs** into `data/work/01_pdfs/2025/` and checked against the committed manifest. The code only reads `data/raw/2025_pdf_manifest.csv`; it never writes in `data/raw/`. The original archived PDFs remain untouched in the scraper repository. The PDF bytes are not committed as 515 duplicate Git blobs. The first run requires Git and Internet access. Colab runtimes are temporary, so save the executed notebook before leaving.

## Run

**Colab:** Click the button above, then choose **Runtime → Run all**. The notebook clones this P2 repo into the Colab session, installs its dependencies, copies and checks the 2025 files in its working folder, runs the PDF parser and ticker resolver, and displays the audit. This is a full-year CPU run and can take several minutes. If the runtime stops, running it again can resume from the parser checkpoint.

**Local:** Use Python 3.10+ and Git. From the repo root:

```bash
python -m pip install -r requirements.txt
python scripts/rebuild_2025.py
```

Then open `notebooks/DSA405_002_FA26_P2_sryan3.ipynb` and run all cells. It will reuse the checked files and parser checkpoint. Run the notebook from a restarted kernel before submission.

## Generated files

- `data/work/04_transactions/transactions_raw.csv`: V8.1 extraction from 2025 PDFs.
- `data/work/04_transactions/transactions_resolved.csv`: V8.2 after ticker and asset cleanup. In this 2025 batch the resolver added classifications and audit columns but changed **zero** of the six compared values.
- `data/clean/house_ptr_2025_p2.csv`: V8.2 plus three class audit fields for raw date text and date-prefix comparison.
- `data/work/06_public/house_ptr_transactions_latest.csv` and `house_ptr_transactions_web.csv`: standalone published outputs from this P2 copy.
- `data/work/05_status/checkpoint.csv` and `data/work/04_transactions/needs_fallback.csv`: extraction status and PDFs that need fallback review.

Generated files are ignored by Git and recreated by the notebook. `source_year = 2025` means the **filing index year**, not necessarily the transaction year. The notebook logs measured Stage 3 parsing decisions, Stage 4 classifications and class QA decisions with exact row counts. It found 640 raw date text fields with extra PDF text but zero disagreements between the leading raw date and the resolved transaction date. V8.1 values remain beside V8.2 results. It does not claim that Stage 3 PDF extraction is error-free; review flagged cases against the linked source PDFs.

## Submission

Inspect the audit exceptions and a sample of original PDFs, document any manual changes in the numbered cleaning log, save executed notebook outputs, and submit the notebook and repo link with the course's self-scored rubric. P2 uses one source; committee rosters and joins remain for P3.
