
    const $=id=>document.getElementById(id);
    const addText=(parent,tag,value,className)=>{const el=document.createElement(tag);el.textContent=value==null||value===""?"—":String(value);if(className)el.className=className;parent.append(el);return el};
    function fields(id,entries){const root=$(id);root.replaceChildren();for(const [label,value,raw] of entries){addText(root,"dt",label);addText(root,"dd",value,raw?"raw mono":"")}}
    function renderCode(code){
      for(const [stage,snippets] of Object.entries(code)){
        const details=$(`code-${stage}`),host=details?.querySelector(".code-sources");
        if(!host)continue;
        details.open=true;
        const cellCount=snippets.filter(s=>s.kind==="notebook").length;
        details.querySelector("summary").textContent=`Code for this step · ${cellCount?`${cellCount} Colab section${cellCount===1?"":"s"}`:"Parser and PDF source code"}${cellCount&&snippets.some(s=>s.kind==="engine")?" + parser/source code":""}`;
        host.replaceChildren();
        for(const item of snippets){
          const article=document.createElement("article");article.className="source-snippet";
          const head=document.createElement("header");
          const title=document.createElement("strong");title.textContent=item.label;
          const link=document.createElement("a");link.href=item.url;link.target="_blank";link.rel="noopener";link.textContent=`Open ${item.source} ↗`;
          head.append(title,link);article.append(head);
          const tag=document.createElement("span");tag.className="code-tag";tag.textContent=item.kind==="notebook"?"Original Colab code · complete cell or contiguous section":"Under the hood · exact excerpt outside the Colab notebook";article.append(tag);
          const explanation=document.createElement("p");explanation.textContent=item.explanation;article.append(explanation);
          const flow=document.createElement("div");flow.className="file-flow";for(const [name,value] of [["Reads",item.reads],["Produces",item.makes]]){const badge=document.createElement("span");const bold=document.createElement("b");bold.textContent=name+": ";badge.append(bold,document.createTextNode(value));flow.append(badge);if(name==="Reads")flow.append(document.createTextNode("→"))}article.append(flow);
          article.append(codeBlock(item.focus_code,item.focus_line,item.focus_line));
          const full=document.createElement("details");full.className="full-block";
          addText(full,"summary","See this line in the complete code block");
          full.append(codeBlock(item.full_code,item.full_start_line,item.focus_line));article.append(full);
          full.addEventListener("toggle",()=>{if(full.open){const pre=full.querySelector("pre"),focus=pre.querySelector(".focused");if(focus)pre.scrollTop+=focus.getBoundingClientRect().top-pre.getBoundingClientRect().top-80;}});
          host.append(article);
        }
      }
    }
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
    const stepObserver=new IntersectionObserver(entries=>{for(const entry of entries)if(entry.isIntersecting){document.querySelectorAll(".journey a").forEach(link=>{if(link.hash==="#"+entry.target.id)link.setAttribute("aria-current","step");else link.removeAttribute("aria-current")})}},{rootMargin:"-10% 0px -70% 0px"});
    sections.forEach(section=>stepObserver.observe(section));
    async function start(){
      const response=await fetch("data/examples.json?v=geometry-v3");if(!response.ok)throw Error(`Index: ${response.status}`);const data=await response.json();
      renderCode(data.code);
      $("expand-code").addEventListener("click",()=>document.querySelectorAll(".code-reveal,.full-block").forEach(d=>d.open=true));
      $("collapse-code").addEventListener("click",()=>document.querySelectorAll(".code-reveal,.full-block").forEach(d=>d.open=false));
      const examples=data.examples,cache=new Map();
      async function choose(id){
        $("random").disabled=true;$("status").className="";$("status").textContent=`Loading filing ${id}…`;
        try{let ex=cache.get(id);if(!ex){const result=await fetch(`data/filings/${id}.json?v=geometry-v3`);if(!result.ok)throw Error(`Filing ${id}: ${result.status}`);ex=await result.json();cache.set(id,ex);}
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
