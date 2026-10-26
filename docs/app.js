'use strict';
const $ = s => document.querySelector(s);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt = s => { if(!s)return 'Not established'; if(/^\d{4}$/.test(s))return s; if(/^\d{4}-\d{2}$/.test(s))return new Date(s+'-15T12:00:00Z').toLocaleDateString('en-GB',{month:'short',year:'numeric',timeZone:'UTC'}); return new Date(s+'T12:00:00Z').toLocaleDateString('en-GB',{day:'numeric',month:'short',year:'numeric',timeZone:'UTC'}); };
const statusKinds = {differs:'National law differs from EU text',behind:'National law has not yet caught up with the EU change',draft:'A fix is proposed but not yet law',postponed:'National law applies part of the EU change later',enacted:'A fix is enacted but not yet in force',official:'An official body says gaps remain',open:'Unclear whether national law falls short'};
const statusHelp = {differs:'The national wording says something different from the EU wording.',behind:'The EU change applies, but national law still reflects the old rule.',draft:'A draft or bill would close the gap, but it is not in force.',enacted:'A national fix exists and starts later.',postponed:'A transition or postponement delays part of the change.',official:'The Commission or a court has said so.',open:'The question is disputed.'};
const whoClass = {eu:'eu',national:'nat'};
const actName = r => (r.baseAct.match(/(?:Directive|Regulation) (?:\(EU\) )?\d+\/\d+(?:\/E[CU])?/g)||[r.baseAct]).join(' and ');
const labels = {judgment:'Court finding',commission:'Commission position',national:'National corrective act',research:'Research lead',government:'Government acknowledgment'};
let records = [], filtered = [], toastTimer, snapshot;
const filterIds = ['search','country','change','stage','sort'];
const euChangeYear = r => Number((r.correctionDate || r.celex.slice(1,5)).slice(0,4));
function safeURL(value){try{const u=new URL(value);return ['https:','http:'].includes(u.protocol)?esc(u.href):'#';}catch{return '#';}}
function notify(message){$('#toast').textContent=message;$('#toast').hidden=false;clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('#toast').hidden=true,3000);}
function paramsFromForm(){const p=new URLSearchParams();filterIds.forEach(id=>{const v=$('#'+id).value.trim();if(v && !(id==='sort'&&v==='revision'))p.set(id,v);});if($('#hide-recognized').checked)p.set('unrecognized','1');return p;}
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
 const byName=(a,b)=>a.country.localeCompare(b.country)||a.title.localeCompare(b.title);
 const byDeadline=(a,b)=>a.deadline&&b.deadline?a.deadline.localeCompare(b.deadline):a.deadline?-1:b.deadline?1:0;
 filtered.sort((a,b)=>(sort==='revision'?euChangeYear(b)-euChangeYear(a)||b.evidenceDate.localeCompare(a.evidenceDate):sort==='oldest'?a.evidenceDate.localeCompare(b.evidenceDate):sort==='deadline'?byDeadline(a,b):sort==='newest'?b.evidenceDate.localeCompare(a.evidenceDate):0)||byName(a,b));
 $('#result-count').textContent=filtered.length===records.length?`${records.length} cases`:`${filtered.length} of ${records.length} cases`;
 refreshFacets();
 $('#results').innerHTML=filtered.length?filtered.map(r=>`<article class="record"><div><div class="kicker"><b>${esc(r.country)}</b> · ${esc(actName(r))} · ${esc(r.topic)}</div><h2><a href="#case/${encodeURIComponent(r.id)}">${esc(r.title)}</a></h2><p>${esc(r.summary)}</p><div class="act-chain">EU change: ${esc(r.amendingAct)}</div></div><div class="record-aside"><div class="stage">${esc(statusKinds[r.statusKind]||r.statusLabel)}</div>${r.recordKind==='lead'?'':`<div class="date">${esc(r.badgeLabel||labels[r.stage])}</div>`}<div class="date">As of ${fmt(r.evidenceDate)}</div>${sort==='deadline'?`<div class="date">${r.deadline?`Deadline ${fmt(r.deadline)}`:'No deadline'}</div>`:''}${r.priorRecognition==='not-located'?'<span class="recognition candidate">No prior recognition located</span>':'<span class="recognition known">Previously recognized</span>'}</div></article>`).join(''):`<div class="empty"><h3>No matching findings</h3><p>Try a broader search or clear the filters to see all documented cases.</p><button class="button" id="empty-reset">Clear filters</button></div>`;
 $('#empty-reset')?.addEventListener('click',resetFilters);
 if(updateURL){const p=paramsFromForm();history.replaceState(null,'',location.pathname+(p.size?'?'+p:'')+location.hash);}
}
function resetFilters(){filterIds.forEach(id=>$('#'+id).value=id==='sort'?'revision':'');$('#hide-recognized').checked=false;applyFilters();}
function coverage(){
 const count=f=>{const m={};records.forEach(r=>{const k=f(r);m[k]=(m[k]||0)+1});return Object.entries(m).sort((x,y)=>y[1]-x[1]||x[0].localeCompare(y[0]))};
 const acts=count(actName), countries=[...new Set(records.map(r=>r.country))].sort(), code=Object.fromEntries(records.map(r=>[r.country,r.countryCode])), topic={};
 records.forEach(r=>{topic[actName(r)]??=r.topic});
 const cell=(act,c)=>{const l=records.filter(r=>actName(r)===act&&r.country===c);if(!l.length)return '<td></td>';return `<td><a class="cov-dot" href="${l.length===1?'#case/'+encodeURIComponent(l[0].id):'?country='+encodeURIComponent(c)}" aria-label="${esc(c)}: ${l.length} case${l.length>1?'s':''} on ${esc(act)}" title="${esc(c)}"><i></i></a></td>`};
 $('#coverage-page').innerHTML=`<div class="doc"><div class="doc-top"><a class="back" href="#">← Back to findings</a></div><h1>Coverage</h1><p class="doc-lead">${records.length} cases across ${countries.length} of the 27 Member States and ${acts.length} directives. A dot means a case is listed.</p><p class="doc-note">This is a sample, not a complete review. A country or directive that is missing here has not been examined; that does not mean it complies.</p><h2>Which directives, in which countries</h2><div class="cov-scroll"><table class="cov-mat"><thead><tr><th class="l">Directive · topic</th>${countries.map(c=>`<th><abbr title="${esc(c)}">${esc(code[c])}</abbr></th>`).join('')}<th class="n">Cases</th></tr></thead><tbody>${acts.map(([act,n])=>`<tr><td class="l">${esc(act.replace(/^Directive\s+(\(EU\)\s*)?/,''))} <span>· ${esc(topic[act])}</span></td>${countries.map(c=>cell(act,c)).join('')}<td class="n">${n}</td></tr>`).join('')}</tbody></table></div><div id="systematic-review"></div></div>`;
 window.renderSystematicCoverage?.();
}
function method(){
 const ex=records.find(r=>r.id==='hu-bank-capital-leverage-trigger')||records[0];
 const key=[['Country · EU act · topic','Whose law, which directive, and what area.'],['Status','One of seven plain labels, listed below.'],['Noticed before?','Whether an official source or published analysis already pointed out this specific difference.'],['Timeline','Who acted at each point: the EU, the country, a court, the Commission, our own check, or commentary.'],['Side by side','The EU text on the left, national law on the right, with the key wording quoted.'],['Does it matter?','What the difference means on paper, and what we have not established.']];
 const steps=[['Pick an EU change','An amendment, correction, recast or replacement of a directive.'],['Compare with national law','We read the national text in force and compare it with the changed EU provision.'],['Look for explanations','Later national fixes, drafts, Commission or court steps, and stricter rules that may be lawful.'],['Check independently','A separate AI research agent challenges the comparison before a case is added. This does not replace legal advice.']];
 $('#method-page').innerHTML=`<div class="doc"><div class="doc-top"><a class="back" href="#">← Back to findings</a></div><h1>Method</h1><p class="doc-lead">EU Directive Drift lists cases where a country’s law does not match an EU directive after the directive was changed. Each case sets the EU text beside the national text, with sources.</p><h2>How to read a case</h2><div class="doc-2col"><div class="doc-ex" aria-hidden="true">${caseHtml(ex,true)}</div><ol class="doc-key">${key.map(([t,d],i)=>`<li><span class="mk">${i+1}</span><span><b>${t}${t.endsWith('?')?'':'.'}</b> ${d}</span></li>`).join('')}</ol></div><h2>The seven statuses</h2><dl class="doc-dl">${['differs','behind','draft','enacted','postponed','official','open'].map(k=>`<dt>${esc(statusKinds[k])}</dt><dd>${esc(statusHelp[k])}</dd>`).join('')}</dl><h2>How we find and check cases</h2><ol class="doc-steps">${steps.map(([t,d])=>`<li><b>${t}</b>${d}</li>`).join('')}</ol><h2>What this site does not claim</h2><ul class="doc-no"><li>A difference between texts is not automatically a breach. A stricter national rule can be lawful.</li><li>The cases are a sample, not a review of every country or directive. See <a href="#coverage">Coverage</a>.</li><li>Each case reflects the day we checked it; the timeline shows that date.</li></ul></div>`;
 const e=$('#method-page .doc-ex'), mk=(el,n)=>el&&el.insertAdjacentHTML('beforeend',`<span class="mk">${n}</span>`);
 mk(e.querySelector('.kicker'),1);mk(e.querySelector('.case-facts div:nth-child(1) dt'),2);mk(e.querySelector('.case-facts div:nth-child(2) dt'),3);mk(e.querySelector('.case-chain li:nth-child(2) time'),4);mk(e.querySelector('.case-col.eu .label'),5);mk([...e.querySelectorAll('h2')].find(x=>x.textContent==='Does it matter?'),6);
}
function caseHtml(r,ex){
 const c=r.comparison, ns=r.noveltySearch;
 const quote=(label,text)=>`<div class="case-quote"><span>${esc(label)}</span>${esc(text)}</div>`;
 const points=[...(r.baseActPublished?[{date:r.baseActPublished,event:`${r.baseAct} published.`,who:'eu'}]:[]),...r.timeline,...(r.timeline.some(t=>t.date===r.evidenceDate)?[]:[{date:r.evidenceDate,event:`${r.evidenceLabel||'Checked'}.`,who:'check'}])].sort((a,b)=>a.date.localeCompare(b.date)), whoLabel={eu:'EU',national:r.country,court:'Court',commission:'Commission',check:'Our check',commentary:'Commentary'};
 return `<div class="case">${ex?'':`<div class="case-top"><a class="back" href="#">← Back to findings</a><div class="case-actions"><button type="button" id="copy-link" class="text-button">Copy link</button></div></div>`}<div class="kicker"><b>${esc(r.country)}</b> · ${esc(actName(r))} · ${esc(r.topic)}</div><h1>${esc(r.title)}</h1><p class="case-summary">${esc(r.summary)}</p><div class="case-side"><dl class="case-facts"><div><dt>Status</dt><dd>${statusKinds[r.statusKind]?esc(statusKinds[r.statusKind])+(r.statusDetail?`<span class="case-detail">${esc(r.statusDetail)}</span>`:''):esc(r.statusLabel)}</dd></div><div><dt>Noticed before?</dt><dd>${r.priorRecognition==='not-located'?'<span class="case-dot"></span>Not that we found':esc(r.recognizedBy.join(', ')||'Previously recognized')}</dd></div></dl><div><ol class="case-chain" aria-label="Timeline">${points.map(t=>`<li${t.date===r.evidenceDate?' class="now"':t.date>r.evidenceDate?' class="future"':''}><time datetime="${esc(t.date)}">${fmt(t.date)}</time>${whoLabel[t.who]?`<span class="case-who ${whoClass[t.who]||''}">${esc(whoLabel[t.who])}</span>`:'<span></span>'}<span class="case-ev">${esc(t.event)}</span></li>`).join('')}</ol>${r.updateType==='Corrigendum'&&!ex?'<p class="case-aside">An EU correction fixes a mistake in the published wording of an EU law. It does not change national law and sets no new deadline.</p>':''}</div></div><div class="case-gap"><div class="case-col eu"><div class="label">EU · ${esc(r.amendingAct)}</div>${c?quote(c.afterLabel||'Later rule',c.after):''}${ex?'':`<p>${esc(r.euChange)}</p><small>Updates ${esc(r.baseAct)} · ${esc(r.provisions)}</small>`}</div><div class="case-col national"><div class="label">${esc(r.country)} · national law</div>${c?quote(c.beforeLabel||'Earlier national rule',c.before):''}${ex?'':`<p>${esc(r.nationalGap)}</p><small>${esc(r.nationalLaw)}</small>`}</div></div>${!ex&&c&&c.note?`<p class="case-note">${esc(c.note)}</p>`:''}${r.consequence?`<h2>Does it matter?</h2><p class="case-text">${esc(r.consequence)}</p>`:''}${ex?'':`<h2>Sources</h2><table class="case-sources"><thead><tr><th>Source</th><th>Used for</th><th>Pinpoint</th></tr></thead><tbody>${r.sources.map(s=>`<tr><td><a href="${safeURL(s.url)}" target="_blank" rel="noopener noreferrer">${esc(s.title)} ↗</a></td><td>${esc(s.role)}</td><td>${esc(s.locator||'')}</td></tr>`).join('')}</tbody></table><details class="case-more"><summary>Limits and checks</summary><div><h3>Limits of this finding</h3><p>${esc(r.caveat)}</p><h3>Prior recognition</h3><p>${esc(r.recognitionNote)}</p>${ns?`<h3>Search for earlier recognition</h3><p>${fmt(ns.date)} · ${esc(ns.method)}</p>`:''}<h3>Independent check</h3><p>${esc(r.review)}</p></div></details>`}</div>`;
}
function detail(id){
 const r=records.find(x=>x.id===id), el=$('#detail-page');
 if(!r){el.innerHTML='<a class="back" href="#">← Back to findings</a><h1>Outside the open-issues catalogue</h1><p>This record is not listed in the current catalogue. Fully resolved cases are excluded.</p>';return;}
 document.title=`${r.country}: ${r.amendingAct} — EU Directive Drift`;
 el.innerHTML=caseHtml(r);
 $('#copy-link').addEventListener('click',async()=>{try{await navigator.clipboard.writeText(location.href);notify('Finding link copied');}catch{notify('Copy the finding URL from your address bar');}});
}
function route(){
 const hash=location.hash; if(hash==='#main'){$('#main').focus();return;} const type=hash.startsWith('#case/')?'detail':hash==='#method'?'method':hash==='#coverage'?'coverage':'catalogue';
 ['catalogue','detail','method','coverage'].forEach(t=>$('#'+t+'-page').hidden=t!==type);
 document.querySelectorAll('[data-page]').forEach(a=>{const active=a.dataset.page===type;a.classList.toggle('active',active);if(active)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');});
 document.title='EU Directive Drift — National implementation gaps';
 if(type==='detail'){try{detail(decodeURIComponent(hash.slice(6)));}catch{detail('');}}
 window.scrollTo(0,0);$('#main').focus({preventScroll:true});
}
async function init(){
 window.addEventListener('hashchange',route);
 try{
 const res=await fetch('data/findings.json');if(!res.ok)throw new Error('Data unavailable');const data=await res.json();records=data.findings;snapshot=data.snapshot;
 const countries=[...new Set(records.map(r=>r.country))].sort();countries.forEach(c=>$('#country').add(new Option(c,c)));
 const params=new URLSearchParams(location.search);filterIds.forEach(id=>{if(params.has(id))$('#'+id).value=params.get(id);});if(!$('#sort').value)$('#sort').value='revision';$('#hide-recognized').checked=params.get('unrecognized')==='1';
 filterIds.forEach(id=>$('#'+id).addEventListener(id==='search'?'input':'change',()=>applyFilters()));$('#hide-recognized').addEventListener('change',()=>applyFilters());
 $('#filters').addEventListener('submit',e=>e.preventDefault());$('#reset').addEventListener('click',resetFilters);
 applyFilters(false);coverage();method();route();
 }catch(err){$('#load-error').hidden=false;$('#result-count').textContent='Catalogue unavailable';$('#coverage-page').innerHTML=$('#method-page').innerHTML='<a class="back" href="#">← Back to findings</a><h1>Page unavailable</h1><p>Reload the local website to try loading the dataset again.</p>';route();console.error(err);}
}
init();
