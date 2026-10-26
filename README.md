# EU Update Chain

A lean research website tracing changes in EU law into national provisions. Inspired by EU Translation Inconsistencies. Both reference repositories were inspected read-only and were neither cloned nor edited. The website has no external dependencies and is ready for GitHub Pages publishing from a branch.

## Open locally

Run `npm start`, then open **http://127.0.0.1:4173/**. Alternatively use `python3 scripts/serve.py`; choose another port with `--port 4174`. Stop with Ctrl+C. The server binds to this computer and serves only `docs/`. Use the server rather than opening the HTML directly, so the dataset can load. Local checks use Node.js and Python 3; no `npm install` is needed.

## Publish on GitHub Pages later

The local Git repository uses `main`. No remote or hosted repository has been created, and nothing has been pushed or published.

When ready, create an **empty public repository** on GitHub (without adding a README, license or `.gitignore` there). Replace `YOUR-USERNAME` and `YOUR-REPOSITORY` below with its owner and name, then run:

```sh
npm run check
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
git push -u origin main
```

In the GitHub repository, open **Settings → Pages** and select:

- **Source:** Deploy from a branch
- **Branch:** `main`
- **Folder:** `/docs`

Click **Save**. A project repository will be served at `https://YOUR-USERNAME.github.io/YOUR-REPOSITORY/`; GitHub also shows the published URL in Pages settings.

`docs/` contains the complete static site, including its dataset. `docs/.nojekyll` bypasses Jekyll processing. No custom GitHub Actions workflow, build step, package installation or Python server is needed on GitHub. GitHub manages Pages deployment internally; a Pages deployment may still appear in the Actions tab. See [GitHub's branch publishing documentation](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site).

Assets and data use relative URLs, so the site also works beneath a repository path or on a custom domain. Case, Method and Coverage links use URL fragments and need no server routing rules.

For later updates, edit the files in `docs/`, run `npm run check`, then commit and push to `main`. Pages publishes the committed files directly. The older local `eu-update-chain-mvp.zip` export is ignored by Git; `docs/` is the source to maintain.

## What the website does

- Search and filter by country, EU change type and evidence.
- Put candidates with no located prior recognition first, with newer EU changes prioritised; hide previously recognized concerns with one checkbox.
- Sort independently by EU change year, evidence date, Member State or deadline.
- Show who previously recognized each concern, separately from its legal strength.
- Present the EU change, current national provision, dates, comparison, independent review and official source links.
- Preserve filters in the URL; provide shareable case links.
- Explain research limits on Method and Coverage pages.

The snapshot is **26 October 2026 (UTC)**. The catalogue currently contains **56 records across 22 Member States and 28 EU changes**. The completed fourth research pass added **11 records**, including **2 with no precise prior recognition located**. The catalogue has **19** such candidates in total; the other **37** concerns were already publicly recognized.

The latest work examined bank-capital corrections, single-permit unemployment protection, environmental offences, trafficking-service offences, anti-SLAPP jurisdiction, online withdrawal and financial explanations, and electricity-contract rights. The strongest new less-documented lead is Hungary’s reversed risk trigger for an additional bank-capital requirement following an August 2026 EU correction. Its actual supervisory effect remains unverified. A second new lead concerns Romania’s group-fund exception: national branches wording survives an October EU correction to subsidiaries. Lawful wider domestic regulation remains possible; no affected manager or decision was examined. The other additions are explicitly marked as previously recognized. Further recent corrections were excluded where current national law or administration already supplied the right, or no substantive omission was established.

Fully resolved cases are excluded from the public dataset, counts. Remaining records include both qualified text mismatches and publicly identified implementation concerns. Their inclusion does not establish a current breach in every case.

“No prior recognition located” describes limited searches. It does not establish first discovery. In particular, the Hungarian, Latvian and Lithuanian exposure-formula leads involve lower national limits; lawful stricter protection remains a possible explanation. They are not findings of unsafe worker protection or deliberate disregard.

## Maintain the dataset

Edit `docs/data/findings.json`, run `npm run check`, and reload. No generator or model API is needed. Each record contains the act chain, national provision, dated evidence, caveat, timeline, sources and review. Optional `comparison` labels support national/EU comparisons without implying that the national wording must change.

Keep these editorial fields consistent:

| Field | Values / meaning |
| --- | --- |
| `updateType` | `Amendment`, `Recast`, `Replacement`, `New framework` or `Corrigendum` |
| `catalogueStatus` | `open` or `review`; remove fully resolved cases from this catalogue |
| `recordKind` | `finding` or `lead`; leads have unresolved legal significance |
| `stage` | `judgment`, `commission`, `government` or `research` |
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

Before adding a case, check the actual amended duty, national rule, currentness, lawful options, exceptions and transitional rules. Search for corrections and previous recognition; obtain an independent challenge. Missing notification alone does not prove a substantive national omission. An old judgment describes its legally relevant date, not necessarily present law. Draft corrections are not enacted corrections.

## Files and lean evidence

`docs/` is the portable website and GitHub Pages publishing folder. `scripts/` holds the local server, checks and optional research utilities; `research/` holds their compact inventories. `reference-notes.md` and `independent-qa.md` summarize the inspection and final review. Full legislation, judgments and source PDFs are not bundled: records link to official publishers. The website uses no external fonts, analytics, accounts or paid services.

This is a manually maintained MVP. It has no automatic discovery or monitoring service, database, editor or authentication. It has not been deployed. The `docs/` folder can also be served by any static host.

## Verification

`npm run check` checks JavaScript syntax and validates identifiers, required fields, recognition metadata, dates, timelines and source URL syntax. It cannot verify legal accuracy. `python3 scripts/check_links.py` optionally checks availability without keeping downloads; official sites may block HEAD requests or show anti-bot pages.

Browser checks covered loading, search, combined filters, recognition hiding and persistence after reload, the new EU-change-year sort and its persistence, empty results, reset, new case timelines and source links, and method/coverage navigation. Source assessments were cross-checked by separate research agents. The fourth pass additionally checked new framework/replacement filters and the updated recognition counts. Full cross-browser and mobile-device testing remains outside this MVP.
