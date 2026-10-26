# Read-only reference inspection

Inspected 25 October 2026. Used public website GETs and authenticated GitHub API GETs; SSH authentication also succeeded. Neither reference repository was cloned or changed. Temporary HTML/CSS/JS inspection copies live only in /tmp.

## What the reference actually does

- Separate static website and Python generator repositories. Public website has no installed packages; reads checked JSON export and does not trigger model/research work.
- Home catalogue uses an editorial white page, Georgia serif act headings, system sans metadata, muted blue links, thin gray rules, and generous whitespace. Max content width 1120px with 40px inset. Catalogue rows use main text + 350px facts columns.
- Masthead title, understated lede, collection counts; Method dialog; Statistics link; private Dashboard link.
- Catalogue row: act citation/title and one-sentence explanation, exact reviewed version, finding count, coverage completeness, language list, Major/Limited/unrated proportions. Sort by act date, findings, review state; URL preserves sort.
- Reader: full legal text next to finding list. Selecting highlighted text opens evidence, language source, English wording, translated wording, original wording, explanation, potential legal impact and uncertainty. Filters and copy-link preserve selection in URL.
- Coverage and findings are distinct. Completed run is not full coverage. No findings does not establish equivalence.
- Findings are provisional single-pass AI assessments; automated source checks but no case-law review. The new project should do better on explicit court/Commission evidence where available.
- The public snapshot contains checked source quotations. Raw run inputs/archives stay in generator. User's MVP should remain lighter: concise records and re-downloadable source URLs, no bulky source archive.

## Transfer to this MVP

The implementation uses an editorial catalogue, country-specific update chains, dated official evidence, source pinpoints, shareable URLs and Method/Coverage disclosures. Under the user’s revised scope it excludes corrected cases. Recognition by a court, Commission or national authority is a separate field and can be hidden; candidates with no located official recognition appear first. The website stores short analysis and links rather than copies of the source archive.

## Sources read

- https://eu-translation-inconsistencies.onrender.com/ ; catalogue.css ; catalogue.js
- GET https://api.github.com/repos/Bttlbmb/eutranslationinconsistencies/readme
- GET https://api.github.com/repos/Bttlbmb/eutranslationinconsistencies/contents/docs/reader.md
- GET https://api.github.com/repos/Bttlbmb/eutranslationinconsistencies-generator/readme

Reference READMEs report 127 acts / 2,671 supported language-specific records, 23 October 2026 snapshot. Those are the reference's counts, never counts for this MVP.
