
    const $=id=>document.getElementById(id);
    const addText=(parent,tag,value,className)=>{const el=document.createElement(tag);el.textContent=value==null||value===""?"—":String(value);if(className)el.className=className;parent.append(el);return el};
    function fields(id,entries){const root=$(id);root.replaceChildren();for(const [label,value,raw] of entries){addText(root,"dt",label);addText(root,"dd",value,raw?"raw mono":"")}}
    let allCodeCards=[];
    let stepCode={},sourceFiles=[],activeStep="source",codeRequest=0;
    const sourceCache=new Map();
    function renderCode(code){stepCode=code;allCodeCards=Object.values(code).flat();}
    function render(ex){
      $("selected-member").textContent=ex.politician;$("selected-info").textContent=`Filing ${ex.filing_id} · ${ex.rows} parsed transactions`;$("open-pdf").href=ex.pdf_url;$("pdf-link").href=ex.pdf_url;$("pdf-image").src=ex.pdf_image;$("pdf-image").alt=`Page ${ex.page} of House PTR filing ${ex.filing_id} for ${ex.politician}`;
      $("pdf-caption").textContent=`Filing ${ex.filing_id} · page ${ex.page} of ${ex.page_count} page${ex.page_count===1?"":"s"}`;
      const summary=$("summary");summary.replaceChildren();for(const [name,value] of [["Member",ex.politician],["District",ex.state_district],["Filing",ex.filing_id],["Transactions",ex.rows],["Following row",ex.spotlight_row]]){const p=addText(summary,"span",`${name}: ${value}`,"pill");}
      const facts=$("facts");facts.replaceChildren();for(const [name,value] of [["Member",ex.politician],["District",ex.state_district],["Filing ID",ex.filing_id],["Pages",ex.page_count],["Transactions parsed",ex.rows],["Row followed below",ex.spotlight_row]]){addText(facts,"dt",name);addText(facts,"dd",value)}
      $("raw-text").textContent=(ex.raw_pdf_text||"No embedded text was extracted from this page. It may be scanned; inspect the original PDF.")+(ex.raw_text_truncated?"\n\n… page excerpt ends here; open the PDF for the full document.":"");
      renderGeometry(ex);
      const noRows=ex.status==="no_parsed_rows";
      $("no-rows").classList.toggle("hidden",!noRows);$("no-rows").textContent=ex.status_note||"";
      for(const id of ["parse","resolve","audit","csv"])$(id).classList.toggle("no-transactions",noRows);
      document.querySelectorAll(".empty-state").forEach(note=>note.classList.toggle("hidden",!noRows));
      for(const id of ["raw-fields","parsed-fields","before-fields","after-fields","audit-cards","preview"])$(id).replaceChildren();
      $("download").classList.toggle("hidden",noRows);
      const url=new URL(location.href);url.searchParams.set("filing",ex.filing_id);history.replaceState(null,"",url);
      if(noRows){$("resolver-note").textContent="No parsed row is available to trace through Stage 4. The code below is still available to study.";$("csv-description").textContent=ex.status_note;return;}
      const s=ex.stage3,r=ex.stage4,p=ex.p2;
      fields("raw-fields",[["Asset text",s.asset_raw,true],["Trade code text",s.transaction_type_raw,true],["Trade date text",s.transaction_date_raw,true],["Amount text",s.amount_raw,true],["PDF row method",s.page_parse_method]]);
      fields("parsed-fields",[["Asset",s.asset],["Ticker",s.ticker],["Trade type",s.transaction_type],["Trade date",s.transaction_date],["Amount minimum",s.amount_min],["Amount maximum",s.amount_max],["Needs review",s.needs_review]]);
      fields("before-fields",[["Asset",r.asset_v8_1],["Ticker",r.ticker_v8_1]]);
      fields("after-fields",[["Asset",r.asset_v8_2_cleaned],["Ticker",r.ticker_v8_2_cleaned],["Candidate",r.ticker_candidate_raw],["Decision",r.ticker_parse_status],["Review flag",r.needs_review]]);
      $("resolver-note").textContent=ex.changed_stage4_values?`Across this filing, ${ex.changed_stage4_values} asset or ticker cells changed in Stage 4. The old values remain in the CSV.`:"The resolver classified the candidate, but the asset and ticker text did not change in this filing. The old values are still retained for comparison.";
      const audit=$("audit-cards");audit.replaceChildren();for(const [title,value,desc] of [["Extra text in raw date?",p.raw_date_has_extra_text?"Yes":"No","Checks whether the entire original date field is only a date."],["Leading date found",p.raw_date_prefix||"None","Pulls a date from the beginning of the original text, if present."],["Does it disagree?",p.date_prefix_disagrees?"Yes — inspect PDF":"No","Compares that leading date with the normalized transaction date."]]){const card=document.createElement("div");card.className="box";addText(card,"span",title);addText(card,"strong",value);addText(card,"span",desc);audit.append(card)}
      const table=document.createElement("table"),head=document.createElement("thead"),hrow=document.createElement("tr");for(const col of ex.preview_columns)addText(hrow,"th",col.replaceAll("_"," "));head.append(hrow);table.append(head);const body=document.createElement("tbody");for(const row of ex.csv_preview){const tr=document.createElement("tr");for(const col of ex.preview_columns)addText(tr,"td",row[col]);body.append(tr)}table.append(body);$("preview").replaceChildren(table);
      $("csv-description").textContent=`${ex.rows} transaction row${ex.rows===1?"":"s"} · ${ex.csv_columns} columns · filing ${ex.filing_id}`;$("download").href=ex.csv_url;$("download").download=`house_ptr_${ex.filing_id}_p2.csv`;
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
    async function showCode(card,sourceOverride){
      const request=++codeRequest;
      $("code-title").textContent=sourceOverride?sourceOverride.name:card.source;
      $("code-explanation").textContent=sourceOverride?sourceOverride.label:card.explanation;
      $("code-origin").href=sourceOverride?sourceOverride.url:card.url;
      for(const button of $("step-code-choices").children)button.setAttribute("aria-pressed",String(button.dataset.label===card?.label&&!sourceOverride));
      const source=sourceOverride|| (card.kind!=="notebook"?sourceFiles.find(f=>f.name===card.url.split("/").pop().split("#")[0]):null);
      $("code-file").value=source?source.name:"notebook";
      $("code-reading").textContent=source?"Complete file · highlighted function and current line":"Complete notebook cell · current line highlighted";
      $("code-body").textContent="Loading source…";
      try{
        let text=card?.full_code,start=card?.full_start_line||1;
        if(source){start=1;if(!sourceCache.has(source.name)){const response=await fetch(source.text_url+"?v=split-v5");if(!response.ok)throw Error(String(response.status));sourceCache.set(source.name,await response.text());}text=sourceCache.get(source.name);}
        if(request!==codeRequest)return;
        const pre=codeBlock(text,start,sourceOverride?null:card.focus_line);pre.tabIndex=0;pre.setAttribute("aria-label","Complete source code");
        if(!sourceOverride){const first=card.full_start_line,last=first+card.full_code.split("\n").length-1;[...pre.querySelectorAll(".code-line")].forEach((row,i)=>{if(start+i>=first&&start+i<=last)row.classList.add("relevant");});}
        $("code-body").replaceChildren(pre);
        const focus=pre.querySelector(".focused");if(focus)pre.scrollTop+=focus.getBoundingClientRect().top-pre.getBoundingClientRect().top-80;
      }catch(error){if(request===codeRequest)$("code-body").textContent=`Could not load source (${error.message}). Use the original source link above.`;}
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
      const response=await fetch("data/examples.json?v=split-v5");if(!response.ok)throw Error(`Index: ${response.status}`);const data=await response.json();
      renderCode(data.code);
      renderSourceLibrary(data.sources);
      setupSplit();
      const examples=data.examples,cache=new Map();
      async function choose(id){
        $("random").disabled=true;$("status").className="";$("status").textContent=`Loading filing ${id}…`;
        try{let ex=cache.get(id);if(!ex){const result=await fetch(`data/filings/${id}.json?v=split-v5`);if(!result.ok)throw Error(`Filing ${id}: ${result.status}`);ex=await result.json();cache.set(id,ex);}
          render(ex);currentId=id;$("content").classList.remove("hidden");$("status").textContent="";
        }catch(error){$("status").className="error";$("status").textContent=`Could not load this filing. Try another random filing. ${error.message}`;}
        finally{$("random").disabled=false;}
      }
      function randomId(){const pool=examples.filter(e=>e.filing_id!==currentId);return pool[Math.floor(Math.random()*pool.length)].filing_id;}
      $("random").addEventListener("click",()=>choose(randomId()));
      const initial=new URL(location.href).searchParams.get("filing");
      await choose(examples.some(e=>e.filing_id===initial)?initial:randomId());
      $("provenance").textContent=`2025 archive · ${data.batch_pdf_count} verified PDFs · ${data.batch_transaction_count.toLocaleString()} parsed rows · ${data.parsed_filing_count} filings with rows · ${data.sample_size-data.parsed_filing_count} without parsed rows · parser ${data.source_commit.slice(0,12)}. ${data.selection}`;
    }
    start().catch(error=>{$("status").className="error";$("status").textContent=`The walkthrough could not load: ${error.message}. Open through a web server or GitHub Pages.`});
