"""Validate every published example, not just the default browser selection."""
import csv
import io
import json
from datetime import datetime
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def main():
    data = json.loads((DOCS / "data/examples.json").read_text(encoding="utf-8"))
    manifest = list(csv.DictReader((ROOT / "data/raw/2025_pdf_manifest.csv").open(encoding="utf-8")))
    ids = {Path(row["filename"]).stem for row in manifest}
    assert ids == {e["filing_id"] for e in data["examples"]}
    assert len(data["examples"]) == len(ids) == data["sample_size"]
    rows = 0
    parsed = 0
    for entry in data["examples"]:
        ex = json.loads((DOCS / "data/filings" / (entry["filing_id"] + ".json")).read_text(encoding="utf-8"))
        assert ex["filing_id"] == entry["filing_id"]
        with Image.open(DOCS / ex["pdf_image"]) as img:
            img.verify()
        if ex["status"] == "no_parsed_rows":
            assert ex["rows"] == 0 and ex["geometry"] is None and "csv_url" not in ex
            continue
        parsed += 1
        with (DOCS / ex["csv_url"]).open(encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream)
            records = list(reader)
            assert len(reader.fieldnames) == ex["csv_columns"]
        assert len(records) == ex["rows"]
        assert all(row["filing_id"] == ex["filing_id"] for row in records)
        record = next(r for r in records if r["transaction_number_in_filing"] == ex["spotlight_row"])
        assert ex["csv_record"] == record
        assert next(csv.reader(io.StringIO(ex["csv_serialized_row"]))) == list(record.values())
        assert record["asset_raw"] == ex["stage3"]["asset_raw"]
        for key in ["asset_lookup_context", "asset_type", "continuation_raw", "detail_raw"]:
            assert ex["stage3"][key] == record[key]
        for key, value in ex["stage4"].items():
            assert value == record[key], (ex["filing_id"], key)
        token = ex["stage3"]["date_token"]
        try:
            normalized = datetime.strptime(token, "%m/%d/%Y").strftime("%Y-%m-%d")
        except ValueError:
            normalized = token
        assert normalized == ex["stage3"]["transaction_date"]
        assert ex["csv_preview"][0]["transaction_number_in_filing"] == ex["spotlight_row"]
        g = ex["geometry"]
        assert g["page"] == int(record["page"]) == ex["page"]
        for field in g["fields"]:
            x0, y0, x1, y1 = field["rect"]
            assert 0 <= x0 < x1 <= g["width"] + 1
            assert 0 <= y0 < y1 <= g["height"] + 1
            if field["name"] + "_raw" in ex["stage3"]:
                assert field["after"] == ex["stage3"][field["name"] + "_raw"]
        for key, value in ex["p2"].items():
            assert str(value) == record[key]
        rows += len(records)
    assert rows == data["batch_transaction_count"]
    assert parsed == data["parsed_filing_count"]
    notebook = json.loads((ROOT / "notebooks/DSA405_002_FA26_P2_sryan3.ipynb").read_text(encoding="utf-8"))
    seen = set()
    for cards in data["code"].values():
        for card in cards:
            full = card["full_code"].splitlines()
            assert full[card["focus_line"] - card["full_start_line"]] == card["focus_code"]
            if card["kind"] == "notebook":
                index = int(card["source"].split()[-1])
                assert card["full_code"] == "".join(notebook["cells"][index]["source"])
                seen.add(index)
            else:
                filename = card["url"].split("/main/")[-1].split("#")[0]
                if "Pinned Stage" in card["source"]:
                    filename = "data/upstream/house-ptr-scraper/src/" + card["url"].split("/")[-1].split("#")[0]
                lines = (ROOT / filename).read_text(encoding="utf-8").splitlines()
                start = card["full_start_line"] - 1
                assert lines[start:start + len(full)] == full, card["label"]
    assert seen == {i for i, cell in enumerate(notebook["cells"]) if cell["cell_type"] == "code" and cell["source"]}
    assert len(data["sources"]) == 10
    for source in data["sources"]:
        original = (ROOT / "data/upstream/house-ptr-scraper/src" / source["name"]
                    if "house-ptr-scraper/blob" in source["url"] else ROOT / source["url"].split("/main/")[1])
        saved = (DOCS / source["text_url"]).read_text(encoding="utf-8")
        assert saved == original.read_text(encoding="utf-8"), source["name"]
        assert len(saved.splitlines()) == source["lines"]
    print(f"PASS: {len(ids)} PDFs, {parsed} traced filings, {rows} CSV rows, all notebook cells and source lines")


if __name__ == "__main__":
    main()
