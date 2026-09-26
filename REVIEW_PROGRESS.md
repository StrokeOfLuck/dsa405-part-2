# P2 review progress

Status: progress snapshot, not final submission. No Moodle submission has been made.

[Open the visual review](https://strokeofluck.github.io/dsa405-part-2/docs/review-progress.html)

## Confirmed scope

2025 filing-index year. Retain earlier transaction dates in those filings. Committee sources and joins remain for P3.

## Approved source-review decisions

### 1. Keep the transaction date

- Source: https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/2025/20024346.pdf (page 4; Transaction 27)
- Observed: Raw date: 01/13/2025 1/17/25 CLASS. Saved date: 2025-01-13.
- Approved decision: Retain January 13, 2025. The extra text came from the option description below the date.
- Preservation/reversal: No values removed. Preserve the raw text and extra-text flag.
- Status: Approved retention. Retention of existing values; formal notebook review record pending.

### 2. Keep both similar entries

- Source: https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/2025/20026517.pdf (page 1; Two Oklahoma County entries)
- Observed: Same asset, date and $1,001–$15,000 band. Descriptions list 15,000 units and 5,000 units.
- Approved decision: Retain both source entries. Their different quantities do not support deleting either as a duplicate.
- Preservation/reversal: No rows removed. Preserve the original similarity flag and document the review.
- Status: Approved retention. Retention of existing values; formal notebook review record pending.

### 3. Preserve the exact $800 amount

- Source: https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/2025/20027995.pdf (page 2; Transaction 8)
- Observed: amount_exact = 800.0; range bounds blank; status = nonstandard_exact.
- Approved decision: Retain $800 as an exact reported amount. Blank range bounds do not mean the amount is unknown.
- Preservation/reversal: No values removed. Keep the original amount text and flag.
- Status: Approved retention. Retention of existing values; formal notebook review record pending.

### 4. Restore the missed $2,000 amount

- Source: https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/2025/20033320.pdf (page 1; Transaction 1)
- Observed: Raw amount: $2,000.00. Numeric amount blank; status = missing_range_bound.
- Approved decision: Approved change: amount_exact → 2000.0; amount_status → nonstandard_exact. Keep range bounds blank.
- Preservation/reversal: Implementation must preserve the old values and flags so this single-row correction can be reversed.
- Status: Approved · application pending. Not yet applied to notebook or generated data.

These targeted cases cover five transaction rows. They do not verify the full dataset. Sean confirmed the decisions after viewing original PDF excerpts in chat.

## Approved provenance brief

This dataset contains reported transactions extracted from 515 financial-disclosure PDFs in the U.S. House Clerk’s 2025 filing archive. House members file these reports to disclose financial transactions, and the Clerk publishes them. Each dataset row represents one extracted transaction, with a link to its source PDF.

The selection uses the filing archive’s year, so some transactions occurred before 2025. Most amounts are reported as dollar ranges; some are exact amounts. The original PDFs remain unchanged, and corrections are documented so readers can trace them back to the source.

The data describes transactions reported in these archived filings. It cannot establish unreported trades, exact values when only ranges were disclosed, or who personally made an investment decision. Automated extraction can miss or misread information. Selected examples were manually reviewed; the entire dataset has not been individually verified.

## Remaining work

- [ ] Add approved review decisions to the notebook and cleaning log.
- [ ] Apply the single-row $2,000 correction with preserved prior values.
- [ ] Complete the dictionary, including exact-amount and derived audit fields.
- [ ] Reconcile row/column accounting after revisions.
- [ ] Insert the approved provenance brief.
- [ ] Run the notebook from a restarted kernel and save all outputs.
- [ ] Complete the self-scored rubric.
- [ ] Submit notebook, repository link, and rubric to Moodle.

The HTML companion is supplementary. The existing walkthrough and parser outputs have not been altered by this progress update.
