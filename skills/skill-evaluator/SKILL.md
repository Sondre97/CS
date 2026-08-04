---
name: skill-evaluator
description: Mål, test og kvalitetssikre Claude-skills før og etter at de deles i BDO. Bruk denne skillen HVER GANG noen vil evaluere, måle, benchmarke eller «teste» en skill, lage golden set/evals, sjekke om en skill trigges riktig, sammenlikne to versjoner av en skill, sette akseptkriterier før utrulling, eller etablere styring/eierskap for delte skills – også når de bare spør «er denne skillen god nok?» eller «ble den bedre?». Trigger på: eval, evaluere, måle skill, benchmark, golden set, regresjonstest, triggertest, skill-kvalitet, utrulling av skills.
---

# skill-evaluator – måling av skills som deles i BDO

En skill som deles på tvers av virksomheten er ikke en prompt, men et
**produkt**: mange brukere, mange oppgaver, konsekvenser når den bommer.
Da holder det ikke at den «virker på det jeg testet den på» – den må måles.
Denne skillen definerer HVA som måles og NÅR; mekanikken (kjøre testene,
benchmark-formatet, viewer) står i Anthropics `skill-creator`, som brukes som
motor der den er tilgjengelig. Full metodikk med kilder: `docs/skill-maling.md`.

## De fem måledimensjonene

Mål alle fem – en skill kan være utmerket på én og ubrukelig på en annen.

| # | Dimensjon | Spørsmål | Måles slik |
|---|---|---|---|
| 1 | **Triggering** | Utløses skillen når den skal – og bare da? | 20 realistiske spørringer (10 skal treffe, 10 nesten-treff som ikke skal), 3 kjøringer per spørring. Presisjon og dekning. |
| 2 | **Effekt** | Blir resultatet bedre MED skillen enn uten? | Golden set (3–10 realistiske oppgaver med etterprøvbare forventninger) kjørt med og uten skill av uavhengige subagenter. Andel forventninger oppfylt (pass rate) per konfigurasjon + delta. |
| 3 | **Pålitelighet** | Samme kvalitet hver gang? | ≥3 kjøringer per oppgave. Snitt ± standardavvik, og pass^k-tankegang: andelen oppgaver der ALLE k kjøringene lykkes. I forretningsbruk veier én pinlig leveranse tyngre enn et pent snitt. |
| 4 | **Kostnad** | Hva koster kvaliteten? | Tokens og tid per kjøring, delta mot baseline. En skill som dobler kvaliteten men tredobler tiden kan være feil valg for hastesaker – dokumentér avveiningen. |
| 5 | **Forretningseffekt** | Virker den i drift, hos alle? | Etter deling: adopsjon (andel relevante oppgaver der skillen faktisk brukes), akseptrate (andel leveranser godkjent uten omarbeid), spart tid per leveranse, brukertilbakemelding. |

## Grader-hierarkiet

Foretrekk graderne i denne rekkefølgen – fall nedover kun når nivået over ikke
kan måle det du trenger:

1. **Kode-gradert** (deterministisk skript): objektivt, gratis å gjenta, samme
   svar hver gang. Eksempel: `pptx-brand/scripts/check_brand.py` sjekker
   farger, fonter og format rett fra filen. Skriv sjekker som skript, ikke
   skjønn, overalt hvor det går.
2. **Modell-gradert** (LLM-som-dommer): for det koden ikke ser – struktur,
   relevans, tone. Krever rubrikk med definerte nivåer, blind vurdering
   (dommeren vet ikke hvilken konfigurasjon som laget hva), og mottiltak mot
   kjente dommer-skjevheter (posisjon, lengde, egenpreferanse) – se
   `references/metodikk.md`.
3. **Menneske-gradert**: fasiten de to andre kalibreres mot. Brukes på
   stikkprøver og alt som skal ut eksternt – ikke på alt (skalerer ikke).

## Prosessen

1. **Definer suksess** før du tester: hva skal skillen gjøre, for hvem, og
   hvilke forventninger er etterprøvbare? Skriv forventninger som diskriminerer
   (skiller god fra dårlig leveranse) og ikke kan «games» av en tom leveranse.
2. **Lag golden set** (`templates/evals.template.json`): 3–10 realistiske
   oppgaver slik brukere faktisk formulerer dem – med filer, tall og kontekst.
   Ta med minst én kant-sak. Ikke perfeksjonér: et lite, kjørbart sett nå slår
   et perfekt sett om tre uker; utvid etter hvert som feil avdekkes.
3. **Kjør baseline**: samme oppgaver med og uten skill (nye skills) eller
   gammel mot ny versjon (endringer). Uavhengige subagenter, ikke deg selv –
   du vet for mye om hva som «egentlig» var ment.
4. **Grader og aggreger**: kjør graderne, aggreger pass rate/tid/tokens per
   konfigurasjon (skill-creator: `aggregate_benchmark` + viewer), og få et
   menneske til å se på selve leveransene, ikke bare tallene.
5. **Iterér på skillen** ut fra funnene – generaliser årsaken bak en feil i
   stedet for å sy inn spesialregler for testoppgavene (overtilpasning gjør
   settet verdiløst). Gjenta 3–5.
6. **Akseptgate før deling** – se terskler under. Skillen deles først når
   gaten er passert og en navngitt eier har godkjent.
7. **I drift**: kjør golden set på nytt ved HVER endring av skillen
   (regresjon), kvartalsvis uten endring (modell- og miljødrift), og følg
   dimensjon 5. Nye feil fra virkeligheten blir nye eval-oppgaver.

## Akseptterskler før deling (utgangspunkt – justér bevisst per skill)

- Effekt: pass rate MED skill ≥ 85 % på golden set, og ≥ 20 prosentpoeng
  over baseline (ellers: hvorfor finnes skillen?)
- Pålitelighet: ingen kritisk forventning feiler i noen av kjøringene;
  standardavvik pass rate ≤ 10 pp
- Triggering: ≥ 90 % riktig på skal-treffe, ≥ 80 % riktig på skal-ikke-treffe
- Kostnad: dokumentert delta; ingen terskel, men avvik skal være begrunnet
- Dokumentert: eier, versjon, CHANGELOG-innslag, dato for siste eval-kjøring

Resultatet føres i `templates/skill-scorecard.template.md` – ett scorecard per
skill-versjon, sjekket inn sammen med skillen.

## Styring når skills deles i virksomheten

- **Eierskap**: hver delt skill har én navngitt eier som svarer for kvalitet
  og vedlikehold. Uten eier – ingen deling.
- **Versjonering**: semver i frontmatter-kommentar eller CHANGELOG
  (MAJOR = endret atferd/arbeidsflyt, MINOR = ny evne, PATCH = fiks).
  Brukerne skal kunne vite hvilken versjon som lagde en leveranse.
- **Endringskontroll**: endringer går via PR med grønn eval-kjøring
  (regresjonsgate) – aldri rett i delt katalog.
- **Tilbakemeldingssløyfe**: én kjent kanal for å melde feil/forslag; eieren
  omsetter meldingene til nye eval-oppgaver og skill-endringer.
- **Revisjon**: kvartalsvis gjennomgang av scorecardene – skills uten bruk
  eller under terskel pensjoneres eller repareres. Rammeverket her følger
  tankegangen i NIST AI RMF (MEASURE/MANAGE) – se docs/skill-maling.md.

## Verktøy

- `skill-creator` (Anthropic, installert): kjøring av test-subagenter,
  benchmark.json, eval-viewer for menneskelig gjennomgang,
  beskrivelses-optimalisering for triggering. Bruk den som motor.
- `templates/` her: evals.template.json (golden set) og
  skill-scorecard.template.md (akseptgate/scorecard).
- `docs/skill-maling.md`: hele rammeverket med kilder – les den når du skal
  begrunne metodevalg eller sette opp måling for et nytt område.
