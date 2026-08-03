---
name: pptx-brand
description: Lag og kvalitetssikre BDO-brandede PowerPoint-presentasjoner som består merkevaresjekk. Bruk denne skillen HVER GANG en presentasjon skal lages, redigeres eller kontrolleres med BDO-profil – kundepresentasjoner, tilbudspresentasjoner, pitch, partnermøter, interne statuser, analysepresentasjoner – også når brukeren bare sier «lag slides», «deck» eller «presentasjon» i en BDO-/jobbsammenheng uten å nevne branding. Trigger på BDO-presentasjon, kundedeck, tilbudsslides, «i BDO-mal», «følger denne profilen?», merkevaresjekk av pptx. Brukes SAMMEN med skillen pptx (filmekanikk) og bdo-design (design-fasit).
---

# pptx-brand – BDO-riktige presentasjoner

## Formål og samspill

Denne skillen finnes fordi presentasjoner er BDOs mest delte leveranseformat, og
fordi «ser BDO ut» må bety det samme uansett hvem som lager dekket. Skillen gjør
tre ting: styrer arbeidsflyten, låser designvalgene til merkevaren, og gjør
resultatet **målbart** med en deterministisk sjekk.

Rollefordeling – les de andre ved behov, dupliser dem ikke:

| Skill | Rolle |
|---|---|
| `pptx` | All filmekanikk: pptxgenjs, mal-/OOXML-redigering, validate, visuell QA |
| `bdo-design` | Fasit for farger, typografi, foto, malfiler og layoutnavn |
| `datavis-story` | Grafvalg og datafortelling før grafen produseres |
| `norsk-analysesprak` | Språkregister for all norsk tekst på slidene |
| **`pptx-brand`** | Arbeidsflyten som binder dem sammen + merkevarekontrollen |

## Arbeidsflyt

### 1. Avklar før du produserer

Formål, publikum og bruk (presentert i møte eller lest på egen hånd?) avgjør
tekstmengde og antall slides. Lag storyline først: ett budskap per slide,
formulert som en meningsbærende setning – tittelen skal kunne leses alene som
et resonnement (action titles). Er ikke antall slides oppgitt, foreslå et
spenn og begrunn det.

### 2. Velg produksjonsvei

**A – Offisiell BDO-mal er tilgjengelig** (bruker peker på .potx/.pptx, eller
malfilene i `0. AI-work/BDO branding/` finnes): Bruk pptx-skillens mal-flyt
(thumbnail → velg layouts → fyll). Velg blant de navngitte norske layoutene
(«Tittel A – Rød (Bildebakgrunn)», «Agenda 4/5 emner», «Heading og tekstfelt
A–D», «Heading, tekstfelt og bilde A/B», «Divider E – Rød» m.fl.) og varier dem
– aldri Blank, aldri samme layout på alle innholdsslides. Malens tema gir
riktige farger og fonter automatisk; ikke hardkod farger oppå temaet.

**B – Ingen mal tilgjengelig**: Bygg med pptxgenjs etter pptx-skillens
oppskrift, med brand-reglene under som designsystem. Sett alle farger og
fonter eksplisitt (generert deck har ikke BDO-temaet, så temafarge-referanser
ville arvet feil farger).

### 3. Brand-regler (fasit fra bdo-design)

- **Farger** – kun disse, tint/skygge av dem, eller gråtoner:
  `E81A3B` (primær rød – aksent og høydepunkt, ALDRI store tekstflater),
  `333333` (all brødtekst), `5B6E7F` (slate/sekundær), `98002E` (burgunder),
  `D67900` (oransje, sparsomt), `009966` (grønn/positiv), `008FD2` (blå),
  `0062B8` (lenker), `F2F2F2` (lyse flater). Grafserier i prioritert
  rekkefølge: E81A3B → 333333 → 5B6E7F → 98002E → D67900 → 009966 → 008FD2.
- **Typografi**: Trebuchet MS overalt i PowerPoint (Bliss Pro kun hvis
  tilgjengelig hos mottaker). Trebuchet er QA-upålitelig i
  LibreOffice-rendring (jf. pptx-skillen), så gi tekstbokser ~10 % slakk og
  stol ikke blindt på overflow-sjekk i forhåndsvisning.
- **Format**: 16:9. Hvite eller `F2F2F2` bakgrunner på innholdsslides; rød
  bakgrunn kun på tittel/divider (med hvit tekst).
- **Grafer**: native PowerPoint-grafer (aldri bilder av grafer), BDO-farger
  eksplisitt satt, prinsippene fra datavis-story. Én graf – én innsikt –
  innsikten i tittelen.
- **Foto**: ekte, nære, norske miljøer med varme (se bdo-design). Mangler
  bilder: generer med Higgsfield etter retningslinjene der.
- Alle designråd i pptx-skillen gjelder (ingen aksentstriper, ingen rene
  kulepunkt-slides, størrelseskontrast osv.) – med BDO-paletten i stedet for
  frie palettvalg.

### 4. Kvalitetskontroll (obligatorisk, i denne rekkefølgen)

1. **Merkevaresjekk**: `python scripts/check_brand.py deck.pptx` – sjekker
   16:9, fonter, farger mot paletten, tema, plassholderrester og layoutbruk.
   Fiks ALLE FAIL og vurder hver WARN før du går videre. Kjøres med `--json`
   i evals og CI; samme sjekk begge steder er poenget – det du leverer er det
   som måles.
2. **Filvalidering**: pptx-skillens `validate.py` (med `--original` for
   malbaserte deck).
3. **Visuell QA**: render til bilder og se på hver slide med friske øyne
   (overflow, overlapp, kontrast – se pptx-skillens QA-liste).
4. **Menneskelig sjekkliste** før ekstern bruk: `references/kvalitetssjekk.md`.

### 5. Lever og lær

Oppgi hva merkevaresjekken konkluderte med når du leverer. Avvik brukeren
påpeker som sjekken ikke fanget, er kandidater til nye sjekker – meld dem inn
som forbedring av denne skillen (se skill-evaluator).

## Måling

Skillen har et golden set i `evals/evals.json` (kjøres med/uten skill, graderes
bl.a. med check_brand.py) og trigger-testsett i `evals/trigger-evals.json`.
Prosess og terskler: se skillen `skill-evaluator` og `docs/skill-maling.md`
i dette repoet. Endrer du skillen: kjør evals på nytt før deling.
