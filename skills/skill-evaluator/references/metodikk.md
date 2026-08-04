# Metodikk – detaljer og begrunnelser

Dette er dybdelaget under SKILL.md. Kildene bak hvert råd står i
`docs/skill-maling.md` (kapittel for kapittel med URL-er).

## Innhold
1. [Gode forventninger](#1-gode-forventninger)
2. [LLM-som-dommer riktig brukt](#2-llm-som-dommer-riktig-brukt)
3. [Kapabilitets- vs regresjonssett](#3-kapabilitets--vs-regresjonssett)
4. [Statistikk i små utvalg](#4-statistikk-i-små-utvalg)
5. [Les transkriptene](#5-les-transkriptene)
6. [Test på tvers av modeller](#6-test-på-tvers-av-modeller)
7. [Triggering-måling](#7-triggering-måling)

## 1. Gode forventninger

En forventning («assertion») er en etterprøvbar påstand om leveransen. Tre
krav skiller nyttige forventninger fra støy:

- **Etterprøvbar**: helst med skript mot leveransens *tilstand* (filen finnes,
  består check_brand.py, har 5 slides, inneholder tallet 182) – ikke mot hva
  agenten *sa* at den gjorde. Sluttmeldingen kan påstå suksess uten dekning;
  tilstanden lyver ikke.
- **Diskriminerende**: en forventning som passerer både med og uten skill
  («filen er en pptx») måler ikke skillens verdi. Sjekk i benchmark-analysen
  hvilke forventninger som aldri skiller konfigurasjonene, og bytt dem ut.
- **Ikke gamebar**: «nevner CSRD» passeres av en tom slide med ordet CSRD.
  Kombiner innholdskrav med strukturkrav (riktig antall slides, graf til
  stede, brand-sjekk grønn) så en hul leveranse ikke slipper gjennom.

Subjektive kvaliteter (skrivestil, design-skjønn) skal IKKE presses inn i
forventninger – de vurderes kvalitativt av menneske eller strukturert dommer.

## 2. LLM-som-dommer riktig brukt

Sterke dommermodeller når ~80–85 % enighet med mennesker – omtrent samme nivå
som mennesker seg imellom (Zheng et al. 2023). Det gjør dommeren til en
skalerbar tilnærming til menneskelig vurdering, men bare med disse
mottiltakene:

| Kjent skjevhet | Mottiltak |
|---|---|
| Posisjonsbias (favoriserer første svar) | Vurder parvis i begge rekkefølger; kast vurderingen hvis den flipper |
| Lengdebias (favoriserer lange svar) | Be dommeren eksplisitt se bort fra lengde; sjekk korrelasjon lengde↔score |
| Egenpreferanse (favoriserer egen modellfamilie) | Ikke la en modell dømme sin egen leveranse der det kan unngås |
| Svak på matte/logikk | Tall, beregninger og fakta graderes med kode, aldri dommer |

Rubrikk-oppsett som fungerer (G-Eval-mønsteret + Anthropics eval-doc):
1. Gi dommeren kriteriene og be den resonnere stegvis før den scorer.
2. Bruk forankrede skalaer der hvert nivå er definert («1: ikke i det hele
   tatt … 5: fullstendig»), eller binært ja/nei for absolutte krav.
3. Krev strukturert output (kun tall/JSON) så scorene kan aggregeres.
4. Blind vurdering: dommeren skal ikke vite hvilken konfigurasjon (med/uten
   skill, gammel/ny versjon) som produserte hva.
5. Parvis sammenlikning («hvilken er best og hvorfor») diskriminerer bedre
   enn fri skala-scoring når to versjoner skal sammenliknes.
6. Kalibrer: la et menneske vurdere et utvalg og sjekk at dommeren lander
   likt; juster rubrikken til den gjør det.

## 3. Kapabilitets- vs regresjonssett

To sett med ulike formål (Anthropic, «Demystifying evals for AI agents»):

- **Kapabilitetssett**: vanskelige oppgaver med lav pass rate. Formålet er å
  drive forbedring – her SKAL det være rødt.
- **Regresjonssett**: alt skillen allerede mestrer, pinnet nær 100 %.
  Formålet er å beskytte det som virker. Kjøres ved hver endring av skillen
  og ved hvert modellbytte (modellbytter er i praksis hovedgrunnen til at
  delte skills plutselig oppfører seg annerledes).
- Når en kapabilitetsoppgave når stabil høy pass rate, **flyttes den over** i
  regresjonssettet. Golden settet vokser altså med skillens modenhet.

Metning er et faresignal: når alt står på 100 % over tid, måler settet
ingenting lenger – legg til hardere oppgaver fra virkelige feil.

## 4. Statistikk i små utvalg

Agentkjøringer er ikke-deterministiske; ett datapunkt per oppgave er anekdote.

- Kjør hver oppgave **minst 3 ganger** per konfigurasjon. Rapportér snitt ±
  standardavvik og min/maks – og vær ærlig på at n=3 gir grove estimater;
  bruk dem til å fange store forskjeller, ikke til å skille 82 % fra 85 %.
- Skill **pass@k** («minst én av k lyktes» – relevant når en bruker kan prøve
  på nytt) fra **pass^k** («alle k lyktes» – relevant når leveransen går rett
  til kunde). For en delt forretningsskill er pass^k den ærlige metrikken;
  de to divergerer dramatisk når k øker (τ-bench: systemer med god pass@1
  falt under 25 % på pass^8).
- Høy varians på én oppgave (f.eks. 50 % ± 40 pp) betyr som regel utydelig
  skill-instruks eller flaky forventning – undersøk transkriptene før du
  konkluderer om kvalitet.
- **Isolér kjøringene**: hver kjøring i rent miljø. Gjenbrukte kataloger gir
  falske positive – agenter finner rester fra forrige kjøring (git-historikk,
  gamle filer) og «løser» oppgaven ved å kopiere dem.

## 5. Les transkriptene

Aggregerte tall forteller AT noe feiler, transkriptene forteller HVORFOR.
Fast rutine etter hver benchmark:

- Les minst ett transkript per oppgave, alle ved avvik.
- Se etter: leser agenten skill-filene den skal (eller hopper den over
  referansene)? Gjør den samme omvei i hver kjøring (kandidat for bundlet
  skript)? Består den forventningene på uærlig vis (reward hacking)?
- Sjekk at graderne er rettferdige: en forventning som feiler på formulering
  («3 faser» skrevet som «tre trinn») skal fikses i forventningen, ikke i
  skillen.

## 6. Test på tvers av modeller

En delt skill kjøres av den modellen brukeren tilfeldigvis har – test derfor
på modellene som er i bruk i virksomheten (mindre modeller trenger mer
eksplisitt veiledning, større modeller mindre). Kjør som minimum golden
settet på den minste og den største modellen i bruk før deling, og på nytt
når standardmodellen i virksomheten byttes. Jf. modellvelger-skillen for
hvilke modeller som faktisk brukes til hva.

## 7. Triggering-måling

Beskrivelsen i frontmatter er skillens ENESTE triggerflate – Claude velger
skill ut fra navn + beskrivelse alene, i konkurranse med alle andre
installerte skills. Mål derfor:

- 20 realistiske spørringer: 10 skal-treffe (ulike formuleringer, også uten
  at skillen nevnes ved navn) og 10 skal-ikke-treffe. De verdifulle
  negativene er **nesten-treff** – nabooppgaver som deler nøkkelord, men hvor
  en annen skill/verktøy er riktig. Åpenbart irrelevante spørringer måler
  ingenting.
- 3 kjøringer per spørring (triggering er også stokastisk). Rapportér andel
  riktig per klasse (presisjon/dekning).
- Enkle ett-stegs spørringer trigger sjelden skills uansett beskrivelse –
  bruk substansielle oppgaver som testcase.
- skill-creators beskrivelses-optimalisering automatiserer forbedringssløyfen
  (60/40 train/test-splitt så beskrivelsen ikke overtilpasses testsettet).
- Overlapp med søsterskills (her: pptx, bdo-design, docx) skal testes
  eksplisitt: legg konkurrerende formuleringer i settet og definér hvilken
  skill som SKAL vinne.
