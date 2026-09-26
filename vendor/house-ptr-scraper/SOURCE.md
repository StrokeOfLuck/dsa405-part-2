# Bundled House PTR source

Copied unchanged on September 26, 2026 from Sean Ryan’s [house-ptr-scraper](https://github.com/StrokeOfLuck/house-ptr-scraper/tree/510945b2b1d600dd90b183858b86419926b81e65/src).

Original commit: `510945b2b1d600dd90b183858b86419926b81e65`.

All six Python files in `src/` are byte-for-byte copies. `SHA256.json` records their fingerprints; the P2 rebuild verifies them before execution. The original repository remains an attribution reference, not a runtime dependency. No separate license file exists at the recorded commit.

P2 runs `stage3_extract.py`, `stage4_clean.py`, and `publish_latest.py`, using `config.py` with paths redirected to P2's working directory. `stage1_download.py` and `stage2_verify.py` are included for reference to the original collection process and are not run for P2. They require the additional `requests` package if run separately and would access the live source; P2 needs neither operation.

The committed raw archive and this code snapshot are sufficient to rebuild P2 after installing the packages in the root requirements.txt. No checkout or download of the original PTR repository is required.
