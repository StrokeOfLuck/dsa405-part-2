"""Build a small, reproducible static tour of real 2025 House PTR filings.

Run after scripts/rebuild_2025.py. The output is a snapshot, not a live parser.
No source PDFs or pipeline CSVs are edited.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import fitz
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "data" / "work"
OUT = ROOT / "docs"
SOURCE_COMMIT = "510945b2b1d600dd90b183858b86419926b81e65"
DISPLAY_FIELDS = [
    "filing_id", "politician", "owner", "asset_v8_2_cleaned",
    "ticker_v8_2_cleaned", "transaction_type", "transaction_date",
    "amount_min", "amount_max", "amount_category", "needs_review",
    "original_pdf_url", "raw_date_has_extra_text", "raw_date_prefix",
    "date_prefix_disagrees",
]


def prepare_final(resolved: pd.DataFrame) -> pd.DataFrame:
    """Reproduce the three P2 date-audit fields from the notebook."""
    final = resolved.copy()
    date_text = final.transaction_date_raw
    final["raw_date_has_extra_text"] = ~date_text.str.fullmatch(r"\d{1,2}/\d{1,2}/\d{4}")
    final["raw_date_prefix"] = date_text.str.extract(
        r"^(\d{1,2}/\d{1,2}/\d{4})", expand=False
    ).fillna("")
    parsed = pd.to_datetime(
        final.raw_date_prefix.replace("", pd.NA), format="%m/%d/%Y", errors="coerce"
    ).dt.strftime("%Y-%m-%d").fillna("")
    final["date_prefix_disagrees"] = parsed.ne("") & parsed.ne(final.transaction_date)
    return final


def text_record(row: pd.Series, fields: list[str]) -> dict[str, str]:
    return {key: str(row[key]) for key in fields}


def source_excerpt(text: str, start: str, end: str) -> str:
    """Copy an exact, contiguous excerpt; fail if the source changes."""
    assert start in text and end in text, (start, end)
    return text[text.index(start):text.index(end) + len(end)].rstrip()


def code_examples() -> dict[str, list[dict[str, str]]]:
    """Keep the webpage snippets tied to the real notebook and pinned scripts."""
    notebook = json.loads((ROOT / "notebooks" / "DSA405_002_FA26_P2_sryan3.ipynb").read_text())
    cells = notebook["cells"]
    code = lambda index: "".join(cells[index]["source"])
    notebook_url = "https://colab.research.google.com/github/StrokeOfLuck/dsa405-part-2/blob/main/notebooks/DSA405_002_FA26_P2_sryan3.ipynb#scrollTo="
    source_url = f"https://github.com/StrokeOfLuck/house-ptr-scraper/blob/{SOURCE_COMMIT}/src/"
    parser = (WORK / "../upstream/house-ptr-scraper/src/stage3_extract.py").resolve().read_text()
    resolver = (WORK / "../upstream/house-ptr-scraper/src/stage4_clean.py").resolve().read_text()
    builder = Path(__file__).read_text()

    def nb(index: int, label: str, excerpt: str, explanation: str) -> dict[str, str]:
        return {"label": label, "source": "Colab notebook", "url": notebook_url + cells[index]["id"],
                "code": excerpt, "explanation": explanation}

    def src(label: str, source: str, url: str, excerpt: str, explanation: str) -> dict[str, str]:
        return {"label": label, "source": source, "url": url, "code": excerpt,
                "explanation": explanation}

    return {
        "source": [nb(3, "Run the pinned rebuild", source_excerpt(
            code(3), 'log_path=Path("data/work/rebuild.log")',
            'raise RuntimeError(f"Pipeline failed. Inspect {log_path} for the stage and error.")'),
            "The notebook runs the separate rebuild script, saves its messages, and stops if it fails. That script checks the PDF copies against the manifest before parsing them.")],
        "text": [src("Render and read page one", "Page snapshot builder",
            "https://github.com/StrokeOfLuck/dsa405-part-2/blob/main/scripts/build_pipeline_demo.py",
            source_excerpt(builder, "with fitz.open(pdf) as document:",
                           'image.save(OUT / "images" / image_name, "WEBP", quality=76, method=6)'),
            "This webpage builder reads the same verified PDF and makes the page image and unprocessed text excerpt shown above. The Colab notebook does not display this page-level text dump.")],
        "parse": [
            src("Clip a physical PDF row into fields", "Pinned Stage 3 parser",
                source_url + "stage3_extract.py#L856-L874",
                source_excerpt(parser, "def extract_row_columns(page, row_bbox, column_boxes):", "    return output"),
                "The parser uses the row's position on the page and known column boundaries to pull text from each field. More parsing happens later in the same script."),
            nb(7, "Load Stage 3 results for audit", source_excerpt(
                code(7), 'source=Path("data/work/04_transactions/transactions_raw.csv")',
                'clean=pd.read_csv(resolved,dtype=str,keep_default_na=False)'),
                "The Colab notebook reads the parser's CSV as text so filing IDs and raw field strings retain their printed form."),
        ],
        "resolve": [
            src("Classify the candidate ticker", "Pinned Stage 4 resolver",
                source_url + "stage4_clean.py#L231-L313",
                source_excerpt(resolver, "def resolve_ticker(row):", '"ticker_parse_status": "ambiguous_preserved",\n        "ticker_validation_source": "house_ptr_structure",\n    }'),
                "This is the original ticker decision function. The status and before/after fields above come from its Stage 4 CSV, not from a simulated rule on this page."),
            nb(21, "Count resolver decisions", source_excerpt(
                code(21), "for status,count in clean.ticker_parse_status.value_counts(dropna=False).items():",
                'print("Stage 4 values changed (zero is a legitimate finding):",actual_changes)'),
                "The notebook counts each classification and compares six retained old/new value pairs."),
        ],
        "audit": [nb(21, "Create the Part 2 date flags", source_excerpt(
            code(21), "p2=clean.copy()",
            'p2["date_prefix_disagrees"]=parsed_prefix.ne("")&parsed_prefix.ne(p2.transaction_date)'),
            "These exact notebook lines make the three audit columns displayed above. They do not overwrite the original date text.")],
        "csv": [nb(21, "Write the final CSV", source_excerpt(
            code(21), 'output=Path("data/clean/house_ptr_2025_p2.csv")', 'p2.to_csv(output,index=False)'),
            "The notebook writes the full 2025 Part 2 table. The download on this page is a subset of that output containing every transaction from the selected filing.")],
    }


def main() -> None:
    raw = pd.read_csv(
        WORK / "04_transactions" / "transactions_raw.csv",
        dtype=str, keep_default_na=False,
    )
    resolved = pd.read_csv(
        WORK / "04_transactions" / "transactions_resolved.csv",
        dtype=str, keep_default_na=False,
    )
    assert len(raw) == len(resolved), "Run the full rebuild before generating the demo"
    keys = ["filing_id", "transaction_number_in_filing"]
    assert not raw.duplicated(keys).any()
    assert raw[keys].reset_index(drop=True).equals(resolved[keys].reset_index(drop=True))
    final = prepare_final(resolved)
    assert final.source_year.eq("2025").all()

    # Choose modest-size filings with visible extraction noise. Include three
    # raw-date exceptions so the audit has something meaningful to illustrate.
    # The fixed hash order makes the snapshot reproducible, not hand-picked.
    groups = raw.groupby("filing_id", sort=False)
    candidates = []
    for filing_id, group in groups:
        if not 2 <= len(group) <= 24:
            continue
        page_one = group[group.page.eq("1")]
        if page_one.empty:
            continue
        noisy = page_one[
            page_one.asset_raw.str.contains("Filing Status:|[\\n]", regex=True)
            | page_one.transaction_date_raw.str.contains(r"\s", regex=True)
        ]
        if noisy.empty:
            continue
        date_exceptions = noisy[
            noisy.transaction_date_raw.ne("")
            & ~noisy.transaction_date_raw.str.fullmatch(r"\d{1,2}/\d{1,2}/\d{4}")
        ]
        spotlight = date_exceptions.iloc[0] if not date_exceptions.empty else noisy.iloc[0]
        candidates.append((filing_id, spotlight, not date_exceptions.empty))
    assert len(candidates) >= 8, f"Only {len(candidates)} suitable filings"
    candidates.sort(key=lambda item: hashlib.sha256(("P2-tour-2025:" + item[0]).encode()).hexdigest())
    selected = []
    seen_members = set()
    for prefer_exception, goal in ((True, 3), (False, 8)):
        for candidate in candidates:
            filing_id, row, is_exception = candidate
            if prefer_exception and not is_exception:
                continue
            if not prefer_exception and is_exception:
                continue
            if row.politician in seen_members:
                continue
            selected.append((filing_id, row))
            seen_members.add(row.politician)
            if len(selected) == goal:
                break
    assert len(selected) == 8

    (OUT / "data" / "csv").mkdir(parents=True, exist_ok=True)
    (OUT / "images").mkdir(parents=True, exist_ok=True)
    # Remove obsolete generated examples from an earlier run of this script.
    for pattern, folder in (("*.csv", OUT / "data" / "csv"), ("*.webp", OUT / "images")):
        for old in folder.glob(pattern):
            old.unlink()
    examples = []
    for filing_id, spotlight in selected:
        match = raw.filing_id.eq(filing_id)
        first = raw.loc[match]
        second = resolved.loc[match]
        finished = final.loc[match]
        index = spotlight.name
        pdf = WORK / "01_pdfs" / "2025" / f"{filing_id}.pdf"
        assert pdf.exists()
        with fitz.open(pdf) as document:
            page = document[0]
            page_count = len(document)
            extracted_text = page.get_text(sort=False)
            # A rendered image is the actual first page, not reconstructed HTML.
            pix = page.get_pixmap(matrix=fitz.Matrix(1.15, 1.15), alpha=False)
            image_name = f"{filing_id}.webp"
            from PIL import Image
            import io

            image = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
            image.save(OUT / "images" / image_name, "WEBP", quality=76, method=6)
        csv_name = f"{filing_id}.csv"
        finished.to_csv(OUT / "data" / "csv" / csv_name, index=False, quoting=csv.QUOTE_MINIMAL)
        a, b, c = raw.loc[index], resolved.loc[index], final.loc[index]
        page_excerpt = extracted_text[:3300]
        examples.append({
            "filing_id": filing_id,
            "politician": a.politician,
            "state_district": a.state_district,
            "rows": len(first),
            "page_count": page_count,
            "spotlight_row": a.transaction_number_in_filing,
            "pdf_url": a.original_pdf_url,
            "pdf_image": f"images/{image_name}",
            "raw_pdf_text": page_excerpt,
            "raw_text_truncated": len(extracted_text) > len(page_excerpt),
            "stage3": text_record(a, [
                "owner_raw", "asset_raw", "asset", "ticker", "transaction_type_raw",
                "transaction_type", "transaction_date_raw", "transaction_date",
                "amount_raw", "amount_min", "amount_max", "needs_review",
                "review_reason", "page_parse_method",
            ]),
            "stage4": text_record(b, [
                "asset_v8_1", "asset_v8_2_cleaned", "ticker_v8_1",
                "ticker_v8_2_cleaned", "ticker_candidate_raw", "ticker_parse_status",
                "ticker_validation_source", "asset_changed_by_ticker_resolver",
                "ticker_changed", "needs_review",
            ]),
            "p2": {
                "raw_date_has_extra_text": bool(c.raw_date_has_extra_text),
                "raw_date_prefix": c.raw_date_prefix,
                "date_prefix_disagrees": bool(c.date_prefix_disagrees),
            },
            "csv_url": f"data/csv/{csv_name}",
            "csv_columns": len(finished.columns),
            "preview_columns": DISPLAY_FIELDS,
            "csv_preview": [text_record(row, DISPLAY_FIELDS) for _, row in finished.head(5).iterrows()],
            "changed_stage4_values": int(
                (second.asset_v8_1 != second.asset_v8_2_cleaned).sum()
                + (second.ticker_v8_1 != second.ticker_v8_2_cleaned).sum()
            ),
        })
    payload = {
        "title": "One filing, from PDF to CSV",
        "source_year": "2025",
        "source_commit": SOURCE_COMMIT,
        "batch_pdf_count": 515,
        "batch_transaction_count": len(raw),
        "sample_size": len(examples),
        "selection": "Eight reproducibly selected examples from the completed 2025 batch, including three with extra text in the raw date. Each has 2–24 trades and visible extraction noise on page one. The Random filing button chooses among these eight.",
        "code": code_examples(),
        "examples": examples,
    }
    (OUT / "data" / "examples.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    print(f"Built {len(examples)} examples from {len(raw)} trades: {[e['filing_id'] for e in examples]}")


if __name__ == "__main__":
    main()
