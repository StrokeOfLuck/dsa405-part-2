"""Copy pinned 2025 House PTR PDFs, then run the original parser in isolation."""

from __future__ import annotations

import argparse
import csv
import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_URL = "https://github.com/StrokeOfLuck/house-ptr-scraper.git"
SOURCE_COMMIT = "510945b2b1d600dd90b183858b86419926b81e65"
SOURCE = ROOT / "data" / "upstream" / "house-ptr-scraper"
RAW = ROOT / "data" / "raw"
WORK = ROOT / "data" / "work"
MANIFEST = RAW / "2025_pdf_manifest.csv"


def run(*args: str, cwd: Path | None = None, env: dict | None = None) -> None:
    subprocess.run(args, cwd=cwd, env=env, check=True)


def checkout_source(source: Path) -> None:
    if not (source / ".git").exists():
        source.parent.mkdir(parents=True, exist_ok=True)
        run("git", "clone", "--depth", "1", "--filter=blob:none", "--sparse", SOURCE_URL, str(source))
    current = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source, text=True).strip()
    if current != SOURCE_COMMIT:
        run("git", "fetch", "--depth", "1", "origin", SOURCE_COMMIT, cwd=source)
        run("git", "checkout", "--detach", SOURCE_COMMIT, cwd=source)
    run("git", "sparse-checkout", "set", "src", "data/01_pdfs/2025", "data/02_xml_indexes", cwd=source)
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source, text=True).strip() == SOURCE_COMMIT


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def copy_raw(source: Path) -> None:
    with MANIFEST.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 515 and all(row["source_commit"] == SOURCE_COMMIT for row in rows)
    raw_pdfs = RAW / "01_pdfs" / "2025"
    work_pdfs = WORK / "01_pdfs" / "2025"
    raw_pdfs.mkdir(parents=True, exist_ok=True)
    work_pdfs.mkdir(parents=True, exist_ok=True)
    for row in rows:
        original = source / "data" / "01_pdfs" / "2025" / row["filename"]
        assert original.stat().st_size == int(row["bytes"]), original
        copied = raw_pdfs / row["filename"]
        if not copied.exists() or sha256(copied) != row["sha256"]:
            shutil.copy2(original, copied)
        assert sha256(copied) == row["sha256"], copied
        working = work_pdfs / row["filename"]
        if not working.exists() or sha256(working) != row["sha256"]:
            shutil.copy2(copied, working)
    assert len(list(raw_pdfs.glob("*.pdf"))) == len(rows), "Raw PDF count differs from manifest"
    index = source / "data" / "02_xml_indexes" / "2025FD.xml"
    (RAW / "02_xml_indexes").mkdir(parents=True, exist_ok=True)
    raw_index = RAW / "02_xml_indexes" / "2025FD.xml"
    if not raw_index.exists() or sha256(raw_index) != sha256(index):
        shutil.copy2(index, raw_index)
    print(f"Verified {len(rows)} PDF copies and the 2025 XML index in {RAW}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, help="Existing checkout for testing; must be the pinned commit")
    parser.add_argument("--max-new-pdfs", type=int, help="Pilot only: parse at most N new PDFs this run")
    args = parser.parse_args()
    source = args.source_dir.resolve() if args.source_dir else SOURCE
    checkout_source(source)
    copy_raw(source)
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
