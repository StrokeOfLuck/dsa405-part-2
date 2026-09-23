# DSA 405 — Part 2: House PTR data audit

This is a separate class project. It does not write to or run the [House PTR scraper](https://github.com/StrokeOfLuck/house-ptr-scraper).

## Input and origin

`data/raw/house_ptr_transactions_filing_year_2025.csv.gz` is a losslessly compressed frozen subset of `data/06_public/house_ptr_transactions_latest.csv` from scraper commit `510945b2b1d600dd90b183858b86419926b81e65` (captured September 23, 2026). It includes **all 7,667 records where `source_year` is 2025**, retaining every column and field value from those rows. `source_year` is the filing index year; a transaction may have occurred in another year. The full upstream export held 27,070 rows. The SHA-256 of the uncompressed 2025 snapshot is `f71ebe00aa6b028ef57fe864158dc8501f67e3690adeffdd1090e1a9e21632a6`; pandas reads the `.csv.gz` directly. The official source of each disclosure is linked in `original_pdf_url`.

The scraper had already extracted and resolved fields from PDFs before this snapshot. This project's *raw input* means the untouched input to the P2 audit, not the original PDFs. Extraction choices and any OCR or layout errors remain upstream and are limits of this audit.

## Run

1. Use Python 3.10+ and install: `python -m pip install -r requirements.txt`.
2. Open `notebooks/DSA405_002_FA26_P2_sryan3.ipynb` (named with your Unity ID).
3. Run all cells from a restarted kernel, or run `python -m jupyter nbconvert --execute --to notebook --inplace notebooks/DSA405_002_FA26_P2_sryan3.ipynb` from the repo root.
4. Review the displayed exceptions against their linked PDFs. Fill in the judgment sections and self-score the course rubric before submission. Submit notebook and repo link on Moodle.

The notebook audits the source, creates a data dictionary and quantified cleaning log, and writes `data/clean/house_ptr_2025_clean.csv`. The raw snapshot is never overwritten. The generated clean file is ignored by Git because the notebook recreates it.

The 2025 audit identifies 640 source-like date strings that do not parse as standalone `MM/DD/YYYY` dates, often because surrounding PDF text is attached; 617 of these rows have `needs_review = False`. These are candidates for source-PDF checks, not automatically incorrect resolved transaction dates.

## Scope

P2 covers one source only. Committee rosters, joins, network analysis, and final verification belong to later work. The file contains *reported transactions*, not verified trade execution or exact transaction amounts. An amount band is not a precise dollar value. Do not convert uncertain extracted text into a confident value without checking its PDF.
