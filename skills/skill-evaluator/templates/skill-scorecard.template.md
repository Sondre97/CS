# Scorecard: <skill-navn> v<versjon>

| Felt | Verdi |
|---|---|
| Skill / versjon | <navn> v<semver> |
| Eier | <navngitt person – uten eier, ingen deling> |
| Dato for eval-kjøring | <ÅÅÅÅ-MM-DD> |
| Modell(er) testet | <modell-id-er> |
| Golden set | <sti til evals.json, antall oppgaver, kjøringer per oppgave> |
| Vedtak | UTKAST / GODKJENT FOR DELING / UNDERKJENT / PENSJONERT |

## 1. Triggering
| Metrikk | Resultat | Terskel | Status |
|---|---|---|---|
| Skal-treffe riktig | __ / __ (___ %) | ≥ 90 % | ☐ |
| Skal-ikke-treffe riktig | __ / __ (___ %) | ≥ 80 % | ☐ |

## 2. Effekt (mot baseline)
| Konfigurasjon | Pass rate (snitt ± stddev) | Tid (s) | Tokens |
|---|---|---|---|
| Med skill | ___ % ± ___ | | |
| Baseline (uten skill / v<forrige>) | ___ % ± ___ | | |
| **Delta** | **___ pp** | | |

Terskler: med skill ≥ 85 % og delta ≥ +20 pp. Status: ☐

## 3. Pålitelighet
- Kjøringer per oppgave (k): ___
- pass^k (andel oppgaver der alle k kjøringer lyktes): ___ %
- Kritiske forventninger som feilet i minst én kjøring: <ingen / liste>
- Høy-varians-oppgaver undersøkt i transkript: <notat>

## 4. Kostnad
- Delta tid og tokens mot baseline, med begrunnelse hvis stor: <notat>

## 5. Forretningseffekt (fylles ut i drift, revideres kvartalsvis)
- Adopsjon (andel relevante oppgaver der skillen brukes): ___
- Akseptrate (leveranser godkjent uten omarbeid): ___
- Estimert spart tid per leveranse: ___
- Tilbakemeldinger siden forrige revisjon → nye eval-oppgaver: <liste>

## Kvalitativ vurdering
- Menneskelig gjennomgang av leveransene (hvem, hovedinntrykk):
- Transkript-funn (navigasjon i skillen, omveier, grader-rettferdighet):

## Vedtak og oppfølging
- Beslutning m/ begrunnelse:
- Endringer siden forrige versjon (CHANGELOG-utdrag):
- Neste planlagte re-kjøring (regresjon ved endring, ellers kvartalsvis):
