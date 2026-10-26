'use strict';
const $ = s => document.querySelector(s);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt = s => { if(!s)return 'Not established'; if(/^\d{4}$/.test(s))return s; if(/^\d{4}-\d{2}$/.test(s))return new Date(s+'-15T12:00:00Z').toLocaleDateString('en-GB',{month:'short',year:'numeric',timeZone:'UTC'}); return new Date(s+'T12:00:00Z').toLocaleDateString('en-GB',{day:'numeric',month:'short',year:'numeric',timeZone:'UTC'}); };
const statusKinds = {differs:'National law differs from EU text',behind:'National law has not yet caught up with the EU change',draft:'A fix is proposed but not yet law',postponed:'National law applies part of the EU change later',enacted:'A fix is enacted but not yet in force',official:'An official body says gaps remain',open:'Unclear whether national law falls short'};
const whoClass = {eu:'eu',national:'nat'};
const actName = r => (r.baseAct.match(/(?:Directive|Regulation) (?:\(EU\) )?\d+\/\d+(?:\/E[CU])?/g)||[r.baseAct]).join(' and ');
const labels = {judgment:'Court finding',commission:'Commission position',national:'National corrective act',research:'Research lead',government:'Government acknowledgment'};
let records = [], filtered = [], toastTimer, snapshot;
const filterIds = ['search','country','change','stage','sort'];
const euChangeYear = r => Number((r.correctionDate || r.celex.slice(1,5)).slice(0,4));
function safeURL(value){try{const u=new URL(value);return ['https:','http:'].includes(u.protocol)?esc(u.href):'#';}catch{return '#';}}
function notify(message){$('#toast').textContent=message;$('#toast').hidden=false;clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('#toast').hidden=true,3000);}
function paramsFromForm(){const p=new URLSearchParams();filterIds.forEach(id=>{const v=$('#'+id).value.trim();if(v && !(id==='sort'&&v==='discovery'))p.set(id,v);});if($('#hide-recognized').checked)p.set('unrecognized','1');return p;}
const facetField={country:r=>r.country,change:r=>r.updateType,stage:r=>r.stage};
function matches(r,skip){
 const q=$('#search').value.trim().toLocaleLowerCase();
 return (skip==='country'||!$('#country').value||r.country===$('#country').value)&&(skip==='stage'||!$('#stage').value||r.stage===$('#stage').value)&&(skip==='change'||!$('#change').value||r.updateType===$('#change').value)&&(!$('#hide-recognized').checked||r.priorRecognition==='not-located')&&(!q||[r.title,r.country,r.topic,r.baseAct,r.amendingAct,r.euChange,r.nationalGap,r.provisions,r.nationalLaw,r.resolution,r.statusLabel].join(' ').toLocaleLowerCase().includes(q));
}
function refreshFacets(){
 Object.entries(facetField).forEach(([id,get])=>{const sel=$('#'+id),pool=records.filter(r=>matches(r,id));
  [...sel.options].forEach(o=>{if(!o.value)return;o.dataset.label??=o.textContent;const n=pool.filter(r=>get(r)===o.value).length;o.textContent=`${o.dataset.label} (${n})`;o.hidden=o.disabled=!n&&o.value!==sel.value;});});
}
function applyFilters(updateURL=true){
 filtered=records.filter(r=>matches(r));
 const sort=$('#sort').value;
 filtered.sort((a,b)=>sort==='discovery'?(Number(a.priorRecognition==='recognized')-Number(b.priorRecognition==='recognized')||euChangeYear(b)-euChangeYear(a)||b.evidenceDate.localeCompare(a.evidenceDate)||a.country.localeCompare(b.country)):sort==='revision'?euChangeYear(b)-euChangeYear(a)||b.evidenceDate.localeCompare(a.evidenceDate)||a.country.localeCompare(b.country):sort==='country'?a.country.localeCompare(b.country)||a.title.localeCompare(b.title):sort==='oldest'?a.evidenceDate.localeCompare(b.evidenceDate):sort==='deadline'?(b.deadline||'').localeCompare(a.deadline||''):b.evidenceDate.localeCompare(a.evidenceDate));
 $('#result-count').textContent=`${filtered.length} of ${records.length} records`;
 refreshFacets();
 $('#results').innerHTML=filtered.length?filtered.map(r=>`<article class="record"><div><div class="kicker"><b>${esc(r.country)}</b> · ${esc(actName(r))} · ${esc(r.topic)}</div><h2><a href="#case/${encodeURIComponent(r.id)}">${esc(r.title)}</a></h2><p>${esc(r.summary)}</p><div class="act-chain">EU change: ${esc(r.amendingAct)}</div></div><div class="record-aside">${r.recordKind==='lead'?'':`<div class="stage">${esc(r.badgeLabel||labels[r.stage])}</div>`}<div class="date">${fmt(r.evidenceDate)}</div>${r.priorRecognition==='not-located'?'<span class="recognition candidate">No prior recognition located</span>':'<span class="recognition known">Previously recognized</span>'}</div></article>`).join(''):`<div class="empty"><h3>No matching findings</h3><p>Try a broader search or clear the filters to see all documented cases.</p><button class="button" id="empty-reset">Clear filters</button></div>`;
 $('#empty-reset')?.addEventListener('click',resetFilters);
 if(updateURL){const p=paramsFromForm();history.replaceState(null,'',location.pathname+(p.size?'?'+p:'')+location.hash);}
}
function resetFilters(){filterIds.forEach(id=>$('#'+id).value=id==='sort'?'discovery':'');$('#hide-recognized').checked=false;applyFilters();}
function coverage(){
 const countries=[...new Set(records.map(r=>r.country))].sort();
 $('#coverage-page').innerHTML=`<a class="back" href="#">← Back to findings</a><div class="eyebrow">A PURPOSEFUL SAMPLE</div><h1>Evidence has boundaries.<br>So does this catalogue.</h1><p class="lead">${records.length} records across ${countries.length} Member States. These counts describe this pilot’s research sample, not the prevalence of missed EU updates.</p><div class="caveat"><strong>No country has been comprehensively reviewed.</strong><p>Absence from the catalogue means unexamined, rather than compliant. Multiple records can concern the same amendment or Member State.</p></div><table class="coverage-table"><caption class="eyebrow">RECORDS BY MEMBER STATE</caption><thead><tr><th>Member State</th><th>Records</th><th>EU updates represented</th></tr></thead><tbody>${countries.map(c=>{const rr=records.filter(r=>r.country===c);return `<tr><td><a href="?country=${encodeURIComponent(c)}">${esc(c)}</a></td><td>${rr.length}</td><td>${[...new Set(rr.map(r=>r.amendingAct))].map(esc).join(', ')}</td></tr>`;}).join('')}</tbody></table><h2>What was reviewed</h2><p>The pilot uses independently researched candidates and cross-checks of official EU and national materials. It includes unresolved implementation concerns, national acknowledgments of unreflected updates, and qualified current text mismatches. Cases documented as fully resolved are excluded.</p><h2>Recent research focus</h2><p>The latest pass examined bank-capital and renewable-energy corrections, labour-migration rules, environmental and trafficking offences, civil-justice safeguards and consumer amendments. Earlier work also covered energy markets, financial services, workplace safeguards, tax reporting, buildings, toys and restricted substances. Each accepted case was checked against the changed EU provision and a dated national text. These searches are a sample, not a complete review of those frameworks.</p><h2>What remains open</h2><p>Formal infringement closure, the full effect of national law in force today, enforcement practice and a complete article-by-article comparison have not been verified for every record. Case-specific limits appear alongside each finding.</p><h2>Research date versus evidence date</h2><p>The research snapshot is ${fmt(snapshot)}. The evidence date attached to a case identifies the judgment, official position or national-text check supporting the record. It is not a claim that the same gap persists at the research date.</p><h2>What the data contains</h2><p>The dataset contains links and concise findings rather than a duplicate archive of legislation. It is a starting point for further investigation and is manually maintained in this MVP.</p>`;
}
function detail(id){
 const r=records.find(x=>x.id===id), el=$('#detail-page');
 if(!r){el.innerHTML='<a class="back" href="#">← Back to findings</a><h1>Outside the open-issues catalogue</h1><p>This record is not listed in the current catalogue. Fully resolved cases are excluded.</p>';return;}
 document.title=`${r.country}: ${r.amendingAct} — EU Update Chain`;
 const c=r.comparison, ns=r.noveltySearch;
 const quote=(label,text)=>`<div class="case-quote"><span>${esc(label)}</span>${esc(text)}</div>`;
 const points=[...(r.baseActPublished?[{date:r.baseActPublished,event:`${r.baseAct} published.`,who:'eu'}]:[]),...r.timeline,...(r.timeline.some(t=>t.date===r.evidenceDate)?[]:[{date:r.evidenceDate,event:`${r.evidenceLabel||'Checked'}.`,who:'check'}])].sort((a,b)=>a.date.localeCompare(b.date)), whoLabel={eu:'EU',national:r.country,court:'Court',commission:'Commission',check:'Our check',commentary:'Commentary'};
  el.innerHTML=`<div class="case"><div class="case-top"><a class="back" href="#">← Back to findings</a><div class="case-actions"><button type="button" id="copy-link" class="text-button">Copy link</button></div></div><div class="kicker"><b>${esc(r.country)}</b> · ${esc(actName(r))} · ${esc(r.topic)}</div><h1>${esc(r.title)}</h1><p class="case-summary">${esc(r.summary)}</p><div class="case-side"><dl class="case-facts"><div><dt>Status</dt><dd>${statusKinds[r.statusKind]?esc(statusKinds[r.statusKind])+(r.statusDetail?`<span class="case-detail">${esc(r.statusDetail)}</span>`:''):esc(r.statusLabel)}</dd></div><div><dt>Noticed before?</dt><dd>${r.priorRecognition==='not-located'?'<span class="case-dot"></span>Not that we found':esc(r.recognizedBy.join(', ')||'Previously recognized')}</dd></div></dl><div><ol class="case-chain" aria-label="Timeline">${points.map(t=>`<li${t.date===r.evidenceDate?' class="now"':t.date>r.evidenceDate?' class="future"':''}><time datetime="${esc(t.date)}">${fmt(t.date)}</time>${whoLabel[t.who]?`<span class="case-who ${whoClass[t.who]||''}">${esc(whoLabel[t.who])}</span>`:'<span></span>'}<span class="case-ev">${esc(t.event)}</span></li>`).join('')}</ol>${r.updateType==='Corrigendum'?'<p class="case-aside">An EU correction fixes a mistake in the published wording of an EU law. It does not change national law and sets no new deadline.</p>':''}</div></div><div class="case-gap"><div class="case-col eu"><div class="label">EU · ${esc(r.amendingAct)}</div>${c?quote(c.afterLabel||'Later rule',c.after):''}<p>${esc(r.euChange)}</p><small>Updates ${esc(r.baseAct)} · ${esc(r.provisions)}</small></div><div class="case-col national"><div class="label">${esc(r.country)} · national law</div>${c?quote(c.beforeLabel||'Earlier national rule',c.before):''}<p>${esc(r.nationalGap)}</p><small>${esc(r.nationalLaw)}</small></div></div>${c&&c.note?`<p class="case-note">${esc(c.note)}</p>`:''}${r.consequence?`<h2>Does it matter?</h2><p class="case-text">${esc(r.consequence)}</p>`:''}<h2>What has happened since?</h2><p class="case-text">${esc(r.resolution)}</p><h2>Sources</h2><table class="case-sources"><tbody>${r.sources.map((s,i)=>`<tr><td>${i+1}</td><td><a href="${safeURL(s.url)}" target="_blank" rel="noopener noreferrer">${esc(s.title)} ↗</a></td><td>${esc(s.role)}</td><td>${esc(s.locator||'')}</td></tr>`).join('')}</tbody></table><details class="case-more"><summary>Limits and checks</summary><div><h3>Limits of this finding</h3><p>${esc(r.caveat)}</p><h3>Prior recognition</h3><p>${esc(r.recognitionNote)}</p>${ns?`<h3>Search for earlier recognition</h3><p>${fmt(ns.date)} · ${esc(ns.method)}</p>`:''}<h3>Independent check</h3><p>${esc(r.review)}</p></div></details></div>`;
 $('#copy-link').addEventListener('click',async()=>{try{await navigator.clipboard.writeText(location.href);notify('Finding link copied');}catch{notify('Copy the finding URL from your address bar');}});
}
function route(){
 const hash=location.hash; if(hash==='#main'){$('#main').focus();return;} const type=hash.startsWith('#case/')?'detail':hash==='#method'?'method':hash==='#coverage'?'coverage':'catalogue';
 ['catalogue','detail','method','coverage'].forEach(t=>$('#'+t+'-page').hidden=t!==type);
 document.querySelectorAll('[data-page]').forEach(a=>{const active=a.dataset.page===type;a.classList.toggle('active',active);if(active)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');});
 document.title='EU Update Chain — National implementation gaps';
 if(type==='detail'){try{detail(decodeURIComponent(hash.slice(6)));}catch{detail('');}}
 window.scrollTo(0,0);$('#main').focus({preventScroll:true});
}
async function init(){
 window.addEventListener('hashchange',route);
 try{
 const res=await fetch('data/findings.json');if(!res.ok)throw new Error('Data unavailable');const data=await res.json();records=data.findings;snapshot=data.snapshot;
 const countries=[...new Set(records.map(r=>r.country))].sort();countries.forEach(c=>$('#country').add(new Option(c,c)));
 const updates=new Set(records.map(r=>r.celex));
 $('#stats').textContent=`${records.length} records · ${countries.length} Member States · ${updates.size} EU changes`;
 const params=new URLSearchParams(location.search);filterIds.forEach(id=>{if(params.has(id))$('#'+id).value=params.get(id);});if(!$('#sort').value)$('#sort').value='discovery';$('#hide-recognized').checked=params.get('unrecognized')==='1';
 filterIds.forEach(id=>$('#'+id).addEventListener(id==='search'?'input':'change',()=>applyFilters()));$('#hide-recognized').addEventListener('change',()=>applyFilters());
 $('#filters').addEventListener('submit',e=>e.preventDefault());$('#reset').addEventListener('click',resetFilters);
 applyFilters(false);coverage();route();
 }catch(err){$('#load-error').hidden=false;$('#result-count').textContent='Catalogue unavailable';$('#coverage-page').innerHTML='<a class="back" href="#">← Back to findings</a><h1>Coverage data unavailable</h1><p>Reload the local website to try loading the dataset again.</p>';route();console.error(err);}
}
init();
