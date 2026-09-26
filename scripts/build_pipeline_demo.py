"""Build a reproducible static tour of every archived 2025 House PTR filing.

Run after scripts/rebuild_2025.py. The output is a snapshot, not a live parser.
No source PDFs or pipeline CSVs are edited.
"""

from __future__ import annotations

import csv
import io
import ast
import re
import xml.etree.ElementTree as ET
from trace_geometry import load_parser
import json
from pathlib import Path

import fitz
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "data" / "work"
OUT = ROOT / "docs"
SOURCE_COMMIT = "510945b2b1d600dd90b183858b86419926b81e65"
DISPLAY_FIELDS = [
    "filing_id", "transaction_number_in_filing", "politician", "owner", "asset_v8_2_cleaned",
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


def code_examples() -> dict[str, list[dict[str, str | int]]]:
    """Show every Colab code line, in notebook order, beside the matching data."""
    notebook = json.loads((ROOT / "notebooks" / "DSA405_002_FA26_P2_sryan3.ipynb").read_text(encoding="utf-8"))
    cells = notebook["cells"]
    code = lambda index: "".join(cells[index]["source"])
    notebook_url = "https://colab.research.google.com/github/StrokeOfLuck/dsa405-part-2/blob/main/notebooks/DSA405_002_FA26_P2_sryan3.ipynb#scrollTo="
    source_url = f"https://github.com/StrokeOfLuck/house-ptr-scraper/blob/{SOURCE_COMMIT}/src/"
    parser = (ROOT / "data/upstream/house-ptr-scraper/src/stage3_extract.py").read_text(encoding="utf-8")
    resolver = (ROOT / "data/upstream/house-ptr-scraper/src/stage4_clean.py").read_text(encoding="utf-8")
    builder = Path(__file__).read_text(encoding="utf-8")

    def nb(index: int, label: str, explanation: str, reads: str, makes: str,
           part: str | None = None, start_line: int = 1) -> dict[str, str | int]:
        return {
            "label": label, "source": f"Colab cell {index}", "kind": "notebook",
            "url": notebook_url + cells[index]["id"], "code": code(index) if part is None else part,
            "start_line": start_line, "explanation": explanation, "reads": reads, "makes": makes,
        }

    def src(label: str, source: str, url: str, excerpt: str, explanation: str,
            reads: str, makes: str) -> dict[str, str | int]:
        return {
            "label": label, "source": source, "kind": "engine", "url": url,
            "code": excerpt, "start_line": 1, "explanation": explanation,
            "reads": reads, "makes": makes,
        }

    # Copy complete function bodies with real source line numbers.
    def function_source(text, name):
        node = next(n for n in ast.parse(text).body if isinstance(n, ast.FunctionDef) and n.name == name)
        return "\n".join(text.splitlines()[node.lineno - 1:node.end_lineno]), node.lineno

    # One long Colab cell contains the Stage 3/4 decision log, P2 date checks,
    # and CSV write. Split only at its existing comment boundaries. Joining the
    # three parts must reproduce that cell byte for byte.
    long_cell = code(21)
    audit_start = long_cell.index("# Make a separate copy for our Part 2 checks")
    csv_start = long_cell.index("# Choose a new file under data/clean")
    parts = (long_cell[:audit_start], long_cell[audit_start:csv_start], long_cell[csv_start:])
    assert "".join(parts) == long_cell
    start_lines = (1, long_cell[:audit_start].count("\n") + 1,
                   long_cell[:csv_start].count("\n") + 1)

    steps = {
        "source": [nb(3, "1 · Get the project and rebuild the 2025 CSVs",
            "Colab first finds or clones this Part 2 repository, installs packages, and runs the rebuild script. The script verifies the committed raw PDFs against the manifest, copies them into data/work/, then fetches only the pinned scraper code needed to parse them.",
            "GitHub repo + data/raw/2025_pdfs/ + manifest",
            "data/work/01_pdfs/2025/*.pdf → transactions_raw.csv → transactions_resolved.csv")],
        "text": [src("How this page renders and reads the PDF", "Webpage snapshot builder",
            "https://github.com/StrokeOfLuck/dsa405-part-2/blob/main/scripts/build_pipeline_demo.py",
            function_source(builder, "main")[0],
            "This is the webpage's own visual aid, not a Colab cell. It reads the verified PDF to show its page image and messy text; the actual transaction parser uses page geometry.",
            "Verified PDF", "Selected-page image + page-level text excerpt")],
        "parse": [
            src("Under the hood · clip PDF columns", "Pinned Stage 3 parser",
                source_url + "stage3_extract.py#L856-L874",
                source_excerpt(parser, "def extract_row_columns(page, row_bbox, column_boxes):", "    return output"),
                "The rebuild script calls this parser. It uses a row's position and column boundaries to capture field text; the whole parser is linked.",
                "PDF page + row coordinates", "Source-like field text"),
            nb(7, "2 · Load both transaction CSVs",
                "The notebook reads the first parser CSV as raw and the ticker-resolved CSV as clean. Text loading preserves printed filing IDs and blank strings.",
                "transactions_raw.csv + transactions_resolved.csv", "raw and clean tables"),
            nb(10, "3 · Count and name the columns",
                "The inventory checks required fields and counts missing and distinct values.",
                "raw table", "audit table for 19 selected fields"),
            nb(12, "4 · Inspect categories, amounts, and dates",
                "These loops print category frequencies and check numeric and date ranges without changing the original text.",
                "raw table", "Printed ranges and unparsed-value counts"),
            nb(14, "5 · Check duplicates and extraction problems",
                "The notebook checks repeated rows, placeholder values, and raw date text that fails strict parsing. Some filings have extra date text; others do not.",
                "raw table", "checks table + bad_date examples"),
            nb(18, "6 · Explain every field",
                "The dictionary records intended types, expected values, missing counts, and field cautions.",
                "raw table + audit field list", "dictionary table"),
        ],
        "resolve": [
            src("Under the hood · classify ticker candidates", "Pinned Stage 4 resolver",
                source_url + "stage4_clean.py#L231-L313",
                source_excerpt(resolver, "def resolve_ticker(row):",
                               '"ticker_parse_status": "ambiguous_preserved",\n        "ticker_validation_source": "house_ptr_structure",\n    }'),
                "The rebuild script calls this resolver. It classifies candidates while retaining older asset and ticker fields for comparison.",
                "Stage 3 asset and ticker", "Stage 4 value + ticker_parse_status"),
            nb(21, "7 · Log Stage 3 and Stage 4 decisions",
                "This is the first part of one long Colab cell. It checks row alignment, records parsing decisions, and counts actual Stage 4 value changes.",
                "raw and clean tables", "changes log + actual_changes counts",
                part=parts[0], start_line=start_lines[0]),
        ],
        "audit": [nb(21, "8 · Add the Part 2 date checks",
            "The next part of the same Colab cell copies clean, checks the original date text, and logs three audit fields without overwriting source values.",
            "clean table + transaction_date_raw", "p2 table + three date audit fields",
            part=parts[1], start_line=start_lines[1])],
        "csv": [
            nb(21, "9 · Save and display the cleaned table",
                "The final part of that Colab cell writes the entire 2025 P2 CSV. This page offers a separate download filtered to the selected filing.",
                "p2 table + changes log", "data/clean/house_ptr_2025_p2.csv",
                part=parts[2], start_line=start_lines[2]),
            nb(26, "10 · Reconcile rows and columns",
                "The last code cell confirms that no transaction rows were removed and accounts for renamed and new fields.",
                "raw and p2 tables", "accounting table + output paths"),
        ],
    }
    # Guard against accidentally hiding even one line of the Colab notebook.
    assert {3, 7, 10, 12, 14, 18, 21, 26} == {
        int(item["source"].split()[-1]) for group in steps.values()
        for item in group if item["kind"] == "notebook"
    }
    rebuild = (ROOT / "scripts/rebuild_2025.py").read_text(encoding="utf-8")
    for name, label, explanation in [
        ("prepare_working_copy", "Verify raw data and make working copies", "Check each committed raw PDF's SHA-256 against the manifest, then copy the verified bytes into data/work/ for parsing."),
        ("main", "Run Stage 3, Stage 4, then publish", "The rebuild runs each Python stage in order. The Colab notebook later reads their saved CSVs.")]:
        body, line = function_source(rebuild, name)
        card = src(label, "Project rebuild script", "https://github.com/StrokeOfLuck/dsa405-part-2/blob/main/scripts/rebuild_2025.py", body, explanation, "Committed data/raw snapshot + manifest", "Verified working copies + transaction CSVs")
        card["start_line"] = line
        steps["source"].append(card)
    for name, label, explanation in [
        ("table_row_items", "Read physical table rows", "Turn detected table rows into bounding boxes and clipped column text."),
        ("date_anchor_items", "Recover rows from paired dates", "When normal table detection is insufficient, use paired date positions to build row regions."),
        ("clean_space", "Normalize whitespace after character repair", "Repair encoded characters, collapse repeated whitespace, and trim the result."),
        ("parse_pdf_geometry_v8", "Choose rows and build transactions", "Find tables or paired dates, separate new transactions from continuations, then normalize fields. This is the complete parser function."),
        ("clip_text", "Read and normalize one rectangle", "Read embedded PDF text inside the rectangle and pass it through whitespace and character cleanup."),
        ("normalize_house_pdf_text", "Repair the House PDF character encoding", "Map the known encoded characters back to readable characters before interpreting values.")]:
        body, line = function_source(parser, name)
        card = src(label, "Pinned Stage 3 parser", source_url + f"stage3_extract.py#L{line}", body, explanation, "PDF geometry / text", "Transaction fields")
        card["start_line"] = line
        steps["text"].append(card)
    rules = [
        ("asset", "Clean asset name", "parse_pdf_geometry_v8", 'asset = ASSET_TYPE_RE.sub', "Separate filing details, remove the asset-type marker and accepted ticker, then trim whitespace. The complete function also shows the description fallback and owner cleanup.", ["asset_raw", "ticker", "detail_raw"], ["asset"]),
        ("ticker", "Extract ticker", "extract_ticker_from_context", "def extract_ticker_from_context", "Look for ticker candidates in the asset context and apply the Stage 3 validation rules. This precedes the Stage 4 ticker review.", ["asset_lookup_context", "asset_type"], ["ticker"]),
        ("transaction_type", "Parse trade type", "extract_core_values", "transaction_type = type_match.group(1).upper()", "Use the transaction-code pattern to extract the type, including a partial/full qualifier when present.", ["transaction_type_raw"], ["transaction_type"]),
        ("transaction_date", "Extract date token", "extract_core_values", "transaction_dates = DATE_RE.findall", "Find the first date token in the clipped column text before converting its format. The next date button shows that conversion.", ["transaction_date_raw"], ["date_token"]),
        ("transaction_date", "Normalize trade date", "to_iso_date", "return datetime.strptime", "Convert the extracted date token to YYYY-MM-DD. Use Extract date token to see how that token was selected from the original text.", ["date_token"], ["transaction_date"]),
        ("amount_min", "Parse amount range", "parse_amount_text", "def parse_amount_text", "Parse the disclosed amount, including continuation text when needed, into numeric bounds and an amount classification.", ["amount_raw", "continuation_raw"], ["amount_min", "amount_max"]),
        ("needs_review", "Check review reasons", "parse_pdf_geometry_v8", "reasons = []", "Collect validation issues after parsing, then set the review flag from that list. Scroll through this section for the individual checks.", ["asset", "ticker", "transaction_date", "amount_raw"], ["needs_review", "review_reason"]),
    ]
    parsed_cards = []
    for field, label, name, token, explanation, inputs, outputs in rules:
        body, line = function_source(parser, name)
        card = src(label, "Pinned Stage 3 parser", source_url + f"stage3_extract.py#L{line}", body, explanation, ", ".join(inputs), ", ".join(outputs))
        card.update(start_line=line, parsed_field=field, input_keys=inputs, output_keys=outputs, focus_token=token)
        parsed_cards.append(card)
    pattern_node = next(node for node in ast.parse(parser).body if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "TXN_RE" for target in node.targets))
    pattern_code = "\n".join(parser.splitlines()[pattern_node.lineno-1:pattern_node.end_lineno])
    pattern_card = src("Show trade matching pattern", "Pinned Stage 3 parser", source_url + f"stage3_extract.py#L{pattern_node.lineno}", pattern_code, "Match a standalone P, S, or E, optionally followed by (partial) or (full). Text outside the match is not included in the parsed trade type.", "transaction_type_raw", "Matched trade token")
    pattern_card.update(start_line=pattern_node.lineno, parsed_field="transaction_type", input_keys=["transaction_type_raw"], output_keys=["transaction_type"], focus_token='r"(?<!')
    parsed_cards.append(pattern_card)
    steps["parse"] = parsed_cards + steps["parse"]
    resolve_rules = [
        ("decision", "Explain ticker decision", "resolve_ticker", "def resolve_ticker", "Classify the candidate using asset type, the earlier ticker, source structure, and any reference match. The values below include the recorded validation source.", ["stage3.asset_type", "stage4.ticker_v8_1", "stage4.ticker_candidate_raw"], ["stage4.ticker_parse_status", "stage4.ticker_validation_source"]),
        ("candidate", "Explain candidate", "resolve_ticker", "candidate = extract_ticker_candidate", "A candidate is a proposed ticker found in source text. Non-stock assets skip candidate extraction. Use Find candidate in source text to inspect the helper used for stocks.", ["stage3.asset_type", "stage3.asset_lookup_context", "stage3.asset_raw", "stage3.asset"], ["stage4.ticker_candidate_raw", "stage4.ticker_parse_status"]),
        ("ticker", "Explain final ticker", "resolve_ticker", "def resolve_ticker", "The resolver returns the ticker used in Stage 4. Compare the preserved earlier ticker, proposed candidate, and final ticker below.", ["stage3.asset_type", "stage4.ticker_v8_1", "stage4.ticker_candidate_raw"], ["stage4.ticker_v8_2_cleaned", "stage4.ticker_parse_status", "stage4.ticker_validation_source"]),
        ("asset", "Explain asset cleanup", "remove_resolved_ticker_from_asset", "if not asset or not ticker:", "Remove the accepted ticker parenthetical from the presentation asset name. If asset or ticker is empty, return the asset unchanged. Source evidence remains preserved.", ["stage4.asset_v8_1", "stage4.ticker_v8_2_cleaned"], ["stage4.asset_v8_2_cleaned", "stage4.asset_changed_by_ticker_resolver"]),
        ("review", "Explain review flag", "rebuild_review_fields", "if not reasons:", "Update ticker-related warnings while retaining unrelated reasons. Any remaining reason sets needs_review to true; a flag requests review and does not itself prove an error.", ["stage4.review_reason_v8_1", "stage3.asset_type", "stage4.ticker_v8_2_cleaned", "stage4.ticker_parse_status"], ["stage4.review_reason", "stage4.review_level", "stage4.needs_review"]),
    ]
    resolve_cards = []
    for field, label, name, token, explanation, inputs, outputs in resolve_rules:
        body, line = function_source(resolver, name)
        card = src(label, "Pinned Stage 4 resolver", source_url + f"stage4_clean.py#L{line}", body, explanation, ", ".join(inputs), ", ".join(outputs))
        card.update(start_line=line, resolve_field=field, input_keys=inputs, output_keys=outputs, focus_token=token)
        resolve_cards.append(card)
    body, line = function_source(resolver, "extract_ticker_candidate")
    card = src("Find candidate in source text", "Pinned Stage 4 resolver", source_url + f"stage4_clean.py#L{line}", body, "For stock assets, search the preserved asset evidence in priority order and take the last compact parenthetical before [ST]. This helper is skipped for non-stock assets; its code is available here to study.", "Preserved asset evidence", "Proposed ticker")
    card.update(start_line=line, focus_token="candidates = symbol_like_parentheticals")
    steps["resolve"] = resolve_cards + [card] + steps["resolve"]
    audit_cards = []
    for key, label, token, explanation in [
        ("raw_date_has_extra_text", "Check the whole date field", 'p2["raw_date_has_extra_text"]', "fullmatch checks the entire string against a date-shaped pattern. Extra text, a blank, or a different format fails this pattern. This is not a calendar-validity check."),
        ("raw_date_prefix", "Extract the leading date", 'p2["raw_date_prefix"]', "The ^ anchor searches only at the beginning. It keeps a date-shaped prefix even if text follows. No prefix becomes an empty string."),
        ("date_prefix_disagrees", "Compare dates", 'p2["date_prefix_disagrees"]', "Convert the prefix to YYYY-MM-DD, then compare with the parser date. Invalid or missing prefixes become empty; those do not trigger this disagreement flag. No flag is not proof of a valid date."),
    ]:
        card = dict(steps["audit"][0])
        card.update(label=label, audit_field=key, focus_token=token, explanation=explanation)
        audit_cards.append(card)
    steps["audit"] = audit_cards + steps["audit"]
    csv_cards = []
    for key, label, explanation in [
        ("field", "Inspect a CSV field", "Follow a saved value into its CSV column. CSV stores text; commas, quotes, and line breaks inside a value require quoting. Click a preview cell or choose any column."),
        ("row", "See the serialized row", "The writer serializes all columns in order into one CSV record. Values containing line breaks can span physical lines. The preview below shows the complete transaction followed on this page."),
        ("index", "Why index=False?", "index=False omits pandas' extra row index. It does not remove real columns such as filing_id or transaction_number_in_filing. The notebook writes the whole-year table; this page downloads the selected filing."),
    ]:
        card = dict(steps["csv"][0])
        card.update(label=label, csv_action=key, focus_token="p2.to_csv", explanation=explanation)
        csv_cards.append(card)
    steps["csv"] = csv_cards + steps["csv"]
    # Student guide links plain-language lessons to unchanged original source.
    source_lessons = [
        ("Find the project", None, 'if not Path("scripts/rebuild_2025.py").exists()',
         "Find the folder containing this project's code. If it is missing, download a copy from GitHub.",
         "Opening a notebook does not guarantee that its supporting scripts are on the computer. We need those files before Python can run them.",
         "A notebook session", "The project folder is available",
         "Path describes a file location. exists() asks whether it is there. if runs the indented instructions only when its condition is true."),
        ("Prepare Python", None, 'subprocess.run([sys.executable,"-m","pip"',
         "When running in Colab, install the Python packages listed in requirements.txt.",
         "The parser uses tools for PDFs and tables that Python does not include by itself. This gives the notebook those tools.",
         "requirements.txt — the package list", "Required Python packages installed in Colab",
         "subprocess.run starts another command. sys.executable selects this session's Python. pip install installs packages. check=True stops if the command fails. Outside Colab, this block is skipped."),
        ("Run the PDF-to-CSV pipeline", None, 'result=subprocess.run',
         "Ask Python to run scripts/rebuild_2025.py. That script coordinates the archive checks and parser stages.",
         "Run this when you want to reproduce the transaction CSVs from the archived PDFs. The webpage already has saved results. The next lessons explain the script this command starts; the notebook adds its class audit and final CSV afterward.",
         "Project code and Python tools", "The PDF-to-CSV process and its log messages",
         "The list contains the program and script to run. stdout=log sends normal messages to the log file; stderr=STDOUT sends errors there too. This line launches the work; it does not itself read transaction fields."),
        ("Choose a fixed archive", "checkout_source", 'if current != SOURCE_COMMIT:',
         "Get the scraper code and select its recorded Git version. The 2025 PDFs are already preserved separately in this repository's data/raw/ folder.",
         "A fixed parser version keeps the extraction code reproducible, while the committed data/raw/ snapshot keeps the source documents fixed separately.",
         "Parser repository and SOURCE_COMMIT", "The recorded parser code",
         "A commit is a saved Git version. SOURCE_COMMIT identifies the version this project expects. The code checks the current version and switches if needed."),
        ("Verify raw PDFs and make working copies", "prepare_working_copy", 'assert original_hash == row["sha256"]',
         "Verify each PDF already committed in data/raw/ against the manifest, then copy the verified bytes into data/work/ so the parser never writes to the raw source folder.",
         "This checks that the parser gets the expected file bytes. It does not prove the disclosure is accurate or that parsing will succeed.",
         "515 committed raw PDFs and a manifest (file checklist)", "Verified working PDF copies",
         "sha256 computes a file fingerprint. The first assert proves the committed raw PDF matches the recorded fingerprint; only then is that file copied into data/work/."),
        ("Run the parser stages", "main", 'for stage in (',
         "Run Stage 3 to extract transactions, Stage 4 to review tickers, then publish the parser's output files locally.",
         "Each stage uses the previous stage's results. Later notebook cells load these CSVs, add the class audit, and write the final Part 2 CSV.",
         "Verified PDFs and archived parser code", "Raw and resolved transaction CSVs",
         "for repeats the indented command for each script name, in order. Here publish_latest.py prepares local output files; it is not publishing this website. Walkthrough tabs 02–04 unpack the parsing work."),
        ("Check that it finished", None, 'if result.returncode:',
         "Check the rebuild's exit code and stop the notebook if the rebuild failed. Read rebuild.log to find the cause.",
         "Continuing after an error could make later cells use old or incomplete CSVs. Stopping makes the failure visible.",
         "The rebuild's return code and log", "Continue on success, or an error explaining where to look",
         "returncode is the command's result: 0 means success. A nonzero value makes this if run. raise RuntimeError stops the cell with an error message."),
    ]
    guided_cards = []
    for index, (label, name, token, what, why, reads, makes, translation) in enumerate(source_lessons, 1):
        if name is None:
            card = nb(3, f"{index}. {label}", what, reads, makes)
        else:
            body, line = function_source(rebuild, name)
            card = src(f"{index}. {label}", "Project rebuild script", "https://github.com/StrokeOfLuck/dsa405-part-2/blob/main/scripts/rebuild_2025.py", body, what, reads, makes)
            card["start_line"] = line
        card.update(focus_token=token, source_guide=dict(what=what, why=why, translation=translation))
        guided_cards.append(card)
    steps["source"] = guided_cards
    for filename, label, token, what, why in [
        ("stage1_download.py", "Original Stage 1: download PDFs", "pdf_path.write_bytes", "Read the House filing index, select PTR entries, and download their PDF files.", "This is the original live collection step. Project 2 does not run it: it retrieves the already archived 2025 PDFs from the recorded Git version."),
        ("stage2_verify.py", "Original Stage 2: verify coverage", "missing_docids =", "Compare expected filing IDs from the House index with local PDF filenames. Include parser checkpoint status when available.", "This checks collection coverage. Project 2 does not run this live verification script; it checks its fixed PDF copies against the manifest instead. File fingerprints do not establish coverage of today's live index."),
    ]:
        text = (ROOT / "data/upstream/house-ptr-scraper/src" / filename).read_text(encoding="utf-8")
        body, line = function_source(text, "run")
        card = src(label, "Pinned Stage 1/2 archive scripts", source_url + filename + f"#L{line}", body, what, "House filing index and archive files", "Downloaded PDFs" if filename.startswith("stage1") else "Coverage and verification reports")
        card.update(start_line=line, focus_token=token, workflow_only=True, source_guide=dict(what=what, why=why, translation="This is original scraper code, shown for context. The Project 2 rebuild skips this script and reuses the fixed archive."))
        steps["source"].append(card)
    for group in steps.values():
        for item in group:
            if item["kind"] == "notebook":
                cell_index = int(item["source"].split()[-1])
                item["full_code"] = code(cell_index)
                item["full_start_line"] = 1
            else:
                item["full_code"] = item["code"]
                item["full_start_line"] = item["start_line"]
                for text in [parser, resolver, builder]:
                    if item["code"] in text:
                        item["start_line"] = text[:text.index(item["code"])].count("\n") + 1
                        item["full_start_line"] = item["start_line"]
                        break
            lines = item["code"].splitlines()
            preferred = ["to_csv(", "fitz.Rect(", "output[name]", "raw = pd.read_csv", "p2 = clean.copy", "for page_number", "sha256(working)", "run(sys.executable", "return clean_space", "ticker_candidate", "raw_date_has_extra_text"]
            if item["source"] == "Webpage snapshot builder":
                preferred = ["page.get_pixmap"]
            elif item["label"] == "Choose rows and build transactions":
                preferred = ["primary_table = find_ptr_table"]
            elif item["label"] == "Repair the House PDF character encoding":
                preferred = ["chr(code -"]
            elif item["source"] == "Colab cell 3":
                preferred = ["result=subprocess.run"]
            elif item["source"] == "Colab cell 7":
                preferred = ["raw=pd.read_csv"]
            if "focus_token" in item:
                preferred = [item["focus_token"]]
            chosen = next((i for token in preferred for i, line in enumerate(lines) if token in line), next((i for i, line in enumerate(lines) if line.strip() and not line.lstrip().startswith("#")), 0))
            item["focus_line"] = item["start_line"] + chosen
            item["focus_code"] = lines[chosen]
    return steps


def enrich_fallback(examples):
    """Use the official XML index for scanned filings with no readable name."""
    members = {m.findtext("DocID"): m for m in ET.parse(WORK / "02_xml_indexes/2025FD.xml").getroot()}
    fallback = pd.read_csv(WORK / "04_transactions/needs_fallback.csv", dtype=str, keep_default_na=False)
    reasons = dict(zip(fallback.filing_id, fallback.review_reason))
    for example in examples:
        if example["status"] != "no_parsed_rows":
            with (OUT / example["csv_url"]).open(encoding="utf-8", newline="") as stream:
                rows = list(csv.DictReader(stream))
            record = next(row for row in rows if row["transaction_number_in_filing"] == example["spotlight_row"])
            parser_text = (ROOT / "data/upstream/house-ptr-scraper/src/stage3_extract.py").read_text(encoding="utf-8")
            txn_node = next(node for node in ast.parse(parser_text).body if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "TXN_RE" for target in node.targets))
            pattern = re.compile(ast.literal_eval(txn_node.value.args[0]), re.I)
            raw_type = example["stage3"]["transaction_type_raw"]
            match = pattern.search(raw_type)
            parsed_type = (match.group(1).upper() + (" (" + match.group(2).lower() + ")" if match.group(2) else "")) if match else ""
            assert parsed_type == example["stage3"]["transaction_type"]
            example["trade_match"] = {"matched": match.group(0) if match else "", "before": raw_type[:match.start()] if match else raw_type, "after": raw_type[match.end():] if match else "", "result": parsed_type}
            example["csv_record"] = record
            buffer = io.StringIO(newline="")
            writer = csv.writer(buffer, lineterminator="\n")
            writer.writerow(record.values())
            example["csv_serialized_row"] = buffer.getvalue()
            tokens = re.findall(r"\d{1,2}/\d{1,2}/\d{4}", example["stage3"]["transaction_date_raw"])
            example["stage3"]["date_token"] = tokens[0] if tokens else ""
            continue
        member = members.get(example["filing_id"])
        if member is not None:
            example["politician"] = " ".join(member.findtext(key) or "" for key in ("Prefix", "First", "Last", "Suffix")).strip()
            example["state_district"] = member.findtext("StateDst") or ""
            example["metadata_source"] = "Official 2025 filing XML index"
        example["fallback_reason"] = reasons.get(example["filing_id"], "No transaction rows returned")
        example["status_note"] = "This archived PDF produced no transaction rows. Parser reason: " + example["fallback_reason"] + ". Inspect the original PDF; no transaction CSV is available for this filing."


def source_catalog():
    """Publish complete project/engine source files, including helper functions."""
    folder = OUT / "data/source"
    folder.mkdir(parents=True, exist_ok=True)
    entries = []
    upstream = ROOT / "data/upstream/house-ptr-scraper/src"
    files = [(ROOT / "scripts/rebuild_2025.py", "1 · Verify raw data and run the pinned parser"),
             (upstream / "stage1_download.py", "Original scraper Stage 1 · Historical downloader (not used for P2 raw input)"),
             (upstream / "stage2_verify.py", "Original scraper Stage 2 · Historical coverage check (not used for P2 raw input)"),
             (upstream / "config.py", "1 · Parser paths and configuration"),
             (upstream / "stage3_extract.py", "2–3 · Complete geometry parser and CSV writer"),
             (upstream / "stage4_clean.py", "4 · Complete ticker resolver and CSV writer"),
             (upstream / "publish_latest.py", "4 · Publish the scraper's output tables"),
             (ROOT / "scripts/build_pipeline_demo.py", "Webpage · Build the saved examples"),
             (ROOT / "scripts/trace_geometry.py", "Webpage · Observe PDF coordinates"),
             (ROOT / "docs/walkthrough.js", "Webpage · Interactive controls and rendering")]
    for path, label in files:
        text = path.read_text(encoding="utf-8")
        (folder / path.name).write_text(text, encoding="utf-8")
        url = (f"https://github.com/StrokeOfLuck/house-ptr-scraper/blob/{SOURCE_COMMIT}/src/{path.name}"
               if path.parent == upstream else "https://github.com/StrokeOfLuck/dsa405-part-2/blob/main/" + path.relative_to(ROOT).as_posix())
        entries.append({"name": path.name, "label": label, "url": url,
                        "text_url": "data/source/" + path.name, "lines": len(text.splitlines())})
    return entries


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

    manifest = list(csv.DictReader((ROOT / "data/raw/2025_pdf_manifest.csv").open(encoding="utf-8")))
    selected = []
    for entry in manifest:
        filing_id = Path(entry["filename"]).stem
        group = raw[raw.filing_id.eq(filing_id)]
        if group.empty:
            selected.append((filing_id, None))
        else:
            noisy = group[~group.transaction_date_raw.str.fullmatch(r"\d{1,2}/\d{1,2}/\d{4}")]
            selected.append((filing_id, noisy.iloc[0] if not noisy.empty else group.iloc[0]))
    trace = load_parser(ROOT)
    (OUT / "data/filings").mkdir(parents=True, exist_ok=True)
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
        index = spotlight.name if spotlight is not None else None
        pdf = WORK / "01_pdfs" / "2025" / f"{filing_id}.pdf"
        assert pdf.exists()
        parsed, metadata, traces = trace(pdf)
        assert len(parsed) == len(first), (filing_id, len(parsed), len(first))
        geometry = None
        if spotlight is not None:
            row_number = int(spotlight.transaction_number_in_filing) - 1
            actual = parsed.iloc[row_number]
            for field in ["asset_raw", "owner_raw", "transaction_type_raw", "transaction_date_raw", "amount_raw", "page_parse_method"]:
                assert str(actual[field]) == str(spotlight[field]), (filing_id, field)
            geometry = traces[row_number]
        with fitz.open(pdf) as document:
            page = document[geometry["page"] - 1 if geometry else 0]
            page_count = len(document)
            extracted_text = page.get_text(sort=False)
            # Render the actual page containing the observed transaction.
            pix = page.get_pixmap(matrix=fitz.Matrix(1.15, 1.15), alpha=False)
            image_name = f"{filing_id}.webp"
            from PIL import Image
            import io

            image = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
            image.save(OUT / "images" / image_name, "WEBP", quality=76, method=6)
        if spotlight is None:
            examples.append({
                "filing_id": filing_id, "politician": metadata["politician"] or "Member name unavailable",
                "state_district": metadata["state_district"], "rows": 0,
                "page_count": page_count, "page": 1, "spotlight_row": None,
                "pdf_url": f"https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/2025/{filing_id}.pdf",
                "pdf_image": f"images/{image_name}", "geometry": None,
                "raw_pdf_text": extracted_text[:3300], "raw_text_truncated": len(extracted_text) > 3300,
                "status": "no_parsed_rows",
                "status_note": "This archived PDF produced no transaction rows in this run. Inspect the original PDF; this does not establish that it contains no transactions. No transaction CSV is available for this filing.",
            })
            continue
        csv_name = f"{filing_id}.csv"
        finished.to_csv(OUT / "data" / "csv" / csv_name, index=False, quoting=csv.QUOTE_MINIMAL)
        a, b, c = raw.loc[index], resolved.loc[index], final.loc[index]
        page_excerpt = extracted_text[:3300]
        examples.append({
            "filing_id": filing_id,
            "status": "parsed", "geometry": geometry, "page": geometry["page"],
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
                "asset_lookup_context", "asset_type", "continuation_raw", "detail_raw",
            ]),
            "stage4": text_record(b, [
                "asset_v8_1", "asset_v8_2_cleaned", "ticker_v8_1",
                "ticker_v8_2_cleaned", "ticker_candidate_raw", "ticker_parse_status",
                "ticker_validation_source", "asset_changed_by_ticker_resolver",
                "ticker_changed", "needs_review", "review_reason_v8_1", "review_reason", "review_level",
            ]),
            "p2": {
                "raw_date_has_extra_text": bool(c.raw_date_has_extra_text),
                "raw_date_prefix": c.raw_date_prefix,
                "date_prefix_disagrees": bool(c.date_prefix_disagrees),
            },
            "csv_url": f"data/csv/{csv_name}",
            "csv_columns": len(finished.columns),
            "preview_columns": DISPLAY_FIELDS,
            "csv_preview": [text_record(row, DISPLAY_FIELDS) for _, row in pd.concat([finished.loc[[index]], finished.drop(index).head(4)]).iterrows()],
            "changed_stage4_values": int(
                (second.asset_v8_1 != second.asset_v8_2_cleaned).sum()
                + (second.ticker_v8_1 != second.ticker_v8_2_cleaned).sum()
            ),
        })
    enrich_fallback(examples)
    payload = {
        "title": "One filing, from PDF to CSV",
        "source_year": "2025",
        "source_commit": SOURCE_COMMIT,
        "pymupdf_version": fitz.VersionBind,
        "batch_pdf_count": 515,
        "batch_transaction_count": len(raw),
        "sample_size": len(examples),
        "selection": "Random selection uses only filings with parsed transactions. Filings without parsed rows remain in the archive and audit counts but are excluded from the picker. Each selected filing follows one observed transaction through the saved pipeline.",
        "code": code_examples(),
        "sources": source_catalog(),
        "parsed_filing_count": sum(e["rows"] > 0 for e in examples),
        "examples": [{key: e[key] for key in ("filing_id", "politician", "rows", "status")} for e in examples],
    }
    for example in examples:
        (OUT / "data/filings" / (example["filing_id"] + ".json")).write_text(
            json.dumps(example, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "data" / "examples.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Built {len(examples)} examples from {len(raw)} trades: {[e['filing_id'] for e in examples]}")


if __name__ == "__main__":
    main()
