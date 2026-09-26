"""Refresh same-page dictionary and log from the executed notebook's CSV outputs."""
from pathlib import Path
import csv
import html
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs'
def records(name):
    with (ROOT/'data/clean'/name).open(encoding='utf-8',newline='') as f:
        return list(csv.DictReader(f))

def details(row):
    return '<dl>'+''.join(f'<dt>{html.escape(k.capitalize())}</dt><dd>{html.escape(str(v))}</dd>' for k,v in row.items())+'</dl>'

dictionary = records('data_dictionary.csv')
assert len(dictionary)==66 and len({r['variable'] for r in dictionary})==66
entries=''.join('<details class="dictionary-entry"><summary><code>'+html.escape(r['variable'])+'</code> · '+html.escape(r['type'])+'</summary>'+details({k:v for k,v in r.items() if k!='variable'})+'</details>' for r in dictionary)
dictionary_html='''<section class="p2-review" id="data-dictionary"><h2>Data dictionary</h2><p>The CSV contains transactions; this dictionary explains its columns. Expand a field to see its meaning, type, units, allowed values, missingness and caveats. These are the same definitions generated in notebook section 2.</p><p>Counts refer to the full corrected dataset (7,667 rows), not the selected filing. Stage 3's asset and ticker are preserved as asset_v8_1 and ticker_v8_1; later versions and audit fields are documented separately.</p><label for="dictionary-search">Find a field or meaning</label><input id="dictionary-search" type="search" placeholder="Try amount, date or ticker"><p id="dictionary-count" role="status">66 of 66 fields shown</p>'''+entries+'''<p><a href="data/data_dictionary.csv" download>Download dictionary CSV</a> · <a href="data/house_ptr_2025_p2.csv" download>Download corrected transaction CSV</a></p></section>'''
log=records('cleaning_log.csv')
from review_view import render_review
log_html=render_review(ROOT)
page=(DOCS/'index.html').read_text(encoding='utf-8')
for marker,content in [('DICTIONARY',dictionary_html),('LOG',log_html)]:
    pattern=f'<!-- P2_{marker}_START -->.*?<!-- P2_{marker}_END -->'
    page,n=re.subn(pattern,lambda m:f'<!-- P2_{marker}_START -->{content}<!-- P2_{marker}_END -->',page,flags=re.S)
    assert n==1, f'Missing or duplicate {marker} marker'
(DOCS/'index.html').write_text(page,encoding='utf-8')
for name in ['house_ptr_2025_p2.csv','data_dictionary.csv','cleaning_log.csv','validation_summary.json']:
    shutil.copy2(ROOT/'data/clean'/name,DOCS/'data'/name)
print(f'Exported {len(dictionary)} definitions and {len(log)} log entries.')

from sync_filing_outputs import sync_filing_outputs
sync_filing_outputs(ROOT)
