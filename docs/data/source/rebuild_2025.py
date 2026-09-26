"""Verify committed raw 2025 House PTR files, copy them to work/, and run the pinned parser."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_COMMIT = "510945b2b1d600dd90b183858b86419926b81e65"
SOURCE = ROOT / "vendor" / "house-ptr-scraper"
RAW = ROOT / "data" / "raw"
WORK = ROOT / "data" / "work"
MANIFEST = RAW / "2025_pdf_manifest.csv"


def run(*args: str, cwd: Path | None = None, env: dict | None = None) -> None:
    subprocess.run(args, cwd=cwd, env=env, check=True)


def verify_parser(source: Path) -> None:
    """Verify the bundled code; no Git checkout or network access is needed."""
    manifest = json.loads((SOURCE / "SHA256.json").read_text(encoding="utf-8"))
    for name, expected in manifest.items():
        path = source / "src" / name
        if not path.is_file() or sha256(path) != expected:
            raise ValueError(f"Bundled parser hash mismatch: {path}")
    print(f"Verified {len(manifest)} bundled parser files from {SOURCE_COMMIT}", flush=True)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def prepare_working_copy() -> None:
    with MANIFEST.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 515 and all(row["source_commit"] == SOURCE_COMMIT for row in rows)
    work_pdfs = WORK / "01_pdfs" / "2025"
    work_pdfs.mkdir(parents=True, exist_ok=True)
    for row in rows:
        original = RAW / "2025_pdfs" / row["filename"]
        assert original.stat().st_size == int(row["bytes"]), original
        original_hash = sha256(original)
        assert original_hash == row["sha256"], f"Raw PDF hash mismatch: {original}"
        working = work_pdfs / row["filename"]
        if not working.exists() or sha256(working) != original_hash:
            shutil.copy2(original, working)
        assert sha256(working) == original_hash, working
    assert len(list(work_pdfs.glob("*.pdf"))) == len(rows), "PDF count differs from manifest"
    index = RAW / "2025FD.xml"
    (WORK / "02_xml_indexes").mkdir(parents=True, exist_ok=True)
    copied_index = WORK / "02_xml_indexes" / "2025FD.xml"
    if not copied_index.exists() or sha256(copied_index) != sha256(index):
        shutil.copy2(index, copied_index)
    print(f"Verified {len(rows)} PDF copies and the 2025 XML index in {WORK}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, help="Optional local source directory; files must match the bundled manifest")
    parser.add_argument("--max-new-pdfs", type=int, help="Pilot only: parse at most N new PDFs this run")
    args = parser.parse_args()
    source = args.source_dir.resolve() if args.source_dir else SOURCE
    verify_parser(source)
    prepare_working_copy()
    env = os.environ.copy()
    env.update(HOUSE_PTR_ROOT=str(WORK), HOUSE_PTR_START_YEAR="2025", HOUSE_PTR_END_YEAR="2025")
    if args.max_new_pdfs:
        env["HOUSE_PTR_MAX_NEW_PDFS"] = str(args.max_new_pdfs)
    else:
        env.pop("HOUSE_PTR_MAX_NEW_PDFS", None)
    for stage in ("stage3_extract.py", "stage4_clean.py", "publish_latest.py"):
        print(f"Running {stage} on the P2 copy", flush=True)
        run(sys.executable, str(source / "src" / stage), cwd=ROOT, env=env)
    print("P2 outputs:", WORK / "04_transactions" / "transactions_raw.csv", WORK / "04_transactions" / "transactions_resolved.csv", flush=True)


if __name__ == "__main__":
    main()
