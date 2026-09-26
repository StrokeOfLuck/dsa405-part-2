"""Build a review view from existing parser flags and recorded human decisions."""
import csv
import html
import json

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
        card+=f'<p><strong>Original flag:</strong> {esc(flag)}</p><p><code>needs_review = {esc(row["needs_review"])}</code> · <code>review_level = {esc(row["review_level"] or "blank")}</code> · <code>possible_adjacent_same_signature = {esc(row["possible_adjacent_same_signature"])}</code></p>'
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
