# DSA 405 · Project 2: Data Audit, Cleaning Log & Provenance

**Sean Ryan · Fall 2026 · `sryan3`**

This project audits reported U.S. House financial transactions extracted from 2025 disclosure PDFs. It explains how the data was produced, checks its quality, documents cleaning decisions and preserves the evidence needed to reverse those decisions. P2 covers this one source. Committee data and joins belong to P3.

**[Open the interactive project](https://strokeofluck.github.io/dsa405-part-2/docs/index.html)** · **[Read the executed notebook](https://strokeofluck.github.io/dsa405-part-2/docs/P2-notebook.html)** · **[Submission readiness](https://strokeofluck.github.io/dsa405-part-2/docs/index.html#submission-readiness)**

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/StrokeOfLuck/dsa405-part-2/blob/main/notebooks/DSA405_002_FA26_P2_sryan3.ipynb)

[Original House PTR scraper](https://github.com/StrokeOfLuck/house-ptr-scraper) · [This P2 repository](https://github.com/StrokeOfLuck/dsa405-part-2) · [Instructor's P2 requirements](https://github.com/jon-holt/DSA-405-Student/blob/main/assignments/projects/DSA405_P2_AuditCleaningLog_FA26.md) · [Course rubrics](https://github.com/jon-holt/DSA-405-Student/blob/main/course/DSA405_ProjectRubrics_FA26.md)

## Start here for grading

The required deliverable is [DSA405_002_FA26_P2_sryan3.ipynb](notebooks/DSA405_002_FA26_P2_sryan3.ipynb), with saved outputs. It contains all five required sections, in order:

1. Systematic audit of extracted source data.
2. Data dictionary for all final P2 columns.
3. Quantified cleaning log and reviewed decisions.
4. Row and column accounting.
5. Provenance brief, 166 words.

The website is a supplementary way to inspect the same work. Its grading links open focused evidence views; the pipeline tabs show code and source examples.

| Grading criterion | Weight | Evidence in this project | Open the evidence |
|---|---:|---|---|
| Diagnosis & data dictionary | ×2 | Loaded and intended types, missing counts/rates, distinct values, numeric ranges, short categorical domains, defect checks and defects not found. All 66 final fields have dictionary entries. | [Audit](https://strokeofluck.github.io/dsa405-part-2/docs/index.html#audit-inventory) · [Dictionary](https://strokeofluck.github.io/dsa405-part-2/docs/index.html#data-dictionary) · notebook sections 1–2 |
| Cleaning execution | ×2 | Source-supported retention decisions and one exact-amount correction. Before-values and original flags are retained; alternatives and uncertainty are explained. | [Cleaning decisions](https://strokeofluck.github.io/dsa405-part-2/docs/index.html#cleaning-execution) · notebook section 3 |
| **Cleaning log** | **×3** | **19 numbered decisions**, each with affected counts, rationale, information loss and reversal instructions. Human-review entries are generated from the recorded decisions used by the website. | [Original flags and reviews](https://strokeofluck.github.io/dsa405-part-2/docs/index.html#cleaning-log) · [Full notebook log](https://strokeofluck.github.io/dsa405-part-2/docs/P2-notebook.html#3.-Quantified-cleaning-log-and-reviewed-decisions) |
| Provenance brief | ×1 | A 166-word explanation of the producer, purpose, coverage and limitations, including digital versus scanned/handwritten PDFs. | [Provenance](https://strokeofluck.github.io/dsa405-part-2/docs/index.html#review-provenance) · notebook section 5 |
| Tidy structure & reproducibility | ×2 | One extracted transaction per row, reconciled row/column accounting, preserved raw files, successful saved execution, this README and exact direct dependency versions. | [Reproducibility](https://strokeofluck.github.io/dsa405-part-2/docs/index.html#reproducibility) · [requirements.txt](requirements.txt) · notebook sections 4 and setup |

These links identify supporting work, not awarded grades. [SELF_ASSESSMENT.md](SELF_ASSESSMENT.md) records Sean’s confirmed self-scores: 4 — Excellent on all five criteria (self-assessed 100%, not an instructor grade).

## Data source and scope

| Coverage | Saved result |
|---|---:|
| Archived PDFs | 515 |
| Filings with extracted transactions | 449 |
| PDFs without extracted transaction rows | 66 |
| Transaction rows retained | 7,667 |
| Extracted / resolver / final P2 columns | 50 / 61 / 66 |
| Rows removed by the P2 notebook | 0 |

The source is the [House Clerk's financial disclosure collection](https://disclosures-clerk.house.gov/FinancialDisclosure), using its [2025 filing index (XML)](https://disclosures-clerk.house.gov/public_disc/financial-pdfs/2025FD.xml). The repository contains a fixed archive, not a live inventory. `source_year = 2025` identifies the filing-index year; earlier transaction dates are retained.

This pipeline reads digital PDFs with selectable text. Handwritten or scanned forms need a more complex approach, such as OCR, which this pipeline does not perform. The 66 PDFs without extracted rows remain archived; zero extracted rows does not establish that a document reports no transactions. The website's random picker selects only the 449 filings with parsed transactions.

Raw inputs are preserved under [data/raw/](data/raw/): 515 PDFs, the XML index, a [SHA-256 manifest](data/raw/2025_pdf_manifest.csv), and [source notes](data/raw/SOURCES.md). They were copied from scraper commit `510945b2b1d600dd90b183858b86419926b81e65`. Project code verifies the archived files and copies them to `data/work/` before parsing; it does not write to `data/raw/`.

## Bundled source code

All five scripts and `config.py` are included in [vendor/house-ptr-scraper/src/](vendor/house-ptr-scraper/src/). [Source provenance](vendor/house-ptr-scraper/SOURCE.md) records their original commit and checksums. They are unchanged copies, and the rebuild uses these local files. The original repository is retained as attribution, not a runtime dependency.

## Five focused Python stages

The original automation has five scripts. Geometry is intentional: PDF text positions and column boundaries help associate values with the right transaction, whereas continuous text can mix neighboring fields.

1. **Collect the PDFs.** [stage1_download.py](https://github.com/StrokeOfLuck/dsa405-part-2/blob/main/vendor/house-ptr-scraper/src/stage1_download.py) reads the official filing index and downloads disclosure documents.
2. **Verify the collection.** [stage2_verify.py](https://github.com/StrokeOfLuck/dsa405-part-2/blob/main/vendor/house-ptr-scraper/src/stage2_verify.py) checks the index against available PDFs to identify missing documents.
3. **Extract using geometry.** [stage3_extract.py](https://github.com/StrokeOfLuck/dsa405-part-2/blob/main/vendor/house-ptr-scraper/src/stage3_extract.py) uses text positions and column boundaries to extract transaction fields and records uncertainty.
4. **Clean up tickers and related fields.** [stage4_clean.py](https://github.com/StrokeOfLuck/dsa405-part-2/blob/main/vendor/house-ptr-scraper/src/stage4_clean.py) resolves ticker candidates, cleans related asset text and updates ticker-related flags while preserving prior values. It is not a general date or amount correction stage.
5. **Prepare CSV outputs.** [publish_latest.py](https://github.com/StrokeOfLuck/dsa405-part-2/blob/main/vendor/house-ptr-scraper/src/publish_latest.py) prepares the processed tables for downstream use.

For P2, [rebuild_2025.py](scripts/rebuild_2025.py) verifies the committed archive against its manifest, makes working copies and verifies and runs the bundled extraction, cleanup and export scripts. It does not redownload the raw PDFs or rerun the original live collection process. The notebook then performs the audit and documented P2 corrections. The website's six lesson tabs are not six scraper stages.

## Original flags, human decisions and remaining uncertainty

[decisions.json](data/review/decisions.json) records four confirmed review cases covering five rows:

1. Retain the January 13 date after checking the PDF.
2. Retain two similar transactions because their quantities differ.
3. Retain the reported exact $800 amount with blank range bounds.
4. Restore the explicitly reported $2,000 amount in one row, changing two value cells.

The notebook validates each decision's recorded flags and before-values against the parser output, applies the correction and generates its manual cleaning-log entries from the same records. Original `needs_review`, `review_reason` and `review_level` fields remain as history. A recorded outcome does not automatically clear unrelated issues.

Of **206 originally flagged rows**, three have recorded human decisions and **203 remain unreviewed**. Two additional unflagged rows were checked. One missing-range amount case remains unresolved, and date warnings remain for source review. There are 640 raw-date shape flags and zero readable-prefix disagreements; neither result establishes that all dates are correct. Targeted PDF reviews are not a dataset-wide accuracy estimate.

The website explains why each original flag appeared and what to check in the PDF. Its filters change the display only; they do not save new decisions. The required notebook log also records general extraction and cleaning decisions beyond these five reviewed rows.

## Reproduce the notebook

Use **Python 3.12**. The successful saved run used Python 3.12.14 on Windows. Internet access is needed to obtain P2 and install dependencies. The parser code is bundled in `vendor/house-ptr-scraper/`; P2 does not fetch the original PTR repository. A downloaded ZIP can be used instead of Git.

1. Clone this repository and open a terminal in its root.
2. Create and activate a virtual environment using your usual Python tooling.
3. Install the exact direct dependencies:

```bash
python -m pip install -r requirements.txt
python -m pip check
```

4. Open [the notebook](notebooks/DSA405_002_FA26_P2_sryan3.ipynb) in a notebook editor, select that environment, restart the kernel and run all cells. The setup cell calls the rebuild script automatically.
5. Save the notebook with its outputs. The final cells check accounting, row keys, preserved values, the CSV round-trip, raw-file hashes and the two-cell correction.

To run only the extraction/cleanup pipeline from the terminal:

```bash
python scripts/rebuild_2025.py
```

This command does not replace the notebook audit or apply its P2 review decisions. A later notebook run can reuse the parser checkpoint.

**Colab:** use the badge above and choose Runtime → Run all. The setup cell clones the repository and installs dependencies. A fresh Colab installation/run has not been independently verified.

**Verified execution:** on September 26, 2026, all eight code cells passed in a fresh kernel after moving the old parser working folder aside. All 515 PDFs were processed from scratch using the six bundled source files, with no PTR repository download. The result retained 7,667 rows and all raw-file hash checks passed. All eight code cells have successful saved outputs. The initial run rebuilt extraction in a fresh working folder; subsequent fresh-kernel runs reused the parser checkpoint while executing every notebook cell. All 518 raw files were unchanged by hashes. The installed environment passes `pip check`. [requirements.txt](requirements.txt) pins nine direct packages to those installed versions; it is not a full cross-platform environment lock.

## Files and website refresh

| Location | Purpose |
|---|---|
| [notebooks/](notebooks/) | Required notebook with saved outputs |
| [data/raw/](data/raw/) | Immutable PDF archive, index and manifest |
| [data/review/decisions.json](data/review/decisions.json) | Confirmed human review decisions |
| `data/work/` | Recreated parser working files and checkpoints, ignored by Git |
| `data/clean/` | Notebook-generated final CSV, dictionary, log, audit, accounting and validation summary, ignored by Git |
| [docs/data/house_ptr_2025_p2.csv](docs/data/house_ptr_2025_p2.csv) | Published copy of the corrected full dataset |
| [docs/](docs/) | Supplementary walkthrough and notebook HTML |
| [SELF_ASSESSMENT.md](SELF_ASSESSMENT.md) | Confirmed student self-scores with supporting evidence and limitations |

After rerunning the notebook, refresh the dictionary, review view and all 449 individual filing downloads:

```bash
python scripts/export_p2_review.py
python -m http.server 8000 --directory docs
```

Open `http://localhost:8000/`. Final filing downloads match the corrected notebook dataset. Earlier pipeline steps deliberately show original parser values; saved teaching snippets explain those steps, while the submitted notebook contains the current complete audit and correction code. Clicking the website does not rerun Python.

For changes to PDF geometry examples, [build_pipeline_demo.py](scripts/build_pipeline_demo.py), [trace_geometry.py](scripts/trace_geometry.py) and [validate_pipeline_demo.py](scripts/validate_pipeline_demo.py) provide the separate demo-building workflow. Rerun the P2 export after rebuilding demo assets so final filing downloads retain the reviewed corrections.

## Submission checklist

Due **October 1, 2026, 11:59 PM**, according to the P2 handout.

- [x] All five required sections are in one notebook, in order.
- [x] Successful fresh-kernel execution with saved outputs is recorded.
- [x] Raw inputs are preserved; row/column accounting reconciles.
- [x] README includes purpose, source and reproduction steps.
- [x] Direct dependency versions are pinned.
- [x] Reviewed the outstanding exceptions and documented the remaining limitations. Unresolved rows remain flagged for future review. Sean confirmed the overall review on September 26, 2026; 203 rows remain individually unreviewed.
- [x] Self-scored rubric confirmed by Sean on September 26, 2026: all five criteria scored 4.
- [x] Bench Check 1 completed September 26, 2026, as reported by Sean.
- [ ] Final check of the saved notebook before upload.
- [ ] Submit the notebook, this repository link and confirmed rubric to Moodle.

The website is supplementary. Moodle submission remains outstanding; Sean reported completing Bench Check 1. AI assisted with code, documentation and review presentation; Sean confirmed the four manual review cases. The notebook includes the assistance disclosure.
