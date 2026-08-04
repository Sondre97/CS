# CS – Claude Skills med måling

Delte Claude-skills for BDO-arbeidsflyter, med et felles rammeverk for å
**måle** dem før og etter deling. Prinsippet: en skill som deles i
virksomheten er et produkt, ikke en prompt – den har eier, versjon, testsett
og akseptkriterier.

## Innhold

| Sti | Hva |
|---|---|
| `skills/pptx-brand/` | Skill: BDO-brandede PowerPoint-presentasjoner. Inkluderer deterministisk merkevaresjekk (`scripts/check_brand.py`) og eget golden set (`evals/`) |
| `skills/skill-evaluator/` | Skill: det generelle målerammeverket – fem dimensjoner, grader-hierarki, akseptterskler, styring. Templates for golden set og scorecard |
| `docs/skill-maling.md` | Rammeverket med kildegrunnlag (Anthropic, OpenAI, Zheng et al., τ-bench, HELM, Kirkpatrick, NIST AI RMF m.fl.) |
| `eval-runs/` | Benchmark-kjøringer per skill og iterasjon (med/uten skill, grading, benchmark.json) |

## Kom i gang

Installer en skill ved å kopiere katalogen til `~/.claude/skills/` (Claude
Code) eller pakke den med skill-creators `package_skill.py` og laste opp
(claude.ai). Merk: skills synkroniseres ikke på tvers av flater – dette
repoet er distribusjonskanalen, og endringer skal inn her via PR.

## Kvalitetsregler for delte skills

1. Hver skill har navngitt eier og CHANGELOG.
2. Ny skill deles først når akseptgaten i `skill-evaluator` er passert
   (golden set mot baseline, triggersett, scorecard).
3. Endringer kjører regresjon (samme golden set) før merge.
4. Kvartalsvis: re-kjør settene (modell-/miljødrift) og revider scorecardene.

Detaljer og begrunnelser: `docs/skill-maling.md`.
