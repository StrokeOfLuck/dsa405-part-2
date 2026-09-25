# Raw data sources

This folder preserves the raw source material used for DSA 405 Project Milestone 2.

## 2025 House Periodic Transaction Reports

- **Producer:** Office of the Clerk, U.S. House of Representatives
- **Source:** House financial disclosure / periodic transaction report PDFs
- **Snapshot:** 515 PDFs archived under the scraper's 2025 source snapshot
- **Pinned upstream commit:** `510945b2b1d600dd90b183858b86419926b81e65`
- **Copied into this repository:** 2026-09-25
- **Location:** `data/raw/2025_pdfs/`
- **Integrity:** The PDFs are copied byte-for-byte from the pinned scraper snapshot. `2025_pdf_manifest.csv` records filenames, sizes, SHA-256 hashes, and the pinned source commit.
- **Rule:** Files in `data/raw/` are source data and must not be edited or overwritten by project code.

## 2025 House disclosure index

- **File:** `data/raw/2025FD.xml`
- **Producer:** Office of the Clerk, U.S. House of Representatives
- **Snapshot:** copied from the same pinned scraper commit
- **Copied into this repository:** 2026-09-25

Working and cleaned derivatives belong outside `data/raw/`. Raw files are retained unchanged so every cleaning decision can be checked against the source.
