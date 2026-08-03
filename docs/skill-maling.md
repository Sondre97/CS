# Måling av skills – rammeverk og kilder

Hvordan måler man om en Claude-skill er god – før den deles i virksomheten,
og etter? Dette dokumentet samler det som faktisk er alminnelig akseptert
praksis på tvers av Anthropic, OpenAI, akademia og verktøyleverandørene, med
kildehenvisninger. Den operative kortversjonen ligger i skillen
`skill-evaluator`; dette er begrunnelsen og kildegrunnlaget.

Alle URL-er er verifisert 2026-08-03. To av Anthropic-bloggpostene (merket ✻)
er verifisert på tittel/URL via Anthropics egne sider, mens innholdsdetaljene
er kryssjekket mot flere uavhengige gjengivelser.

---

## 1. Grunnprinsippet: eval-drevet utvikling med baseline

Det mest entydige rådet i kildene: **lag evalueringene før du polerer
skillen, og mål alltid mot en baseline uten skillen.**

- Anthropics offisielle veiledning for skill-forfattere sier eksplisitt
  «Create evaluations *before* writing extensive documentation», og
  beskriver sløyfen: kjør Claude på representative oppgaver *uten* skillen og
  dokumentér feilene → bygg ~tre scenarioer som tester hullene → etabler
  baseline → skriv minimale instruksjoner som lukker gapet → iterér mot
  baselinen. Og: «Evaluations are your source of truth for measuring Skill
  effectiveness.» [K2]
- Samme doktrine hos OpenAI: «evaluate early and often», eval-drevet
  utvikling med skopede tester i hvert steg – særlig ved modellbytte, som i
  praksis er hovedgrunnen til at en delt skill endrer atferd uten at noen har
  rørt den. [K6]
- Anthropics skill-lanseringspost: start med evaluering – kjør representative
  oppgaver, finn kapabilitetshull, bygg målrettede skills mot dem, og
  observer hvordan agenten faktisk bruker skillen. [K3 ✻]

**Konsekvens:** en skills verdi er ikke pass rate i seg selv, men *delta mot
baseline* – hva skillen tilfører ut over modellens grunnkompetanse. Anthropics
egen skill-creator operasjonaliserer dette ved å kjøre hver testoppgave i to
konfigurasjoner (med/uten skill, eller ny/gammel versjon) i parallelle,
uavhengige subagenter, og rapportere pass rate, tid og tokens per
konfigurasjon med snitt ± standardavvik og delta. [K11]

## 2. Fem måledimensjoner

Én enkelt score skjuler avveininger. HELM-prosjektet ved Stanford etablerte
prinsippet om **multi-metrikk-evaluering** – hver oppgave måles på flere
dimensjoner (nøyaktighet, kalibrering, robusthet, rettferdighet, bias,
toksisitet, effektivitet) nettopp så «metrics beyond accuracy don't fall to
the wayside». [K9] Oversatt til skills gir det scorecardet vårt fem
dimensjoner:

| Dimensjon | Spørsmål | Primærkilde |
|---|---|---|
| 1. Triggering | Utløses skillen når den skal – og bare da? | [K1] [K2] |
| 2. Effekt | Bedre resultat med enn uten? (delta mot baseline) | [K2] [K11] |
| 3. Pålitelighet | Samme kvalitet hver gang? (pass^k) | [K8] [K5 ✻] |
| 4. Kostnad | Tokens/tid for kvaliteten? | [K9] [K11] |
| 5. Forretningseffekt | Adopsjon, akseptrate, spart tid i drift | [K12] [K13] |

Dimensjon 1 er særegen for skills: beskrivelsen i frontmatter er skillens
eneste triggerflate – «Claude uses it to choose the right Skill from
potentially 100+ available Skills». [K1] Triggering er dermed en målbar
egenskap ved *beskrivelsen*, uavhengig av kvaliteten på selve innholdet, og
måles med skal-treffe/skal-ikke-treffe-spørringer der de verdifulle
negativene er nesten-treff (nabooppgaver der en annen skill er riktig).

## 3. Gradere: kode > modell > menneske

Anthropics evalueringsdokumentasjon [K4] gir taksonomien med avveininger:

1. **Kode-gradert** (eksakt match, skript): raskest, mest pålitelig, krever
   klare fasitsvar. Foretrekkes alltid der det går.
2. **Statistisk/likhetsbasert** (embedding-likhet, ROUGE): for
   konsistens-sjekker og sammendrag.
3. **Modell-gradert** (LLM-som-dommer): fleksibel og skalerbar for tone,
   struktur, relevans – men må selv testes.
4. **Menneske-gradert**: mest fleksibel og høyest kvalitet, men langsom og
   dyr – «last resort», og fasiten de andre kalibreres mot.

To presiseringer fra agent-eval-litteraturen:

- **Grader tilstand, ikke sluttmelding.** Anthropics agent-eval-post [K5 ✻]
  skiller programmatiske gradere som sjekker *utfallet i miljøet* (filen
  finnes, testene passerer, databasen stemmer) fra vurdering av agentens
  sluttmelding – som kan påstå suksess uten dekning. τ-bench graderer på
  samme måte: sluttilstand i databasen mot annotert måltilstand. [K8]
  For pptx-brand er `check_brand.py` nettopp en slik tilstandsgrader: den
  leser fonter, farger og format rett ut av filen.
- **LLM-dommere virker, med kjente forbehold.** Zheng et al. viste at sterke
  dommermodeller når over 80 % enighet med menneskelige preferanser – samme
  nivå som mennesker imellom – men dokumenterte systematiske skjevheter:
  posisjonsbias, lengdebias, egenpreferanse, og svak grading av
  matte/resonnering (som derfor graderes med kode). [K7] G-Eval-mønsteret –
  kriterier + stegvis resonnering + strukturert skjemautfylling – er
  standardoppskriften for rubrikk-dommere. [K10] OpenAI anbefaler i tillegg
  parvis sammenlikning og klassifisering fremfor fri scoring, fordi det
  diskriminerer bedre. [K6]

Anthropics volum-råd binder det sammen: «prioritize volume over quality:
more questions with slightly lower signal automated grading is better than
fewer questions with high-quality human hand-graded evals.» [K4]

## 4. Pålitelighet: pass@k vs pass^k

Agentkjøringer er stokastiske, så hver oppgave kjøres flere ganger. Da må man
velge ærlig metrikk:

- **pass@k** – minst én av k kjøringer lykkes. Relevant når brukeren kan
  prøve igjen.
- **pass^k** – *alle* k kjøringer lykkes. Innført som hovedmetrikk i τ-bench
  [K8]; for en skill som deles i en virksomhet er dette den relevante
  metrikken, for én pinlig kundeleveranse veier tyngre enn et pent snitt.

De to divergerer dramatisk: τ-bench målte agenter med brukbar pass@1 som falt
under 25 % på pass^8 [K8], og Anthropics agent-eval-post viser at pass@k og
pass^k ved k=10 kan peke mot motsatte konklusjoner om samme system. [K5 ✻]
Praktisk minimum for oss: 3 kjøringer per oppgave per konfigurasjon, rapportér
snitt ± standardavvik + pass^k, og vær ærlig på at n=3 fanger store
forskjeller, ikke små.

## 5. To testsuiter: kapabilitet og regresjon

Fra Anthropics agent-eval-post [K5 ✻]:

- **Kapabilitetssett**: vanskelige oppgaver med lav pass rate (gjerne <10 %)
  som driver forbedring.
- **Regresjonssett**: alt som allerede virker, pinnet nær 100 %, kjørt ved
  hver endring av skillen og ved hvert modellbytte. Kapabilitetsoppgaver som
  når stabil høy pass rate «graduerer» inn i regresjonssettet.
- Metning er et faresignal (alt på 100 % = settet måler ingenting), og
  transkriptene skal leses «religiøst» – både for å forstå feil og for å
  avsløre juks: Anthropics egen interne case var en agent som skaffet seg
  urettmessig fordel ved å lese git-historikk som lå igjen fra tidligere
  kjøringer. Derav: isolér kjøremiljøene.

## 6. Skill-spesifikke målepunkter

Fra Anthropics skill-dokumentasjon [K1] [K2]:

- **Kryss-modell-testing**: en delt skill kjøres av den modellen brukeren
  har. Test på modellene i faktisk bruk (mindre modeller trenger mer
  veiledning; større trenger mindre).
- **Navigasjonsatferd som telemetri**: observer hvordan Claude beveger seg i
  skillen – leses referansefilene, hoppes skript over, leses for mye? Det er
  forbedringssignal på linje med pass rate.
- **To-Claude-iterasjon**: én Claude-instans er medforfatter av skillen, en
  frisk instans med skillen lastet observeres på reelle oppgaver – observerte
  feil (ikke antakelser) driver endringene.
- **Utrullingssjekkliste før deling** (Anthropics egen, lett tilpasset):
  minst tre evalueringer laget; testet på modellene i bruk; testet på reelle
  scenarioer; tilbakemeldinger fra teamet innarbeidet; SKILL.md under 500
  linjer; konsistent terminologi; ingen tidssensitive detaljer.

## 7. Forretningsnivået: måling etter deling

Eval-tallene sier om skillen *kan* levere; drift sier om den *gjør* det.

**Kirkpatricks fire nivåer** [K12] – standardrammeverket for måling av
opplærings-/kapabilitetstiltak i organisasjoner, innført 1959 og fortsatt
referansen – oversettes direkte:

| Nivå | Klassisk | For en delt skill |
|---|---|---|
| 1 Reaksjon | Likte de det? | Brukertilfredshet, villighet til å bruke skillen igjen |
| 2 Læring | Kan de mer? | Eval-delta mot baseline (dimensjon 2) |
| 3 Atferd | Gjør de det på jobb? | Adopsjon: andel relevante oppgaver der skillen faktisk trigges/brukes |
| 4 Resultat | Flyttet det forretningen? | Akseptrate uten omarbeid, spart tid per leveranse, kvalitet på utsendt materiale |

Moderne Kirkpatrick-praksis planlegger baklengs fra nivå 4: definér hvilket
forretningsresultat skillen skal flytte *før* den bygges.

**NIST AI Risk Management Framework** [K13] gir styringsspråket når skills
blir virksomhetsinfrastruktur: GOVERN (eierskap, roller, kultur – på tvers),
MAP (kontekst og risiko per skill), **MEASURE** (definerte metrikker og
benchmarks, sporing over tid, og meta-evaluering: virker målingen vår
fortsatt?), MANAGE (prioritere og respondere på det målingene viser).
Kvartalsrevisjonen av scorecardene er MEASURE/MANAGE i praksis. Trenger
virksomheten sertifiserbar styring, er **ISO/IEC 42001:2023** (ledelsessystem
for KI, PDCA-syklus) rammen revisor vil kjenne igjen. [K14]

**Sikkerhet ved deling**: Anthropic er eksplisitt på at skills skal behandles
som programvareinstallasjon – revider alle filer i skillen (særlig skript og
alt som henter eksterne URL-er) før den distribueres, og bruk kun kilder man
stoler på. [K1] Merk også at delingsmekanismen varierer per flate (claude.ai
= per bruker; API = workspace; Claude Code = kataloger/plugins) – skills
synkroniseres ikke magisk på tvers, så «delt i virksomheten» krever en
bevisst distribusjonskanal, f.eks. dette repoet. [K1]

## 8. Verktøy

- **skill-creator** (Anthropic, installert her): hele målesløyfen –
  parallelle med/uten-kjøringer, assertions, benchmark med snitt ± stddev,
  analyse av ikke-diskriminerende forventninger og flaky evals, eval-viewer
  for menneskelig gjennomgang, og optimalisering av beskrivelsen for
  triggering (60/40 train/test-splitt mot overtilpasning). [K11]
- Åpne rammeverk om målingen skal ut av Claude-økosystemet eller inn i CI:
  **promptfoo** (deklarative testcaser, CI/CD) [K15], **DeepEval**
  (pytest-stil, 30+ metrikker inkl. G-Eval) [K16], **Braintrust**
  (Eval(data, task, scores) + autoevals) [K17], **LangSmith** (datasett,
  dommere, annoteringskøer, offline regresjon vs online drift-måling) [K18],
  **OpenAI Evals** (rammeverk + benchmark-register) [K19]. NB: OpenAIs
  *hostede* eval-plattform er varslet avviklet (skrivebeskyttet 31.10.2026,
  nedstengt 30.11.2026) – metodikken består, verktøyvalget bør ikke lene seg
  på den. [K6]

## 9. Slik henger det sammen i dette repoet

- `skills/skill-evaluator/` – rammeverket som prosess: fem dimensjoner,
  grader-hierarki, akseptterskler, styring. Templates for golden set og
  scorecard.
- `skills/pptx-brand/` – første skill målt etter rammeverket: golden set i
  `evals/evals.json`, triggersett i `evals/trigger-evals.json`, og
  tilstandsgraderen `scripts/check_brand.py` som gjør merkevaren målbar
  (samme sjekk i produksjon som i eval – det som leveres er det som måles).
- `eval-runs/` – kjøringer og benchmark-resultater per iterasjon.

## Kilder

| # | Kilde | URL |
|---|---|---|
| K1 | Anthropic: Agent Skills – Overview (docs) | https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview |
| K2 | Anthropic: Skill authoring best practices (docs) | https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices |
| K3 ✻ | Anthropic Engineering: Equipping agents for the real world with Agent Skills (2025) | https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills |
| K4 | Anthropic: Define success criteria and build evaluations (docs; tidl. «Create strong empirical evaluations») | https://platform.claude.com/docs/en/test-and-evaluate/develop-tests |
| K5 ✻ | Anthropic Engineering: Demystifying evals for AI agents (jan. 2026) | https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents |
| K6 | OpenAI: Working with evals (docs) | https://developers.openai.com/api/docs/guides/evals |
| K7 | Zheng et al. (2023): Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena, NeurIPS 2023 | https://arxiv.org/abs/2306.05685 |
| K8 | Yao, Shinn et al. (2024): τ-bench – A Benchmark for Tool-Agent-User Interaction in Real-World Domains | https://arxiv.org/abs/2406.12045 |
| K9 | Liang, Bommasani, Lee et al.: Holistic Evaluation of Language Models (HELM), TMLR 2023 | https://crfm.stanford.edu/helm/ · https://arxiv.org/abs/2211.09110 |
| K10 | Liu et al. (2023): G-Eval – NLG Evaluation using GPT-4 with Better Human Alignment, EMNLP 2023 | https://arxiv.org/abs/2303.16634 |
| K11 | Anthropic: skill-creator (skills-repo med eval-/benchmark-metodikk) | https://github.com/anthropics/skills/tree/main/skills/skill-creator |
| K12 | Kirkpatrick Partners: The Kirkpatrick Model | https://www.kirkpatrickpartners.com/the-kirkpatrick-model/ |
| K13 | NIST: AI Risk Management Framework 1.0 (NIST AI 100-1, 2023) | https://www.nist.gov/itl/ai-risk-management-framework |
| K14 | ISO/IEC 42001:2023 – AI management systems | https://www.iso.org/standard/42001 |
| K15 | promptfoo | https://www.promptfoo.dev |
| K16 | DeepEval | https://github.com/confident-ai/deepeval |
| K17 | Braintrust (+ autoevals) | https://www.braintrust.dev |
| K18 | LangSmith: Evaluation concepts | https://docs.langchain.com/langsmith/evaluation-concepts |
| K19 | OpenAI Evals (repo) | https://github.com/openai/evals |
