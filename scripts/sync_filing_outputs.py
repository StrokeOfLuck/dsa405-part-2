"""Keep each filing's final preview/download consistent with the notebook output."""
import csv
import io
import json
from collections import defaultdict

def sync_filing_outputs(root):
    with (root/'data/clean/house_ptr_2025_p2.csv').open(encoding='utf-8',newline='') as f:
        reader=csv.DictReader(f);columns=reader.fieldnames;grouped=defaultdict(list)
        for row in reader:grouped[row['filing_id']].append(row)
    for filing,rows in grouped.items():
        p=root/f'docs/data/filings/{filing}.json'
        ex=json.loads(p.read_text(encoding='utf-8'))
        lookup={r['transaction_number_in_filing']:r for r in rows}
        record=lookup[str(ex['spotlight_row'])]
        ex['csv_record']=record
        ex['csv_columns']=len(columns)
        for col in ['amount_exact','amount_status']:
            if col not in ex['preview_columns']:ex['preview_columns'].append(col)
        ex['csv_preview']=[{col:lookup[str(r['transaction_number_in_filing'])][col] for col in ex['preview_columns']} for r in ex['csv_preview']]
        for col in ex['p2']:
            if col in record:ex['p2'][col]=(record[col]=='True') if col in {'raw_date_has_extra_text','date_prefix_disagrees'} else record[col]
        # Stage 3 remains the original parsing result; P2 corrections belong to the final CSV.
        ex['stage3']['amount_exact']=record['amount_exact_before_p2']
        ex['stage3']['amount_status']=record['amount_status_before_p2']
        stream=io.StringIO(newline='');writer=csv.DictWriter(stream,fieldnames=columns,lineterminator='\n');writer.writerow(record)
        ex['csv_serialized_row']=stream.getvalue()
        with (root/'docs'/ex['csv_url']).open('w',encoding='utf-8',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=columns,lineterminator='\n');writer.writeheader();writer.writerows(rows)
        p.write_text(json.dumps(ex,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'Synchronized {len(grouped)} filing downloads with the corrected notebook output.')
