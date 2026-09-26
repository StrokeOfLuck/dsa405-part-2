
    const $=id=>document.getElementById(id);
    const addText=(parent,tag,value,className)=>{const el=document.createElement(tag);el.textContent=value===""&&["div","details"].includes(tag)?"":value==null||value===""?"—":String(value);if(className)el.className=className;parent.append(el);return el};
    function fields(id,entries){const root=$(id);root.replaceChildren();for(const [label,value,raw] of entries){addText(root,"dt",label);addText(root,"dd",value,raw?"raw mono":"")}}
    let allCodeCards=[],currentExample=null,auditExample=null,csvSelectedField="asset_v8_2_cleaned",csvSelectedRecord=null;
    let stepCode={},sourceFiles=[],activeStep="source",codeRequest=0;
    const sourceCache=new Map();
    function renderCode(code){stepCode=code;allCodeCards=Object.values(code).flat();}
    function render(ex){
      currentExample=ex;auditExample=null;csvSelectedRecord=null;
      document.querySelectorAll(".learning-panel").forEach(panel=>panel.remove());
      $("selected-member").textContent=ex.politician;$("selected-info").textContent=`Filing ${ex.filing_id} · ${ex.rows} parsed transactions`;$("open-pdf").href=ex.pdf_url;$("pdf-link").href=ex.pdf_url;$("pdf-image").src=ex.pdf_image;$("pdf-image").alt=`Page ${ex.page} of House PTR filing ${ex.filing_id} for ${ex.politician}`;
      $("pdf-caption").textContent=`Filing ${ex.filing_id} · page ${ex.page} of ${ex.page_count} page${ex.page_count===1?"":"s"}`;
      const summary=$("summary");summary.replaceChildren();for(const [name,value] of [["Member",ex.politician],["District",ex.state_district],["Filing",ex.filing_id],["Transactions",ex.rows],["Following row",ex.spotlight_row]]){const p=addText(summary,"span",`${name}: ${value}`,"pill");}
      const facts=$("facts");facts.replaceChildren();for(const [name,value] of [["Member",ex.politician],["District",ex.state_district],["Filing ID",ex.filing_id],["Pages",ex.page_count],["Transactions parsed",ex.rows],["Row followed below",ex.spotlight_row]]){addText(facts,"dt",name);addText(facts,"dd",value)}
      $("raw-text").textContent=(ex.raw_pdf_text||"No embedded text was extracted from this page. It may be scanned; inspect the original PDF.")+(ex.raw_text_truncated?"\n\n… page excerpt ends here; open the PDF for the full document.":"");
      renderGeometry(ex);
      setupSourceGuide();
      const noRows=ex.status==="no_parsed_rows";
      $("no-rows").classList.toggle("hidden",!noRows);$("no-rows").textContent=ex.status_note||"";
      for(const id of ["parse","resolve","audit","csv"])$(id).classList.toggle("no-transactions",noRows);
      document.querySelectorAll(".empty-state").forEach(note=>note.classList.toggle("hidden",!noRows));
      for(const id of ["raw-fields","parsed-fields","before-fields","after-fields","audit-cards","preview"])$(id).replaceChildren();
      $("download").classList.toggle("hidden",noRows);
      const url=new URL(location.href);url.searchParams.set("filing",ex.filing_id);history.replaceState(null,"",url);
      if(noRows){$("resolver-note").textContent="No parsed row is available to trace through Stage 4. The code below is still available to study.";$("csv-description").textContent=ex.status_note;selectStep(activeStep);return;}
      const s=ex.stage3,r=ex.stage4,p=ex.p2;
      fields("raw-fields",[["Asset text",s.asset_raw,true],["Trade code text",s.transaction_type_raw,true],["Trade date text",s.transaction_date_raw,true],["Amount text",s.amount_raw,true],["PDF row method",s.page_parse_method]]);
      fields("parsed-fields",[["Asset",s.asset],["Ticker",s.ticker],["Trade type",s.transaction_type],["Trade date",s.transaction_date],["Amount minimum",s.amount_min],["Amount maximum",s.amount_max],["Needs review",s.needs_review]]);
      wireParsedFields();
      fields("before-fields",[["Asset",r.asset_v8_1],["Ticker",r.ticker_v8_1]]);
      fields("after-fields",[["Asset",r.asset_v8_2_cleaned],["Ticker",r.ticker_v8_2_cleaned],["Candidate",r.ticker_candidate_raw],["Decision",r.ticker_parse_status],["Review flag",r.needs_review]]);
      wireResolveFields();
      $("resolver-note").textContent=ex.changed_stage4_values?`Across this filing, ${ex.changed_stage4_values} asset or ticker cells changed in Stage 4. The old values remain in the CSV.`:"The resolver classified the candidate, but the asset and ticker text did not change in this filing. The old values are still retained for comparison.";
      const audit=$("audit-cards");audit.replaceChildren();for(const [title,value,desc] of [["Extra text in raw date?",p.raw_date_has_extra_text?"Yes":"No","Checks whether the entire original date field is only a date."],["Leading date found",p.raw_date_prefix||"None","Pulls a date from the beginning of the original text, if present."],["Does it disagree?",p.date_prefix_disagrees?"Yes — inspect PDF":"No","Compares that leading date with the normalized transaction date."]]){const card=document.createElement("div");card.className="box";addText(card,"span",title);addText(card,"strong",value);addText(card,"span",desc);audit.append(card)}
      const table=document.createElement("table"),head=document.createElement("thead"),hrow=document.createElement("tr");for(const col of ex.preview_columns)addText(hrow,"th",col.replaceAll("_"," "));head.append(hrow);table.append(head);const body=document.createElement("tbody");for(const row of ex.csv_preview){const tr=document.createElement("tr");for(const col of ex.preview_columns)addText(tr,"td",row[col]);body.append(tr)}table.append(body);$("preview").replaceChildren(table);
      $("csv-description").textContent=`${ex.rows} transaction row${ex.rows===1?"":"s"} · ${ex.csv_columns} columns · filing ${ex.filing_id}`;$("download").href=ex.csv_url;$("download").download=`house_ptr_${ex.filing_id}_p2.csv`;
      setupAuditLearning();setupCsvLearning();
      if(activeStep==="audit"||activeStep==="csv")selectStep(activeStep);
      if(activeStep==="parse")selectParsedField("asset");
      if(activeStep==="resolve")selectResolveField("decision");
    }
    function selectLearning(kind,key){const card=stepCode[kind].find(c=>kind==="audit"?c.audit_field===key:c.csv_action===key);if(card)showCode(card);}
    function auditValues(){return auditExample||{raw:currentExample.stage3.transaction_date_raw,date:currentExample.stage3.transaction_date,...currentExample.p2};}
    function setupAuditLearning(){
      const panel=document.createElement("div");panel.className="box learning-panel";$("audit-cards").before(panel);
      addText(panel,"h3","Explore the date checks");addText(panel,"p","Teaching examples only change this explanation. They do not change the filing or its CSV.");
      const controls=addText(panel,"div","","learning-controls"),context=addText(panel,"pre","");
      const examples=[
        ["This transaction",null],
        ["Extra text",{raw:"11/19/2025 extra text",date:"2025-11-19",raw_date_has_extra_text:true,raw_date_prefix:"11/19/2025",date_prefix_disagrees:false}],
        ["Different dates",{raw:"11/19/2025",date:"2025-11-20",raw_date_has_extra_text:false,raw_date_prefix:"11/19/2025",date_prefix_disagrees:true}],
        ["Invalid date",{raw:"13/40/2025",date:"",raw_date_has_extra_text:false,raw_date_prefix:"13/40/2025",date_prefix_disagrees:false}]
      ];
      function refresh(label){const data=auditValues();context.textContent=`${auditExample?"Teaching example: "+label:"Saved transaction"}\nOriginal date text = ${JSON.stringify(data.raw)}\nParser date = ${JSON.stringify(data.date)}`;
        const keys=["raw_date_has_extra_text","raw_date_prefix","date_prefix_disagrees"];
        [...$("audit-cards").children].forEach((card,i)=>{let button=card.querySelector("button");if(!button){const strong=card.querySelector("strong");button=document.createElement("button");button.type="button";button.className="parsed-value";strong.replaceWith(button);button.addEventListener("click",()=>selectLearning("audit",keys[i]));}button.textContent=i===1?(data[keys[i]]||"No prefix"):(data[keys[i]]?"Yes":"No");button.setAttribute("aria-label",`Explain ${keys[i]}: ${button.textContent}`);});
      }
      for(const [label,data] of examples){const button=addText(controls,"button",label,"parsed-value");button.type="button";button.setAttribute("aria-pressed",String(data===null));button.addEventListener("click",()=>{auditExample=data;for(const b of controls.children)b.setAttribute("aria-pressed",String(b===button));refresh(label);selectLearning("audit",data?.date_prefix_disagrees||label==="Invalid date"?"date_prefix_disagrees":"raw_date_has_extra_text");});}
      refresh("This transaction");
    }
    function csvEncode(value){const text=String(value??"");return /[",\r\n]/.test(text)?'"'+text.replaceAll('"','""')+'"':text;}
    function setupCsvLearning(){
      const panel=document.createElement("div");panel.className="box learning-panel";$("csv").querySelector(".stage-head").after(panel);
      addText(panel,"h3","Inspect the transaction you followed");addText(panel,"p","Choose any column or click a value in the first preview row. See the saved value, its position, and how it is written into CSV text.");
      const label=addText(panel,"label","CSV column"),select=document.createElement("select");select.id="csv-column";label.htmlFor=select.id;
      for(const key of Object.keys(currentExample.csv_record)){const option=addText(select,"option",key);option.value=key;}
      if(!Object.hasOwn(currentExample.csv_record,csvSelectedField))csvSelectedField=Object.keys(currentExample.csv_record)[0];
      select.value=csvSelectedField;panel.append(select);select.addEventListener("change",()=>{csvSelectedField=select.value;selectLearning("csv","field");});
      const controls=addText(panel,"div","","learning-controls");
      for(const [key,title] of [["field","Inspect this field"],["row","See complete CSV record"],["index","Why index=False?"]]){const button=addText(controls,"button",title,"parsed-value");button.type="button";button.addEventListener("click",()=>selectLearning("csv",key));}
      const previewRow=$("preview").querySelector("tbody tr");
      if(previewRow)[...previewRow.children].forEach((td,i)=>{const value=td.textContent;td.replaceChildren();const button=addText(td,"button",value,"parsed-value");button.type="button";const key=currentExample.preview_columns[i];button.setAttribute("aria-label",`Inspect CSV ${key}`);button.addEventListener("click",()=>{csvSelectedField=key;select.value=key;selectLearning("csv","field");});});
    }
    function showLearningValues(pre,card){
      if(!currentExample?.stage3)return;
      const isAudit=activeStep==="audit"&&card?.audit_field,isCsv=activeStep==="csv"&&card?.csv_action;if(!isAudit&&!isCsv)return;
      const box=document.createElement("span");box.className="runtime-values";box.setAttribute("role","note");addText(box,"strong",card.label);
      if(isAudit){const data=auditValues(),key=card.audit_field;
        addText(box,"span",auditExample?"Illustrative teaching example — filing unchanged.":"Saved audit result for this transaction.","runtime-note");
        addText(box,"span",`transaction_date_raw = ${JSON.stringify(data.raw)}\ntransaction_date = ${JSON.stringify(data.date)}`,"runtime-output");
        if(key==="date_prefix_disagrees")addText(box,"span",`raw_date_prefix = ${JSON.stringify(data.raw_date_prefix)}\nA missing or invalid prefix cannot trigger this flag.`,"runtime-output");
        addText(box,"strong","Result");addText(box,"span",`${key} = ${JSON.stringify(data[key])}`,"runtime-output");
      }else{const record=currentExample.csv_record,keys=Object.keys(record),field=csvSelectedField,value=record[field];
        addText(box,"span",`Saved transaction ${currentExample.spotlight_row} · ${keys.length} columns. The notebook writes the full year; this download contains this filing.`,"runtime-note");
        if(card.csv_action==="field"){
          addText(box,"strong",`Column ${keys.indexOf(field)+1}: ${field}`);addText(box,"span",`Saved value = ${JSON.stringify(value)}`,"runtime-output");addText(box,"strong","CSV field text");addText(box,"span",csvEncode(value)||"(empty field between separators)","runtime-output");
          addText(box,"span",/[",\r\n]/.test(value)?"This value needs surrounding quotes. Any quote inside it is doubled. Quoting keeps its commas or line breaks inside one field.":"This value needs no CSV quotes. CSV does not store a Python data type; software interprets the text when reading it.","runtime-note");
          addText(box,"span",field.startsWith("raw_date_")||field==="date_prefix_disagrees"?"Created by the Part 2 date checks in step 05.":field.includes("v8_1")?"Preserved earlier value for comparison with Stage 4.":"Carried into the final table from the parser/resolver. Steps 03 and 04 explain those transformations.","runtime-note");
        }else if(card.csv_action==="row"){
          addText(box,"strong","Header — column names in order");addText(box,"span",keys.map(csvEncode).join(","),"runtime-output");addText(box,"strong","One complete saved transaction record");addText(box,"span",currentExample.csv_serialized_row,"runtime-output");
        }else{
          addText(box,"span",`index=False: ${keys.slice(0,3).join(",")},…\nIllustration with index=True: ,${keys.slice(0,3).join(",")},…\nThe extra first column would hold the DataFrame index. The real transaction_number_in_filing column is kept.`,"runtime-output");
        }
      }
      pre.querySelector(".focused")?.after(box);
    }
    function setupSourceGuide(){
      $("source-guide")?.remove();
      const panel=document.createElement("div");panel.id="source-guide";panel.className="box source-guide";
      $("source").querySelector(".stage-head").after(panel);
      $("workflow-map")?.remove();
      const map=document.createElement("div");map.id="workflow-map";map.className="box source-guide";panel.before(map);
      addText(map,"h3","Where this project enters the original workflow");
      addText(map,"p","The original scraper has four numbered stages. Project 2 reuses its archived inputs, then runs extraction and cleanup. The website tab numbers are lesson numbers, not scraper stage numbers.");
      const list=document.createElement("ol");list.className="workflow-list";map.append(list);
      const rows=[
        ["Original Stage 1 · Download PDFs","stage1_download.py","Not rerun here — reuse the 2025 PDF archive.","download"],
        ["Original Stage 2 · Verify collection coverage","stage2_verify.py","Not rerun here — original index-versus-files audit. It can also read existing parser checkpoints.","verify"],
        ["Project 2 entry · Retrieve and check the archive","rebuild_2025.py","Get the fixed Git version and verify 515 PDF copies against the manifest. This checks the saved archive, not today's live filing list.","archive"],
        ["Original Stage 3 · Extract transactions","stage3_extract.py","Runs on the verified PDFs → transactions_raw.csv. Website tabs 02 and 03 explain this same script.","parse"],
        ["Original Stage 4 · Review tickers","stage4_clean.py","Runs on extracted rows → transactions_resolved.csv. Website tab 04 explains this script.","resolve"],
        ["Prepare parser output files","publish_latest.py","Runs after Stage 4 and prepares local parser output files for downstream use.","publish"],
        ["Class notebook · Audit and final CSV","Colab cell 21","Load the saved tables, add date checks, then write house_ptr_2025_p2.csv. Website tabs 05 and 06 explain these operations.","audit"]
      ];
      for(const [title,file,description,key] of rows){const li=document.createElement("li");list.append(li);addText(li,"strong",title);addText(li,"p",description);const button=addText(li,"button","See code: "+file,"parsed-value");button.type="button";button.addEventListener("click",()=>{
        if(key==="download"||key==="verify")showCode(stepCode.source.find(c=>c.workflow_only&&c.url.includes(key==="download"?"stage1_download.py":"stage2_verify.py")));
        else if(key==="archive")showCode(stepCode.source.find(c=>c.label.includes("Check the PDF copies")));
        else if(key==="publish")showCode(stepCode.source[0],sourceFiles.find(f=>f.name==="publish_latest.py"));
        else selectStep(key);
      });}

      addText(panel,"h3","Step 01: setup and starting the pipeline");
      addText(panel,"p","This page shows a saved run. Clicking a lesson changes the explanation and code highlight; it does not install anything or rerun Python.");
      addText(panel,"p","These seven lessons explain setup and the command that launches extraction. They are not seven separate stages of the whole project. The six tabs above follow the full journey:");
      const journey=addText(panel,"p","01 Get the PDFs ready → 02 Read PDF regions → 03 Separate transaction fields → 04 Review tickers → 05 Add class date checks → 06 Write the final CSV.");
      addText(panel,"p","The complete project source is available on the left. Highlights explain selected operations for this saved transaction, rather than showing every instruction executing. Step 01 starts the parser work that tabs 02–04 explain; those tabs do not run it again.");
      const controls=addText(panel,"div","","learning-controls");controls.id="source-lesson-buttons";
      for(const card of stepCode.source.filter(c=>c.source_guide&&!c.workflow_only)){const button=addText(controls,"button",card.label,"parsed-value");button.type="button";button.dataset.label=card.label;button.addEventListener("click",()=>showCode(card));}
      const content=addText(panel,"div","");content.id="source-lesson-content";content.setAttribute("aria-live","polite");
      const note=addText(panel,"details","");addText(note,"summary","How does the PDF picture fit in?");addText(note,"p",`The image below is a preview of filing ${currentExample.filing_id}. Its highlight identifies the transaction followed later. The website draws that preview from saved data; the setup code on the left prepares files for the Python parser. In step 02, we inspect the actual PDF regions the parser read.`);
      if(activeStep==="source")showCode(stepCode.source[0]);else updateSourceGuide(stepCode.source[0]);
    }
    function updateSourceGuide(card){
      const content=$("source-lesson-content");if(!content||activeStep!=="source")return;
      for(const button of $("source-lesson-buttons").children)button.setAttribute("aria-pressed",String(button.dataset.label===card?.label));
      content.replaceChildren();
      if(!card?.source_guide){addText(content,"p","You are browsing source code. Choose a numbered lesson above to return to its explanation.");return;}
      const guide=card.source_guide;
      addText(content,"h3",card.label);addText(content,"strong","What happens");addText(content,"p",guide.what);addText(content,"strong","Why we do it");addText(content,"p",guide.why);
      const flow=addText(content,"div","","guide-flow");addText(flow,"strong","Starts with");addText(flow,"p",card.reads);addText(flow,"strong","After this code runs");addText(flow,"p",card.makes);
      const controls=addText(content,"div","","learning-controls"),cards=stepCode.source.filter(c=>c.source_guide&&!c.workflow_only),index=cards.findIndex(c=>c.label===card.label);
      for(const [next,label] of [[index-1,"← Previous lesson"],[index+1,"Next lesson →"]])if(index>=0&&cards[next]){const button=addText(controls,"button",label,"parsed-value");button.type="button";button.addEventListener("click",()=>showCode(cards[next]));}
      if(index===cards.length-1){const link=addText(controls,"a","Continue to 02 · PDF geometry →","btn");link.href="#text";}
    }
    function showSourceTranslation(pre,card){
      if(activeStep!=="source"||!card?.source_guide)return;
      const box=document.createElement("span");box.className="runtime-values";box.setAttribute("role","note");addText(box,"strong","Read this line in plain English");addText(box,"span",card.source_guide.translation,"runtime-note");pre.querySelector(".focused")?.after(box);
    }
    function showWhy(card){
      const stage=$(activeStep);if(!stage)return;
      const old=stage.querySelector(".why-panel"),priorParent=old?.parentElement;
      const clicked=document.activeElement?.closest("dd");
      old?.remove();
      const ex=currentExample;if(!card||!ex?.stage3||activeStep==="source")return;
      const s=ex.stage3,r=ex.stage4,q=v=>JSON.stringify(v??"");
      let original,rule,change,result,why,links=[],match=null;
      if(activeStep==="parse"&&card.parsed_field){
        const field=card.parsed_field;
        if(field==="transaction_type"){
          match=ex.trade_match;original=q(s.transaction_type_raw);rule="Find a standalone P, S, or E, optionally followed by (partial) or (full). Matching ignores letter case.";
          change=match?.matched?`Matched ${q(match.matched)}. Outside the match: ${q(match.before)} before and ${q(match.after)} after.`:"No recognized trade token was found.";
          result=q(s.transaction_type);why="The rule extracts a recognized token; it does not interpret the leftover text. Word boundaries prevent matching a code embedded inside a longer word. The raw field stays preserved.";
          links=stepCode.parse.filter(c=>c.parsed_field===field).map(c=>[c.label==="Show trade matching pattern"?"Show matching rule":"Show the extraction line",c]);
        }else if(field==="asset"){
          original=q(s.asset_raw);rule="Take the name before Filing Status:, remove the asset-type marker and accepted ticker parenthetical, then trim whitespace. The function also handles a leaked owner code or a description fallback.";
          change=`Asset type recorded: ${q(s.asset_type)}. Ticker extracted separately: ${q(s.ticker)}. Filing details are kept separately from the presentation name.`;result=q(s.asset);why="Separate the company/asset name from metadata so each can be analyzed as its own field. The original asset text stays available for checking.";
        }else if(field==="ticker"){
          original=q(s.asset_lookup_context);rule="Find parenthetical candidates, keep those that pass the plausibility checks, and choose the last accepted candidate in the context.";
          change=s.ticker?`Stage 3 selected ${q(s.ticker)}.`:"Stage 3 returned an empty ticker; no candidate was accepted.";result=q(s.ticker);why="Parentheses may contain other text, so the parser applies a rule before choosing a ticker. Stage 4 reviews the result separately.";
        }else if(field==="transaction_date"){
          original=q(s.transaction_date_raw);rule="Find the first date-shaped token, then convert month/day/year to YYYY-MM-DD. The date audit later checks for extra text or disagreement.";
          change=`Token found: ${q(s.date_token)} → stored date: ${q(s.transaction_date)}.`;result=q(s.transaction_date);why="A consistent date format makes dates easier to compare. The transaction date can be earlier than the filing year. A failed conversion is not silently turned into a valid date.";
          links=stepCode.parse.filter(c=>c.parsed_field===field).map(c=>[c.label,c]);
        }else if(field==="amount_min"){
          original=q(s.amount_raw);rule="Read money values from the amount field and permitted continuation prefix. Recognize standard ranges, exact amounts, or open-ended wording using separate rules.";
          change=`Saved classification: ${q(s.amount_status)}; category: ${q(ex.csv_record.amount_category)}.`;
          result=`Minimum: ${q(s.amount_min)}\nMaximum: ${q(s.amount_max)}\nExact amount: ${q(s.amount_exact)}`;why="Dollar signs and commas are formatting. Bounds describe the disclosed range; they do not reveal the exact trade amount. Empty bounds must not be treated as zero.";
        }else{
          original=`Asset: ${q(s.asset)}\nTicker: ${q(s.ticker)}\nDate: ${q(s.transaction_date)}\nAmount: ${q(s.amount_raw)}`;rule="Run validation checks and collect review reasons; the flag reflects whether reasons remain.";
          change=s.review_reason?`Recorded reasons: ${s.review_reason}`:"No review reasons were recorded for this transaction.";result=`needs_review = ${q(s.needs_review)}`;why="A flag asks for inspection. No flag means these checks found no recorded issue, not that the row has been independently proven correct.";
        }
      }else if(activeStep==="resolve"&&card.resolve_field){
        const status=r.ticker_parse_status,source=r.ticker_validation_source;
        const decisions={not_applicable:"Asset type is not ST, so this resolver skips candidate extraction and retains the earlier ticker.",missing_candidate:"No candidate and no earlier ticker were found.",legacy_only_review:"No new candidate was found; the earlier ticker is retained for review.",validated:"The candidate matched the configured reference symbols.",accepted:source==="house_ptr_structure+v8_1"?"The candidate equals the earlier ticker, so the resolver accepts it.":"The source candidate fits the structural length rule, so the resolver accepts it.",ambiguous_preserved:"The longer candidate is preserved for review; the resolved ticker is left empty.",accepted_long_existing:"The saved status records acceptance of a longer existing ticker."};
        original=`Earlier asset: ${q(r.asset_v8_1)}\nEarlier ticker: ${q(r.ticker_v8_1)}\nCandidate: ${q(r.ticker_candidate_raw)}`;
        rule=card.resolve_field==="asset"?"Remove only the accepted ticker parenthetical from the presentation name; keep the original value.":card.resolve_field==="review"?"Remove obsolete missing-ticker warnings if a ticker was resolved; add or retain applicable reasons and recompute the flag.":"Classify the candidate using asset type, the earlier ticker, source structure, and any reference match.";
        change=card.resolve_field==="review"?`Earlier reasons: ${q(r.review_reason_v8_1)}\nCurrent reasons: ${q(r.review_reason)}`:card.resolve_field==="asset"?`Asset changed: ${r.asset_changed_by_ticker_resolver}`:(decisions[status]||`Recorded decision: ${status}`);
        result=card.resolve_field==="asset"?q(r.asset_v8_2_cleaned):card.resolve_field==="review"?`Needs review: ${r.needs_review}\nLevel: ${q(r.review_level)}`:`Ticker: ${q(r.ticker_v8_2_cleaned)}\nDecision: ${status}\nValidation source: ${q(source)}`;
        why="Preserve earlier evidence and make the resolver's decision inspectable. Structural acceptance is not independent confirmation that the ticker identifies the right security.";
      }else if(activeStep==="audit"&&card.audit_field){
        const d=auditValues(),key=card.audit_field;original=`Original date text: ${q(d.raw)}\nParser date: ${q(d.date)}`;rule=card.explanation;
        change=key==="raw_date_has_extra_text"?(d[key]?"The entire text does not match the date-only pattern.":"The entire text matches the date-shaped pattern. This alone does not validate the calendar date."):key==="raw_date_prefix"?`Leading date-shaped token: ${q(d.raw_date_prefix)}`:d[key]?"The valid leading date differs from the parser date.":"No disagreement was flagged: either the dates agree or the prefix is missing/invalid.";
        result=`${key} = ${q(d[key])}`;why=(auditExample?"Teaching example; the filing is unchanged. ":"")+"These extra columns make uncertainty visible without overwriting the original date or parser result.";
      }else if(activeStep==="csv"&&card.csv_action){
        const field=csvSelectedField,value=ex.csv_record[field];original=`${field} = ${q(value)}`;rule="Write columns in table order. Quote fields containing commas, quotes, or line breaks; double any quotes inside a quoted field. index=False omits the extra DataFrame index.";
        change=/[",\r\n]/.test(value)?"This value requires CSV quoting to keep it in one field.":value===""?"This is an empty CSV field, not a zero.":"This value can be written without surrounding CSV quotes.";result=csvEncode(value)||"(empty field)";why="CSV preserves field boundaries as text. Reading software decides how to interpret numbers, dates, and booleans.";
        let target=null;
        if(field.startsWith("raw_date_")||field==="date_prefix_disagrees")target=stepCode.audit.find(c=>c.audit_field===field);
        else if(["ticker_v8_2_cleaned","ticker_candidate_raw","ticker_parse_status","asset_v8_2_cleaned","needs_review"].includes(field))target=stepCode.resolve.find(c=>c.resolve_field===({ticker_v8_2_cleaned:"ticker",ticker_candidate_raw:"candidate",ticker_parse_status:"decision",asset_v8_2_cleaned:"asset",needs_review:"review"}[field]));
        else target=stepCode.parse.find(c=>c.parsed_field===({amount_max:"amount_min",transaction_date_raw:"transaction_date",transaction_type_raw:"transaction_type",asset_raw:"asset",amount_raw:"amount_min",ticker_v8_1:"ticker",asset_v8_1:"asset"}[field]||field));
        if(target)links.push(["Go to the step that explains this field",target]);
      }else if(activeStep==="text"&&activeGeometry){
        const g=activeGeometry,f=g.fields.find(f=>f.name===activeField);original=q(f?f.before:g.before);rule="Combine the row's vertical boundaries with the column's horizontal boundaries, then read embedded text inside that rectangle. Repair known encoded characters and normalize whitespace.";
        change=`Observed route: ${g.method}. Selected area: ${(f?f.rect:g.physical_rect).map(v=>v.toFixed(2)).join(", ")} PDF points.`;result=q(f?f.after:g.after);why="PDF text is positioned on a page, not stored as spreadsheet cells. These boundaries help separate fields, but a rectangle can capture stray neighboring text. Step 03 interprets what was captured.";
      }else return;
      const box=document.createElement("div");box.className="why-panel";box.setAttribute("role","note");addText(box,"h3","How this value was processed");
      for(const [label,value] of [["Original",original],["Rule",rule],["What matched or changed",change],["Result",result],["Why",why]]){addText(box,"strong",label);addText(box,label==="Original"||label==="Result"?"pre":"p",value);}
      if(match?.matched){const display=addText(box,"p","Matched part of the original: ");display.append(document.createTextNode(match.before));addText(display,"mark",match.matched);display.append(document.createTextNode(match.after));}
      if(!links.length)links.push(["Show this rule in the code",card]);
      const controls=addText(box,"div","","learning-controls");for(const [label,target] of links){const button=addText(controls,"button",label,"parsed-value");button.type="button";button.addEventListener("click",()=>{const step=Object.keys(stepCode).find(key=>stepCode[key].includes(target));if(step&&step!==activeStep)selectStep(step);showCode(target);});}
      if(clicked&&stage.contains(clicked))clicked.closest(".box").append(box);
      else if(priorParent&&priorParent!==stage&&stage.contains(priorParent))priorParent.append(box);
      else stage.querySelector(".stage-head").after(box);
    }
    function wireResolveFields(){
      const groups={"before-fields":["asset","ticker"],"after-fields":["asset","ticker","candidate","decision","review"]};
      for(const [id,keys] of Object.entries(groups)) [...$(id).querySelectorAll("dd")].forEach((dd,i)=>{
        const value=dd.textContent;dd.replaceChildren();const button=addText(dd,"button",value,"parsed-value resolve-value");button.type="button";button.dataset.resolveField=keys[i];button.setAttribute("aria-label",`Explain ${dd.previousElementSibling.textContent}: ${value}`);button.addEventListener("click",()=>selectResolveField(keys[i]));
      });
    }
    function selectResolveField(field){const card=stepCode.resolve.find(c=>c.resolve_field===field);if(card)showCode(card);}
    function showResolveValues(pre,card){
      if(activeStep!=="resolve"||!card?.resolve_field||!currentExample?.stage4)return;
      const box=document.createElement("span");box.className="runtime-values";box.setAttribute("role","note");addText(box,"strong",card.label+" · this transaction");
      addText(box,"span","Saved input and output from this transaction. The highlighted source explains the rule; this is not a live execution trace.","runtime-note");
      for(const [label,keys] of [["Input",card.input_keys],["Result",card.output_keys]]){addText(box,"strong",label);for(const path of keys){const [stage,key]=path.split(".");addText(box,"span",`${key} = ${JSON.stringify(currentExample[stage][key]??"")}`,"runtime-output");}}
      pre.querySelector(".focused")?.after(box);
    }
    function wireParsedFields(){
      const groups={"parsed-fields":["asset","ticker","transaction_type","transaction_date","amount_min","amount_min","needs_review"],"raw-fields":["asset","transaction_type","transaction_date","amount_min",null]};
      for(const [id,keys] of Object.entries(groups)){
        [...$(id).querySelectorAll("dd")].forEach((dd,i)=>{if(!keys[i])return;const value=dd.textContent;dd.replaceChildren();const button=addText(dd,"button",value,"parsed-value");button.type="button";button.dataset.field=keys[i];button.setAttribute("aria-label",`Explain ${dd.previousElementSibling.textContent}: ${value}`);button.addEventListener("click",()=>selectParsedField(keys[i]));});
      }
    }
    function selectParsedField(field){
      const candidates=stepCode.parse.filter(c=>c.parsed_field===field);
      const card=field==="transaction_date"?candidates.find(c=>c.label==="Normalize trade date"):candidates[0];
      if(card)showCode(card);
    }
    function showParsedValues(pre,card){
      if(activeStep!=="parse"||!card?.parsed_field||!currentExample?.stage3)return;
      const box=document.createElement("span");box.className="runtime-values";box.setAttribute("role","note");
      addText(box,"strong",card.label+" · this transaction");
      addText(box,"span","Saved input and output; highlighted code shows the rule, not an instruction-by-instruction execution trace.","runtime-note");
      for(const [label,keys] of [["Input",card.input_keys],["Result",card.output_keys]]){addText(box,"strong",label);for(const key of keys)addText(box,"span",`${key} = ${JSON.stringify(currentExample.stage3[key]??"")}`,"runtime-output");}
      pre.querySelector(".focused")?.after(box);
    }
    function codeBlock(text,start,focus){
      const pre=document.createElement("pre"),code=document.createElement("code");
      text.replace(/\n$/,"").split("\n").forEach((line,i)=>{
        const row=document.createElement("span");row.className="code-line"+(start+i===focus?" focused":"");
        addText(row,"span",start+i,"line-number");const content=document.createElement("span");content.className="line-content"+(line.trimStart().startsWith("#")?" comment":"");content.textContent=line||" ";row.append(content);code.append(row);
      });pre.append(code);return pre;
    }
    let activeGeometry=null,activeField="row",showHighlight=true,currentId=null;
    function rectangle(svg,g,rect){
      svg.replaceChildren();svg.setAttribute("viewBox",`0 0 ${g.width} ${g.height}`);
      if(!showHighlight)return;
      const box=document.createElementNS("http://www.w3.org/2000/svg","rect");
      for(const [key,val] of Object.entries({x:rect[0],y:rect[1],width:rect[2]-rect[0],height:rect[3]-rect[1]}))box.setAttribute(key,val);
      svg.append(box);
    }
    function inspectField(name){
      activeField=name;const g=activeGeometry;if(!g)return;
      const field=g.fields.find(f=>f.name===name),rect=field?field.rect:g.physical_rect;
      for(const btn of $("field-controls").children)btn.setAttribute("aria-pressed",String(btn.dataset.field===name));
      rectangle($("geometry-overlay"),g,rect);rectangle($("source-overlay"),g,rect);
      $("geometry-before").textContent=(field?field.before:g.before)||"(empty text)";
      $("geometry-after").textContent=(field?field.after:g.after)||"(empty text)";
      $("geometry-coordinates").textContent=`Page ${g.page} · ${name.replaceAll("_"," ")} · [${rect.map(n=>n.toFixed(2)).join(", ")}] PDF points`;
      $("geometry-code").textContent=field?`# extract_row_columns → clip_text → clean_space\nrect = fitz.Rect(${rect.map(n=>n.toFixed(2)).join(", ")})\noutput["${name}"] = clip_text(page, rect)`:`# Accepted row from ${g.method}\nrow_bbox = (${g.row_rect.map(n=>n.toFixed(2)).join(", ")})\ncore = extract_row_columns(page, row_bbox, column_boxes)`;
      showGeometrySource(Boolean(field));
      const windowEl=document.querySelector(".zoom-window"),sheet=windowEl.firstElementChild;
      const top=Math.max(0,rect[1]-18),bottom=Math.min(g.height,rect[3]+18);
      const viewWidth=Math.min(g.width,Math.max(140,rect[2]-rect[0]+24));
      const left=Math.max(0,Math.min(g.width-viewWidth,(rect[0]+rect[2]-viewWidth)/2));
      windowEl.style.aspectRatio=`${viewWidth} / ${bottom-top}`;
      sheet.style.width=`${100*g.width/viewWidth}%`;
      sheet.style.left=`-${100*left/viewWidth}%`;
      sheet.style.right="auto";
      sheet.style.top=`-${100*top/(bottom-top)}%`;
    }
    function showGeometrySource(isField){
      if(activeStep!=="text"||!$("code-pane"))return;
      const name=isField?"extract_row_columns":activeGeometry.method==="date_anchor_recovery"?"date_anchor_items":"table_row_items";
      const card=allCodeCards.find(c=>c.full_code.startsWith(`def ${name}(`));
      if(card)showCode(card);
    }
    function renderSourceLibrary(sources){sourceFiles=sources;}
    function showRuntimeValues(pre,card){
      if(activeStep!=="text"||!activeGeometry||!card||!/^def (extract_row_columns|clip_text|clean_space|normalize_house_pdf_text|table_row_items|date_anchor_items)\(/.test(card.full_code))return;
      const g=activeGeometry,field=g.fields.find(f=>f.name===activeField);
      const rect=field?field.rect:g.physical_rect;
      const box=document.createElement("span");box.className="runtime-values";box.setAttribute("role","note");box.setAttribute("aria-label","Values for the selected PDF field");
      addText(box,"strong",field?`This loop pass: ${field.name}`:"This physical row");
      addText(box,"span","Saved parser trace · values change with your selection.","runtime-note");
      const values=document.createElement("span");values.className="runtime-input";
      values.textContent=(field?`name = ${JSON.stringify(field.name)}   |   `:"")+`PDF page ${g.page}\nx0 = ${rect[0].toFixed(2)}    x1 = ${rect[2].toFixed(2)}\ny0 = ${rect[1].toFixed(2)}    y1 = ${rect[3].toFixed(2)}\nrect = fitz.Rect(${rect.map(n=>n.toFixed(2)).join(", ")})`;
      box.append(values);
      addText(box,"strong",field?`Returned → output[${JSON.stringify(field.name)}]`:"Row text after cleanup");
      const result=addText(box,"span",JSON.stringify(field?field.after:g.after),"runtime-output");result.dataset.field=activeField;
      const details=document.createElement("details");addText(details,"summary","Compare the text before cleanup");addText(details,"span",JSON.stringify(field?field.before:g.before),"runtime-output");box.append(details);
      const focus=pre.querySelector(".focused");if(focus)focus.after(box);
    }
    async function showCode(card,sourceOverride){
      if(activeStep==="resolve"&&card?.resolve_field&&currentExample?.stage4&&["decision","candidate","ticker"].includes(card.resolve_field)){
        const status=currentExample.stage4.ticker_parse_status, lines=card.full_code.split("\n");
        const index=lines.findIndex((line,i)=>line.includes('"ticker_parse_status": "'+status+'"')&&lines[i+1]?.includes('"ticker_validation_source": "'+currentExample.stage4.ticker_validation_source+'"'));
        if(index>=0)card={...card,focus_line:card.full_start_line+index};
      }
      updateSourceGuide(sourceOverride?null:card);
      showWhy(sourceOverride?null:card);
      const request=++codeRequest;
      $("code-title").textContent=sourceOverride?sourceOverride.name:card.source;
      $("code-explanation").textContent=sourceOverride?sourceOverride.label:card.explanation;
      $("code-origin").href=sourceOverride?sourceOverride.url:card.url;
      for(const button of $("step-code-choices").children)button.setAttribute("aria-pressed",String(button.dataset.label===card?.label&&!sourceOverride));
      document.querySelectorAll("#parsed-fields .parsed-value,#raw-fields .parsed-value").forEach(button=>button.setAttribute("aria-pressed",String(!sourceOverride&&card?.parsed_field===button.dataset.field)));
      document.querySelectorAll(".resolve-value").forEach(button=>button.setAttribute("aria-pressed",String(!sourceOverride&&card?.resolve_field===button.dataset.resolveField)));
      const source=sourceOverride|| (card.kind!=="notebook"?sourceFiles.find(f=>f.name===card.url.split("/").pop().split("#")[0]):null);
      $("code-file").value=source?source.name:"notebook";
      $("code-reading").textContent=source?"Complete file · highlighted function and current line":"Saved teaching cell · current line highlighted";
      $("code-body").textContent="Loading source…";
      try{
        let text=card?.full_code,start=card?.full_start_line||1;
        if(source){start=1;if(!sourceCache.has(source.name)){const response=await fetch(source.text_url+"?v=explain-v13");if(!response.ok)throw Error(String(response.status));sourceCache.set(source.name,await response.text());}text=sourceCache.get(source.name);}
        if(request!==codeRequest)return;
        const pre=codeBlock(text,start,sourceOverride?null:card.focus_line);pre.tabIndex=0;pre.setAttribute("aria-label","Complete source code");
        if(!sourceOverride){const first=card.full_start_line,last=first+card.full_code.split("\n").length-1;[...pre.querySelectorAll(".code-line")].forEach((row,i)=>{if(start+i>=first&&start+i<=last)row.classList.add("relevant");});}
        $("code-body").replaceChildren(pre);
        if(!sourceOverride)showRuntimeValues(pre,card);
        if(!sourceOverride)showParsedValues(pre,card);
        if(!sourceOverride)showResolveValues(pre,card);
        if(!sourceOverride)showLearningValues(pre,card);
        if(!sourceOverride)showSourceTranslation(pre,card);
        const focus=pre.querySelector(".focused");if(focus)pre.scrollTop+=focus.getBoundingClientRect().top-pre.getBoundingClientRect().top-(pre.querySelector(".runtime-values")?12:80);
      }catch(error){if(request===codeRequest)$("code-body").textContent=`Could not load source (${error.message}). Use the original source link above.`;}
    }
    function openEvidence(id){
      const target=document.getElementById(id); if(!target)return false;
      const stage=target.closest('section.stage'); if(stage)selectStep(stage.id);
      let parent=target; while(parent){if(parent.tagName==='DETAILS')parent.open=true;parent=parent.parentElement;}
      requestAnimationFrame(()=>{target.scrollIntoView({block:'start',behavior:'smooth'});target.setAttribute('tabindex','-1');target.focus({preventScroll:true});});
      document.querySelectorAll('[data-evidence]').forEach(a=>{if(a.dataset.evidence===id)a.setAttribute('aria-current','location');else a.removeAttribute('aria-current');});
      return true;
    }
    function selectStep(id){
      if(!stepCode[id])return;activeStep=id;
      for(const section of document.querySelectorAll("#visual-pane section.stage"))section.hidden=section.id!==id;
      document.querySelectorAll(".journey a").forEach(a=>{if(a.hash==="#"+id)a.setAttribute("aria-current","step");else a.removeAttribute("aria-current");});
      const cards=[...stepCode[id]];
      if(id==="text")cards.unshift(...stepCode.parse.filter(c=>c.kind==="engine"));
      $("step-code-choices").replaceChildren();
      for(const card of cards){const button=addText($("step-code-choices"),"button",card.label);button.type="button";button.dataset.label=card.label;button.addEventListener("click",()=>showCode(card));}
      showCode(cards[0]);
      if(id==="text"&&activeGeometry)showGeometrySource(activeField!=="row");
      $("visual-pane").scrollTop=0;
    }
    function setupSplit(){
      document.querySelector(".route-guide")?.remove();document.querySelector(".code-guide")?.remove();$("source-library")?.remove();
      document.querySelectorAll(".code-reveal").forEach(el=>el.remove());
      document.querySelectorAll('a[href="#source-library"]').forEach(el=>el.remove());
      const intro=document.createElement("p");intro.className="split-intro";intro.textContent="Follow the PDF to CSV: choose a step, read its highlighted code on the left, and explore the PDF and results on the right.";
      const nav=document.querySelector(".journey");nav.before(intro);
      const split=document.createElement("div");split.id="split-workspace";
      split.innerHTML=`<aside id="code-pane" aria-label="Source code"><div class="code-toolbar"><div><span class="eyebrow">Code</span><h2 id="code-title"></h2></div><a id="code-origin" target="_blank" rel="noopener">Open original source ↗</a></div><p id="code-explanation"></p><div id="step-code-choices" role="group" aria-label="Code blocks for this step"></div><label for="code-file">Browse a complete source file</label><select id="code-file"><option value="notebook">Notebook cell for this step</option></select><small id="code-reading"></small><div id="code-body"></div></aside><div id="visual-pane" aria-label="PDF and pipeline results"></div>`;
      nav.after(split);
      document.querySelectorAll("#content section.stage").forEach(section=>$("visual-pane").append(section));
      for(const source of sourceFiles){const option=addText($("code-file"),"option",source.name);option.value=source.name;}
      $("code-file").addEventListener("change",event=>{const source=sourceFiles.find(f=>f.name===event.target.value);showCode(stepCode[activeStep].find(c=>c.kind==="notebook")||stepCode.source[0],source);});
      document.addEventListener("click",event=>{const link=event.target.closest('a[href^="#"]');if(link&&stepCode[link.hash.slice(1)]){event.preventDefault();selectStep(link.hash.slice(1));}});
      selectStep(stepCode[location.hash.slice(1)]?location.hash.slice(1):"source");
    }
    function renderGeometry(ex){
      activeGeometry=ex.geometry;$("geometry-inspector").classList.toggle("hidden",!ex.geometry);
      $("source-overlay").replaceChildren();if(!ex.geometry)return;
      $("geometry-image").src=ex.pdf_image;$("context-image").src=ex.pdf_image;
      $("geometry-title").textContent=`Transaction ${ex.spotlight_row} · page ${ex.page}`;
      $("geometry-method").textContent=`Actual parser route: ${ex.geometry.method}. Select a column to follow its text into Stage 3.`;
      $("field-controls").replaceChildren();
      for(const [name,label] of [["row","Whole row"],...ex.geometry.fields.map(f=>[f.name,f.name.replaceAll("_"," ")])]){
        const btn=addText($("field-controls"),"button",label);btn.type="button";btn.dataset.field=name;btn.addEventListener("click",()=>inspectField(name));
      }inspectField("row");
    }
    $("toggle-highlight").addEventListener("click",()=>{showHighlight=!showHighlight;$("toggle-highlight").setAttribute("aria-pressed",String(showHighlight));$("toggle-highlight").textContent=showHighlight?"Hide highlight":"Show highlight";inspectField(activeField)});
    const sections=[...document.querySelectorAll("section.stage")];
    for(const id of ["parse","resolve","audit"]){const note=document.createElement("p");note.className="lesson empty-state hidden";note.textContent="No transaction row reached this stage for this filing. The complete code remains available below.";$(id).querySelector(".stage-head").after(note);}
    sections.forEach((section,i)=>{const nav=document.createElement("div");nav.className="step-links";for(const [index,label] of [[i-1,"← Previous step"],[i+1,"Next step →"]])if(sections[index]){const link=addText(nav,"a",label);link.href="#"+sections[index].id;}section.append(nav)});
    async function start(){
      const response=await fetch("data/examples.json?v=original-review-v2");if(!response.ok)throw Error(`Index: ${response.status}`);const data=await response.json();
      renderCode(data.code);
      renderSourceLibrary(data.sources);
      setupSplit();
      const examples=data.examples,cache=new Map();
      const readable=examples.filter(e=>e.status==="parsed" && Number(e.rows)>0);
      if(!readable.length)throw Error("No filings with parsed transactions are available.");
      document.querySelector('.picker-note').textContent=`${readable.length.toLocaleString()} parsed filings available · ${examples.length.toLocaleString()} PDFs archived. This walkthrough focuses on digital PDFs with selectable text. Handwritten or scanned forms need a more complex extraction approach, such as OCR. The ${examples.length-readable.length} PDFs without extracted transactions remain in the archive.`;
      async function choose(id){
        $("random").disabled=true;$("status").className="";$("status").textContent=`Loading filing ${id}…`;
        try{let ex=cache.get(id);if(!ex){const result=await fetch(`data/filings/${id}.json?v=original-review-v2`);if(!result.ok)throw Error(`Filing ${id}: ${result.status}`);ex=await result.json();cache.set(id,ex);}
          render(ex);currentId=id;$("content").classList.remove("hidden");$("status").textContent="";
        }catch(error){$("status").className="error";$("status").textContent=`Could not load this filing. Try another random filing. ${error.message}`;}
        finally{$("random").disabled=false;}
      }
      function randomId(){const others=readable.filter(e=>e.filing_id!==currentId);const pool=others.length?others:readable;return pool[Math.floor(Math.random()*pool.length)].filing_id;}
      $("random").addEventListener("click",()=>choose(randomId()));
      const initial=new URL(location.href).searchParams.get("filing");
      await choose(readable.some(e=>e.filing_id===initial)?initial:randomId());

      $("provenance").textContent=`2025 archive · ${data.batch_pdf_count} verified PDFs · ${data.batch_transaction_count.toLocaleString()} parsed rows · ${data.parsed_filing_count} filings with rows · ${data.sample_size-data.parsed_filing_count} without parsed rows · parser ${data.source_commit.slice(0,12)}. ${data.selection}`;
    }
    document.addEventListener('click',event=>{const link=event.target.closest('[data-evidence]');if(link){event.preventDefault();if(openEvidence(link.dataset.evidence))history.replaceState(null,'','#'+link.dataset.evidence);}});
    start().then(()=>{if(!stepCode[location.hash.slice(1)])openEvidence(location.hash.slice(1));}).catch(error=>{$("status").className="error";$("status").textContent=`The walkthrough could not load: ${error.message}. Open through a web server or GitHub Pages.`});
