"""Build a review view from existing parser flags and recorded human decisions."""
import csv
import html
import json

FLAG_GUIDANCE = {
    'adjacent transaction has same core signature': (
        'A neighboring transaction looks very similar',
        'The parser found adjacent entries with matching owner, asset text, trade type, transaction date, notification date and extracted amount values. They appeared in different PDF locations, so it kept them separate and asked for review.',
        'Compare both entries in the PDF, including descriptions and quantities. Matching dates and dollar bands alone do not prove duplication. Keep separate trades; remove a row only if the source confirms an extraction duplicate.'),
    'notification date before transaction date': (
        'The notification date is earlier than the trade date',
        'The extracted dates appear in an unexpected order. This could come from a source entry or from reading the wrong text or column.',
        'Compare both date cells with the PDF. Correct an extraction mistake only when the source supports it. If the PDF itself shows that order, preserve it and document the discrepancy.'),
    'implausible notification date year': (
        'The notification year falls outside the parser’s expected window',
        'The year is earlier than 2012 or more than one year after the filing-index year. For this 2025 archive, that means earlier than 2012 or later than 2026. This is a checking rule, not proof that the date is wrong.',
        'Read the year in the PDF and compare it with the extracted notification date. Check for a misread digit or misplaced text before changing anything.'),
    'nonstandard_exact': (
        'The form reports an exact amount instead of a usual dollar band',
        'The parser found a single dollar amount. It flags this unusual format even when the amount was extracted correctly.',
        'Confirm the exact amount in the PDF. If it matches, retain it as an exact value and leave range bounds blank. Do not invent a dollar band.'),
    'missing_range_bound': (
        'The amount could not be interpreted as a complete range',
        'The original parser could not supply both range endpoints. The form may show an exact amount, an incomplete range, or text the parser misread.',
        'Read the amount cell in the PDF. Record an exact amount only if it is explicitly shown; restore range endpoints only when supported. Otherwise leave the uncertainty documented.')
}

def flag_guidance(row):
    reasons=[reason.strip() for reason in row['review_reason'].split(';') if reason.strip()]
    if not reasons:
        return '<p><strong>Why this row is included:</strong> This was an additional source check or a companion row in a reviewed pair. The original parser did not flag this row.</p>'
    blocks=[]
    for reason in reasons:
        title,meaning,check=FLAG_GUIDANCE.get(reason,('Parser review requested',reason,'Compare the extracted fields with the linked source PDF before deciding whether to keep or correct them.'))
        blocks.append('<div class="flag-explanation"><h4>'+html.escape(title)+'</h4><p><strong>Why it was flagged:</strong> '+html.escape(meaning)+'</p><p><strong>What to check:</strong> '+html.escape(check)+'</p></div>')
    level=row['review_level']
    blocks.append('<p><strong>Review priority:</strong> '+('Low. The parser treats this as a caution to inspect, rather than an automatic correction.' if level=='low' else 'High. The parser found a date or amount issue that deserves closer inspection.')+' The priority is a parser rule, not a confidence percentage or a human verdict.</p>')
    return ''.join(blocks)

def render_review(root):
    with (root/'data/clean/house_ptr_2025_p2.csv').open(encoding='utf-8',newline='') as f:
        rows=list(csv.DictReader(f))
    decisions=json.loads((root/'data/review/decisions.json').read_text(encoding='utf-8'))
    reviewed={(d['filing_id'],r['transaction_number_in_filing']):(d,r) for d in decisions for r in d['rows']}
    flagged=[r for r in rows if r['needs_review']=='True']
    flagged_reviewed=sum((r['filing_id'],r['transaction_number_in_filing']) in reviewed for r in flagged)
    esc=html.escape
    cards=[]
    for row in rows:
        key=(row['filing_id'],row['transaction_number_in_filing'])
        if row['needs_review']!='True' and key not in reviewed:continue
        saved=reviewed.get(key)
        status=saved[0]['decision'] if saved else 'unreviewed'
        label={'keep':'Reviewed · keep','correct':'Reviewed · corrected','unreviewed':'Not yet reviewed'}[status]
        pdf=row['original_pdf_url']+'#page='+row['page']
        flag=row['review_reason'] or 'No original parser flag — additional source check'
        card=f'<details class="review-item" data-review-state="{status}"'+(' hidden' if saved else '')+'>'
        card+=f'<summary>{esc(row["politician"])} · {esc(key[0])}/{esc(key[1])}<span class="review-status">{label}</span></summary>'
        card+=flag_guidance(row)
        card+=f'<details class="technical-flags"><summary>Original parser fields</summary><p><strong>Original flag:</strong> {esc(flag)}</p><p><code>needs_review = {esc(row["needs_review"])}</code> means the parser requested inspection. <code>review_level = {esc(row["review_level"] or "blank")}</code> is its priority. <code>possible_adjacent_same_signature = {esc(row["possible_adjacent_same_signature"])}</code> records whether it found a similar neighboring entry.</p></details>'
        card+=f'<p>{esc(row["asset_v8_2_cleaned"])} · {esc(row["transaction_date"])} · {esc(row["amount_raw"])}</p><p><a href="{esc(pdf,quote=True)}" target="_blank" rel="noopener">Open original PDF · page {esc(row["page"])} ↗</a></p>'
        if saved:
            d,r=saved
            assert all(row[k]==v for k,v in r['original_flags'].items())
            card+=f'<p><strong>Decision confirmed by {esc(d["reviewed_by"])}:</strong> {esc(d["action"])}</p><p>{esc(d["reason"])}</p>'
            card+='<div class="table-wrap"><table><thead><tr><th>Field</th><th>Before review</th><th>After review</th></tr></thead><tbody>'
            for field,before in r['before'].items():
                card+=f'<tr><td>{esc(field)}</td><td>{esc(before or "(blank)")}</td><td>{esc(r["after"][field] or "(blank)")}</td></tr>'
            card+='</tbody></table></div>'
            card+=f'<p><strong>Decision scope:</strong> {d["affected_count"]} {esc(d["count_unit"])} across this case. <strong>Loss:</strong> {esc(d["what_is_lost"])}</p><p><strong>Reversal:</strong> {esc(d["how_to_reverse"])}</p>'
            card+=f'<details><summary>Reviewed PDF excerpt</summary><div class="evidence"><img loading="lazy" src="images/review-{d["id"]}.png" alt="Source PDF excerpt for filing {esc(key[0])}"></div></details>'
        else:
            card+='<p><strong>Human decision: not yet reviewed.</strong> The original flag remains open. No human acceptance or correction has been recorded for this row.</p>'
        cards.append(card+'</details>')
    assert len(reviewed)==5 and len(flagged)==206 and flagged_reviewed==3
    return f'''<section id="cleaning-log"><h3>Review flagged transactions</h3>
<section id="cleaning-execution"><h4>Cleaning execution</h4><p>Confirmed decisions retain four reviewed rows and correct one exact amount in two cells. Source text, range bounds and original flags are preserved. Each reviewed row below explains the alternative considered and how to reverse its decision.</p></section><p>These are your original parser flags, with confirmed human decisions attached. The list covers the full dataset, independently of the random filing above.</p>
<p><strong>{len(flagged)} originally flagged</strong> · {flagged_reviewed} reviewed · <strong>{len(flagged)-flagged_reviewed} not yet reviewed</strong>. Two additional unflagged rows were checked. Existing flags remain as history; a human decision does not automatically clear unrelated issues.</p>
<label for="review-state">Show</label><select id="review-state"><option value="unreviewed">Original flags not yet reviewed (203)</option><option value="reviewed">Reviewed rows (5)</option><option value="all">All review rows (208)</option></select>
<label for="review-search">Find a member, filing or flag</label><input id="review-search" type="search" placeholder="Try missing_range_bound or 20033320"><p id="review-count" role="status">203 rows shown</p>
{''.join(cards)}
<p><strong>For grading:</strong> these same saved decisions generate the manual-review entries in notebook section 3. Its required cleaning log also documents general extraction and cleaning operations, including counts, reasons, losses and reversal. <a href="P2-notebook.html#3.-Quantified-cleaning-log-and-reviewed-decisions">Read the notebook cleaning log →</a></p></section>'''
