# Scorecard: pptx-brand v0.1 (iterasjon 1)

| Felt | Verdi |
|---|---|
| Skill / versjon | pptx-brand v0.1 |
| Eier | **ikke satt – må settes før deling** |
| Dato for eval-kjøring | 2026-08-04 |
| Modell(er) testet | claude-fable-5 (kun én modell) |
| Golden set | `skills/pptx-brand/evals/evals.json` – 3 oppgaver, **1 kjøring per konfigurasjon** |
| Vedtak | **UTKAST – ikke klar for deling** |

## 1. Triggering
| Metrikk | Resultat | Terskel | Status |
|---|---|---|---|
| Skal-treffe riktig | ikke kjørt | ≥ 90 % | ☐ |
| Skal-ikke-treffe riktig | ikke kjørt | ≥ 80 % | ☐ |

Testsettet finnes (`evals/trigger-evals.json`, 20 spørringer med nesten-treff
mot pptx, docx, bdo-design og HTML-rapporter), men er ikke kjørt. Kjøres med
skill-creators beskrivelses-optimalisering før deling.

## 2. Effekt (mot baseline)
| Konfigurasjon | Pass rate | Tid | Tokens |
|---|---|---|---|
| Med skill | **100 % ± 0** (21/21 forventninger) | ikke fanget | ikke fanget |
| Baseline (uten skill) | **81,5 % ± 3,2** (17/21) | ikke fanget | ikke fanget |
| **Delta** | **+18,5 pp** | – | – |

Terskel med skill ≥ 85 %: **oppfylt**. Terskel delta ≥ +20 pp: **ikke
oppfylt (+18,5 pp)** – men taket er kunstig lavt fordi fire av sju
forventninger per oppgave er innholdskrav baseline også klarer. Se
assertion-kvalitet under.

Per deck (`check_brand.py`): med skill 7 PASS / 0 WARN / 0 FAIL i alle tre.
Uten skill: minst én FAIL i alle tre.

## 3. Pålitelighet
- Kjøringer per oppgave (k): **1 – under kravet på 3**
- pass^k: **kan ikke beregnes ved n=1**
- Kritiske forventninger som feilet: ingen i med-skill-konfigurasjonen
- Merknad: 5 av 6 agenter ble avbrutt av en sesjonsgrense under sin siste
  visuelle QA-runde, etter at filen var skrevet. Kode-graderte forventninger
  er upåvirket; siste finpuss av layout kan mangle i enkelte deck.

## 4. Kostnad
Ikke målt denne iterasjonen (telemetrien gikk tapt da agentene ble avbrutt).
Den ene kjøringen med data brukte 102 752 tokens på 787 sekunder (baseline,
eval-2). Må fanges i iterasjon 2.

## 5. Forretningseffekt
Ikke relevant ennå – skillen er ikke delt.

## Kvalitativ vurdering
- Menneskelig gjennomgang: **ikke gjennomført** – `review.html` er generert
  for formålet, men ingen har sett gjennom dekkene ennå. Kravet i
  skill-evaluator er at et menneske ser på selve leveransene, ikke bare
  tallene, før vedtak.
- Funn fra graderingen som endret skillen i denne iterasjonen:
  1. Baseline skriver «BDO-rød» fra hukommelsen som `ED1A3B` (fasit
     `E81A3B`) i alle tre deck. `check_brand.py` fikk en egen
     nesten-palettfarge-advarsel, og SKILL.md sier nå eksplisitt at
     hex-verdier kopieres fra fasit, aldri gjengis fra hukommelsen.
  2. Med-skill-kjøringene skrev et ekte BDO-tema i `theme1.xml` – sterkere
     enn skillen ba om. Praksisen er nå skrevet inn i SKILL.md med
     begrunnelse.
  3. eval-3 baseline viste den farligste feilen: en temafarge-referanse i et
     deck uten BDO-tema, som ser riktig ut i koden og blir Office-blå hos
     mottaker.

## Vedtak og oppfølging

**Ikke klar for deling.** Retningen er tydelig og alle tre med-skill-deck er
merkevare-rene, men tre av gatens krav mangler: n=3-kjøringer (pålitelighet),
triggertest, og menneskelig gjennomgang. Før iterasjon 2:

1. Kjør golden settet 3 ganger per konfigurasjon og fang tokens/tid per
   kjøring. Rapportér pass^3.
2. Kjør triggersettet.
3. Menneskelig gjennomgang av `review.html`; noter designavvik som
   `check_brand.py` ikke fanger.
4. Bytt ut den ikke-diskriminerende forventningen «filen finnes og er gyldig
   pptx» (passerte i alle seks kjøringer) med en strengere strukturell sjekk,
   og legg til minst én kant-sak – f.eks. et deck bygget fra den offisielle
   `.potx`-malen, som er produksjonsvei A og foreløpig helt utestet.
5. Sett navngitt eier.
