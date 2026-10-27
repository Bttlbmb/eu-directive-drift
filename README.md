# EU Directive Drift

A lean research website tracing changes in EU law into national provisions. Inspired by EU Translation Inconsistencies. Both reference repositories were inspected read-only and were neither cloned nor edited. The website has no external dependencies and is ready for GitHub Pages publishing from a branch.

## Open locally

Run `npm start`, then open **http://127.0.0.1:4173/**. Alternatively use `python3 scripts/serve.py`; choose another port with `--port 4174`. Stop with Ctrl+C. The server binds to this computer and serves only `docs/`. Use the server rather than opening the HTML directly, so the dataset can load. Local checks use Node.js and Python 3; no `npm install` is needed.

## Publish on GitHub Pages

The GitHub repository is [Bttlbmb/eu-directive-drift](https://github.com/Bttlbmb/eu-directive-drift), using the `main` branch. The complete static site is committed in `docs/` and is ready for branch publishing.

In the GitHub repository, open **Settings → Pages** and select:

- **Source:** Deploy from a branch
- **Branch:** `main`
- **Folder:** `/docs`

Click **Save**. Once enabled, the site will be served at [bttlbmb.github.io/eu-directive-drift/](https://bttlbmb.github.io/eu-directive-drift/); GitHub also shows the published URL in Pages settings.

`docs/` contains the complete static site, including its dataset. `docs/.nojekyll` bypasses Jekyll processing. No custom GitHub Actions workflow, build step, package installation or Python server is needed on GitHub. GitHub manages Pages deployment internally; a Pages deployment may still appear in the Actions tab. See [GitHub's branch publishing documentation](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site).

Assets and data use relative URLs, so the site also works beneath a repository path or on a custom domain. Case, Method and Coverage links use URL fragments and need no server routing rules.

For later updates, edit the files in `docs/`, run `npm run check`, then commit and push to `main`. Pages publishes the committed files directly. The older local `eu-update-chain-mvp.zip` export is ignored by Git; `docs/` is the source to maintain.

## What the website does

- Search and filter by country, EU change type and evidence.
- Show newer EU changes first by default; hide previously recognized concerns with one checkbox.
- Sort by newest EU change (default), country, longest overdue (oldest deadline first; cases without a deadline last) or check date. Ties always fall back to country, then title. The deadline appears in each row while sorting by it.
- Show who previously recognized each concern, separately from its legal strength.
- Present the EU change, current national provision, dates, comparison, independent review and official source links.
- Preserve filters in the URL; provide shareable case links.
- Explain research limits on Method and Coverage pages.

The snapshot is **27 October 2026 (UTC)**. The catalogue contains **57 records across 22 Member States and 28 EU changes**: **6 findings and 51 qualified research leads**. **17** records have no precise prior recognition located; **40** were already publicly recognized. These searches do not establish first discovery. The systematic review remains in progress.

A conservative reassessment examined all 68 previously listed records with separate research and challenge passes. Sixteen concerns were withdrawn: permitted protective variations, citation-only errors without an established reporting gap, unverified scope concerns, and comparisons weakened by binding alternative routes or unresolved national regulatory discretion. Twenty-four retained entries were revised; 28 remain unchanged. The [audit index](research/audit-2026-10-26/summary.json) links every original record to its primary review, independent challenge and final disposition. Reasons and primary-source references are preserved in `research/catalogue-decisions.json`; removal is not a certificate that the whole national framework complies. A compact recovery record preserves the earlier working catalogue without keeping full legislation or source PDFs.

Remaining entries include qualified statutory concerns and research leads. The Hungarian bank-capital statute still has a reversed risk trigger, but the supervisor’s current manual already specifies the correct Tier 1 capital type. That entry now concerns statutory clarity and legal force, not a demonstrated capital shortage. French repair guidance and German photovoltaic classification also contain material official counterevidence, now shown in the relevant cases.

Fully resolved cases and concerns withdrawn after review are excluded from the public dataset and counts. Unconfirmed legal effects are marked visibly as research leads. “No prior recognition located” describes bounded searches, not first discovery. Source-access limits and unverified practical effects remain explicit in the individual reviews.

## Systematic review of the 25 shortest directives

The Coverage page now shows the live research ledger: 25 individual directives, including amending directives, selected from the 110 previously examined EU acts by original official English word count including annexes. It tracks all 675 country–directive pairs and provides the change inventories, national comparisons, source references and remaining uncertainties. Ranking was independently checked, including full-PDF checks where legacy HTML omitted tables.

A completed assessment is not a certificate of compliance: all applicable changed obligations must be considered, but the legal result can remain inconclusive. Notifications alone never establish implementation. Unchanged original provisions and actual enforcement or administrative reporting performance are outside the comparison unless specifically examined. Replacements, transitions and relevant exceptions are followed. The current ledger has **237 completed, 47 partly reviewed and 391 unassessed** country–directive pairs. All 27 countries have formal change assessments for the jam directive, covering its 13 inventoried change groups. Overall coverage remains unfinished.

`research/coverage.json` preserves the working assessments; `docs/data/systematic.json` is their smaller public projection. Run `python3 scripts/build_coverage.py` to refresh the public snapshot. The retained ledger survives removal of temporary working files. Catalogue withdrawals and their contrary sources are applied after research-bundle merges, so older working assessments cannot hide the later correction. A withdrawn case does not automatically change whether the broader country–directive assessment is complete.

## Maintain the dataset

Edit `docs/data/findings.json`, run `npm run check`, and reload. Check `research/catalogue-decisions.json` before restoring a withdrawn entry; a new review must address its recorded contrary evidence. The validator rejects accidental reintroduction. No generator or model API is needed. Each record contains the act chain, national provision, dated evidence, caveat, timeline, sources and review. For a `comparison`, `before` and `beforeLabel` belong to the national-law column; `after` and `afterLabel` belong to the EU column. These names describe display positions, not necessarily chronological order. Labels must not imply that every wording difference requires national amendment.

Keep these editorial fields consistent:

| Field | Values / meaning |
| --- | --- |
| `updateType` | `Amendment`, `Recast`, `Replacement`, `New framework` or `Corrigendum` |
| `catalogueStatus` | `open` or `review`; remove fully resolved cases from this catalogue |
| `recordKind` | `finding` or `lead`; leads have unresolved legal significance |
| `stage` | `judgment`, `commission`, `government`, `national` (an enacted corrective act) or `research` |
| `priorRecognition` | `recognized` or `not-located`, independently of `stage` |
| `recognizedBy` | Authorities or publications identifying this specific concern; empty when none located |
| `recognitionNote` | Recognition basis or dated limits of the acknowledgment search |
| `deadline` | Implementation date; null for corrigenda with no fresh deadline |
| `correctionDate` | EU correction publication date where applicable |
| `evidenceDate` | Date of the cited official assessment or current national-text check |
| `baseActPublished` | Official Journal publication date of the original EU act named in `baseAct`, shown as the first point of the case timeline; omit when no single original act exists |
| `statusKind` | One of the plain status headlines defined in `docs/app.js` (`differs`, `behind`, `draft`, `postponed`, `enacted`, `official`, `open`) |
| `statusDetail` | One short plain line under the status headline; `null` when there is nothing to add |
| `timeline[].who` | Who acted: `eu`, `national`, `court`, `commission`, `check` (our own check) or `commentary`; shown as a chip on each timeline point |
| `consequence` | The answer to “Does it matter?”, required for every record: an opener (“Yes, on paper.”, “Yes, until <date>.” or “Possibly.”), the effect on paper, then what is not established |
| `resolution` | Older research note on follow-up. Optional and no longer shown on the site |
| `timeline` | Sorted ISO dates; year/month precision is supported when exact days are unknown |
| `sources` | Source title, HTTPS URL, role and pinpoint `locator`; official law supports legal comparisons, commentary may establish recognition |

This is a dated snapshot. Recheck enacted remedies at their commencement dates and remove a record once its specific concern is fully resolved. Priority review dates include Ireland’s EIA safeguards on 1 November 2026, Czech, Swedish and German January 2027 commencements, Sweden’s proposed February 2027 work-permit change, Finland’s March 2027 stock exception, Luxembourg’s May 2027 permit transition and Poland’s September 2027 commencement. `reviewAfter` and `remedyDate`, where present, are editorial reminders, not automatic findings of compliance.

Write titles, summaries and the comparison and consequence texts in everyday words: no country name in the title (the country is shown above it), no section numbers outside the comparison and sources, and keep every hedge (“may”, “not established”, “we found no…”). Say who did what (the EU, the Member State, a court, our own check).

Before adding a case, check the actual amended duty, national rule, currentness, lawful options, exceptions and transitional rules. Search for corrections and previous recognition; obtain an independent challenge. Missing notification alone does not prove a substantive national omission. A verified typo alone is insufficient for a public implementation concern. A research lead needs a specific unresolved changed duty, right or legal-certainty question. Assess binding alternative routes by their legal result rather than requiring the EU wording to be copied verbatim. Keep permitted protective variations and unsupported scope comparisons in research instead of the issue list. An old judgment describes its legally relevant date, not necessarily present law. Draft corrections are not enacted corrections.

## Files and lean evidence

`docs/` is the portable website and GitHub Pages publishing folder. `scripts/` holds the local server, checks and optional research utilities; `research/` holds their compact inventories. `reference-notes.md` and `independent-qa.md` summarize the inspection and final review. Full legislation, judgments and source PDFs are not bundled: records link to official publishers. The website uses no external fonts, analytics, accounts or paid services.

This is a manually maintained MVP. It has no automatic discovery or monitoring service, database, editor or authentication. GitHub Pages publishes `main:/docs` at [bttlbmb.github.io/eu-directive-drift/](https://bttlbmb.github.io/eu-directive-drift/). The `docs/` folder can also be served by any static host.

## Verification

`npm run check` checks JavaScript syntax and validates identifiers, required fields, recognition metadata, dates, timelines, source URL syntax and pinpoints. It also checks that every evidence type can be filtered and documented withdrawals remain outside the public catalogue and their corrections appear in coverage. Two isolated regression checks exercise accidental restoration and stale research-bundle merging. These checks cannot verify legal accuracy. `python3 scripts/check_links.py` optionally checks availability without keeping downloads; official sites may block HEAD requests or show anti-bot pages.

The 26 October browser checks covered all 53 then-retained case pages and all 675 coverage selector combinations without rendering failures or console errors, plus loading, search, combined filters, recognition hiding and persistence after reload, the EU-change-year sort and its persistence, empty results, reset, timelines and source links, and method/coverage navigation. Source assessments were cross-checked by separate research agents. The fourth pass additionally checked new framework/replacement filters and the updated recognition counts. Full cross-browser and mobile-device testing remains outside this MVP.

The 27 October pass added four qualified leads (Czech and Slovak jelly quantities, Slovenian jam fruit identity, and Croatian toy cobalt permissions), with independent source checks. The first three have no precise prior report located; the Croatian concern is officially recognized. The updated catalogue, recognition filter and 237/47/391 coverage totals were checked in the browser. Compact pass notes are in `research/pass-2026-10-27/`; re-downloadable full legal bodies remain outside the project.
