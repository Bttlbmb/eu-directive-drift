'use strict';
(() => {
 let ledger;
 const html = value => String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
 const statusName = {complete:'Assessment complete', 'in-progress':'Partly reviewed', pending:'Not yet assessed'};
 const prose = value => typeof value === 'string' ? value : value ? Object.entries(value).filter(([key]) => !['id','changeId','evidenceIndex','sourceCelex'].includes(key)).map(([,text]) => prose(text)).filter(Boolean).join(' · ') : '';
 const list = value => Array.isArray(value) ? value : value ? [value] : [];
 const sentence = value => String(value || '').replace(/([a-z])([A-Z])/g,'$1 $2').replace(/[-_]/g,' ');
 const groupName = group => group.change || group.rule || group.delta || group.meaning || group.description || group.title || 'Changed obligation';
 const locator = group => group.euLocator || group.locator || group.provision || group.provisions || '';
 const groupAssessment = (review, id) => {
  const match = (review.provisionChecks || review.changeAssessments || []).find(item => item.changeId === id || item.id === id);
  const value = match || review.changes?.[id];
  if (!value || value === 'pending') return 'Comparison still pending.';
  if (typeof value === 'object') return prose(value);
  const known = {'express-correct-national-wording-read':'Matching national wording read.', 'current-provision-supported':'Current provision supports the changed obligation.', 'not-applicable-language-specific-correction':'No separate national amendment needed for this correction.', 'not-applicable':'No national legislative obligation for this item.'};
  return known[value] || sentence(value);
 };
 const sources = review => ['currentNationalEvidence','evidence','nationalSources'].flatMap(key => review[key] || []).filter(item => item && typeof item === 'object');
 const sourceHTML = item => {
  const links = [...new Set([...(item.urls || []), item.url].filter(url => typeof url === 'string' && /^https?:\/\//.test(url)))];
  return `<li>${links.map((url,index) => `<a href="${html(url)}" target="_blank" rel="noopener noreferrer">${html(item.title || (index ? 'Additional source' : 'Official source'))} ↗</a>`).join(' · ')}<p>${html([item.locator,item.assessment,item.readScope,item.read,item.role].filter(Boolean).join(' '))}</p></li>`;
 };
 window.renderSystematicCoverage = () => {
  const mount = document.querySelector('#systematic-review');
  if (!mount || !ledger) return;
  const counts = ledger.counts;
  mount.innerHTML = `<section class="systematic" aria-labelledby="systematic-title"><div class="eyebrow">SYSTEMATIC REVIEW · IN PROGRESS</div><h2 id="systematic-title">The 25 shortest directives</h2><p>Selected from ${ledger.poolCount} previously examined EU acts, ranking each individual directive—including amendments—by the length of its original official English text, including annexes.</p><div class="systematic-counts"><span><b>${counts.complete}</b> assessments complete</span><span><b>${counts.inProgress}</b> partly reviewed</span><span><b>${counts.countryActPairs - counts.complete - counts.inProgress}</b> not yet assessed</span></div><progress max="${counts.countryActPairs}" value="${counts.complete}" aria-label="Completed country–directive assessments"></progress><p class="systematic-note">${counts.countryActPairs} country–directive assessments cover all 27 Member States. “Complete” means all applicable changed obligations have been assessed within the stated scope; the conclusion can still be uncertain. It does not mean the country complies. A notification alone never completes a review. Independent challenges remain ongoing.</p><details><summary>Scope and selection</summary><p>${html(ledger.scope)}</p><p>Original texts include recitals, provisions, annexes and notes. Incomplete older HTML was checked against the complete official PDF. Standalone corrections were not ranked as separate directives. The ranking and the cutoff were checked independently.</p><p>Actual enforcement and administrative reporting performance are outside this formal-law comparison unless expressly examined. Completed rows retain their own source dates and limitations.</p><a href="data/systematic.json" download>Download the compact review ledger</a></details><div class="systematic-table-wrap"><table class="systematic-acts"><caption>Review progress by directive</caption><thead><tr><th>Directive</th><th>Original words</th><th>Complete / 27</th><th>Partly reviewed</th></tr></thead><tbody>${ledger.acts.map(act => `<tr><th><button class="text-button" type="button" data-inspect-act="${html(act.celex)}">${html(act.id)} · ${html(act.title)}</button></th><td>${act.wordCount.toLocaleString('en-GB')}</td><td>${act.countries.filter(cell => cell.status === 'complete').length}</td><td>${act.countries.filter(cell => cell.status === 'in-progress').length}</td></tr>`).join('')}</tbody></table></div><h3>Inspect a comparison</h3><div class="systematic-selects"><label>Directive<select id="review-act">${ledger.acts.map(act => `<option value="${html(act.celex)}">${html(act.id)} · ${html(act.title)}</option>`).join('')}</select></label><label>Member State<select id="review-country">${ledger.acts[0].countries.map(cell => `<option value="${cell.countryCode}">${html(cell.country)}</option>`).join('')}</select></label></div><div id="systematic-comparison" aria-live="polite"></div></section>`;
  const actSelect = mount.querySelector('#review-act'), countrySelect = mount.querySelector('#review-country');
  const inspect = () => {
   const act = ledger.acts.find(item => item.celex === actSelect.value), cell = act.countries.find(item => item.countryCode === countrySelect.value), review = cell.review || {};
   const evidence = sources(review);
   const note = review.conclusion || review.legalConclusion || review.assessmentScope || review.reviewScope;
   const limits = [review.currentness,...list(review.limitations),...list(review.uncertainties),...list(review.blockers),...list(review.completionBlocker),...list(review.adverseReview)].filter(Boolean);
   const groupList = Array.isArray(act.changeInventory) ? act.changeInventory : [];
   mount.querySelector('#systematic-comparison').innerHTML = `<div class="systematic-cell"><span class="review-state ${cell.status}">${statusName[cell.status]}</span><h3>${html(cell.country)} · ${html(act.id)}</h3>${note ? `<p>${html(sentence(note))}</p>` : '<p>This country–directive comparison is still open. No compliance conclusion follows from an empty row.</p>'}<p><a href="${html(act.originalSource)}" target="_blank" rel="noopener noreferrer">Original EU text ↗</a></p><details><summary>EU change inventory (${groupList.length} groups)</summary><p>${html(act.inventoryStatus)}</p>${groupList.map(group => `<article class="systematic-clause"><h4>${html(locator(group))}</h4><p>${html(groupName(group))}</p><p class="systematic-note">${html(groupAssessment(review,group.id))}</p></article>`).join('') || '<p>The substantive change inventory is still being prepared.</p>'}</details>${evidence.length ? `<details><summary>National sources and comparisons (${evidence.length})</summary><ol class="systematic-sources">${evidence.map(sourceHTML).join('')}</ol></details>` : ''}${limits.length ? `<details><summary>Limits and remaining work</summary>${limits.map(limit => `<p>${html(prose(limit))}</p>`).join('')}</details>` : ''}${cell.findingIds.length ? `<p>Open catalogue records: ${cell.findingIds.map(id => `<a href="#case/${encodeURIComponent(id)}">Read finding</a>`).join(' · ')}</p>` : ''}</div>`;
  };
  actSelect.addEventListener('change',inspect); countrySelect.addEventListener('change',inspect);
  mount.querySelectorAll('[data-inspect-act]').forEach(button => button.addEventListener('click',() => {actSelect.value=button.dataset.inspectAct;inspect();actSelect.focus();actSelect.scrollIntoView({block:'center'});}));
  inspect();
 };
 fetch('data/systematic.json').then(response => {if (!response.ok) throw new Error('Review ledger unavailable');return response.json();}).then(data => {ledger=data;window.renderSystematicCoverage();}).catch(() => {const mount=document.querySelector('#systematic-review');if(mount)mount.textContent='The systematic review ledger could not be loaded. The catalogue remains available.';});
})();
