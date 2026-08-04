// BA-analysen 2026 – 5 slides til partnermøtet, BDO-profil (pptx-brand, vei B: pptxgenjs).
// Alle farger og fonter settes eksplisitt (generert deck har ikke BDO-temaet fra malen;
// temaet patches i etterkant av patch_brand.py slik at også temafargene er BDO).
const pptxgen = require("pptxgenjs");
const fs = require("fs");
const path = require("path");

// ---- BDO-fasit (bdo-design) -------------------------------------------------
const RED = "E81A3B";      // primær rød – aksent/høydepunkt
const DARK = "333333";     // all brødtekst
const SLATE = "5B6E7F";    // sekundær
const GREEN = "009966";    // positiv
const LIGHT = "F2F2F2";    // lyse flater
const REDTINT = "FDE8EB";  // 10 % tint av E81A3B (lys rød flate bak nøkkeltall)
const GRAY = "808080";     // nøytral – kildehenvisninger
const AXIS = "D0CECE";     // nøytral – akselinje
const RESTGRAY = "D9D9D9"; // nøytral – donut-rest
const FONT = "Trebuchet MS";

const W = 13.333, H = 7.5;
const MX = 0.6;                 // venstre/høyre marg
const CW = W - 2 * MX;          // full innholdsbredde (12.13)
const icon = (name) => path.join(__dirname, "icons", `${name}.png`);
const b64 = (p) => "image/png;base64," + fs.readFileSync(p).toString("base64");

const pptx = new pptxgen();
pptx.defineLayout({ name: "BDO169", width: W, height: H });
pptx.layout = "BDO169";
pptx.theme = { headFontFace: FONT, bodyFontFace: FONT };
pptx.author = "BDO";
pptx.company = "BDO";
pptx.subject = "BDOs bygg- og anleggsanalyse 2026";
pptx.title = "BA-analysen 2026 – hovedfunn til partnermøtet";

pptx.defineSlideMaster({
  title: "BDO Innhold",
  background: { color: "FFFFFF" },
  margin: [0.5, 0.5, 0.5, 0.5],
});

// ---- felleselementer --------------------------------------------------------
function baseSlide(kicker, title) {
  const s = pptx.addSlide({ masterName: "BDO Innhold" });
  s.addText(kicker, {
    x: MX, y: 0.38, w: CW, h: 0.32, margin: 0,
    fontFace: FONT, fontSize: 11, bold: true, color: SLATE, charSpacing: 2,
  });
  s.addText(title, {
    x: MX, y: 0.7, w: CW, h: 0.98, margin: 0, valign: "top",
    fontFace: FONT, fontSize: 28, bold: true, color: DARK,
  });
  return s;
}

function sourceNote(s, x, y, w, align = "left") {
  s.addText("Kilde: BDOs bygg- og anleggsanalyse 2026", {
    x, y, w, h: 0.3, margin: 0, align,
    fontFace: FONT, fontSize: 9.5, color: GRAY,
  });
}

function circleIcon(s, name, cx, cy, d = 0.46) {
  s.addShape(pptx.shapes.OVAL, { x: cx, y: cy, w: d, h: d, fill: { color: RED } });
  const pad = d * 0.24;
  s.addImage({ data: b64(icon(name)), x: cx + pad, y: cy + pad, w: d - 2 * pad, h: d - 2 * pad });
}

// ============================================================================
// SLIDE 1 – Vekst, men marginpress
// ============================================================================
{
  const s = baseSlide("BA-ANALYSEN 2026  ·  HOVEDFUNN 1", "Næringen vokser, men lønnsomheten faller");

  s.addText(
    "Omsetningen i bygg- og anleggsnæringen økte med 4,2 prosent i fjor. Samtidig falt driftsmarginen fra 3,8 til 3,1 prosent – kostnadsveksten spiser mer enn veksten gir.",
    { x: MX, y: 1.92, w: 5.75, h: 1.5, margin: 0, valign: "top", fontFace: FONT, fontSize: 14, color: DARK, lineSpacingMultiple: 1.12 }
  );

  // KPI-kort
  const kpi = [
    { x: MX, num: "+4,2 %", numColor: GREEN, label: "omsetningsvekst siste år" },
    { x: 3.57, num: "3,1 %", numColor: RED, label: "driftsmargin – ned fra 3,8 %" },
  ];
  kpi.forEach((k) => {
    s.addShape(pptx.shapes.ROUNDED_RECTANGLE, { x: k.x, y: 3.6, w: 2.78, h: 1.95, rectRadius: 0.08, fill: { color: LIGHT } });
    s.addText(k.num, { x: k.x + 0.2, y: 3.85, w: 2.38, h: 0.75, margin: 0, fontFace: FONT, fontSize: 34, bold: true, color: k.numColor });
    s.addText(k.label, { x: k.x + 0.2, y: 4.62, w: 2.38, h: 0.72, margin: 0, valign: "top", fontFace: FONT, fontSize: 10.5, color: SLATE, lineSpacingMultiple: 1.05 });
  });

  s.addText("Vekst er ikke lenger noen garanti for lønnsomhet.", {
    x: MX, y: 5.85, w: 5.75, h: 0.45, margin: 0, fontFace: FONT, fontSize: 13, italic: true, color: DARK,
  });

  // Graf: driftsmargin i fjor vs. i år (endring mellom to punkter, få perioder -> kolonner)
  s.addText("Driftsmargin i næringen, prosent av omsetning", {
    x: 6.85, y: 1.92, w: 5.85, h: 0.38, margin: 0, fontFace: FONT, fontSize: 12.5, bold: true, color: DARK,
  });
  s.addChart(pptx.charts.BAR, [
    { name: "Driftsmargin", labels: ["I fjor", "I år"], values: [3.8, 3.1] },
  ], {
    x: 6.85, y: 2.4, w: 5.85, h: 4.1,
    barDir: "col", barGapWidthPct: 80,
    chartColors: [SLATE, RED],
    catAxisLabelColor: DARK, catAxisLabelFontFace: FONT, catAxisLabelFontSize: 13,
    catAxisLineColor: AXIS,
    valAxisHidden: true, valAxisMinVal: 0, valAxisMaxVal: 4.5,
    valGridLine: { style: "none" }, catGridLine: { style: "none" },
    showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: '0.0" %"',
    dataLabelColor: DARK, dataLabelFontFace: FONT, dataLabelFontSize: 14, dataLabelFontBold: true,
    showLegend: false, showTitle: false,
  });
  sourceNote(s, 6.85, 6.68, 5.85);

  s.addNotes(
    "Hovedbudskap: aktiviteten holder seg oppe, men lønnsomheten svekkes. Omsetningsvekst på 4,2 prosent i fjor, mens driftsmarginen falt fra 3,8 til 3,1 prosent. " +
    "Poeng til partnerne: topplinjevekst hos kundene må ikke leses som friskmelding – marginbildet avgjør."
  );
}

// ============================================================================
// SLIDE 2 – Konkurser +18 %, særlig underentreprenører
// ============================================================================
{
  const s = baseSlide("BA-ANALYSEN 2026  ·  HOVEDFUNN 2", "Konkursveksten treffer underentreprenørene hardest");

  // Stort nøkkeltall på lys rød flate
  s.addShape(pptx.shapes.ROUNDED_RECTANGLE, { x: MX, y: 1.9, w: 4.5, h: 4.95, rectRadius: 0.1, fill: { color: REDTINT } });
  s.addText("+18 %", { x: 0.85, y: 2.95, w: 4.0, h: 1.2, margin: 0, align: "center", fontFace: FONT, fontSize: 64, bold: true, color: RED });
  s.addText([
    { text: "flere konkurser i bygg", options: { breakLine: true } },
    { text: "og anlegg siste år" },
  ], {
    x: 1.0, y: 4.35, w: 3.7, h: 0.75, margin: 0, align: "center", valign: "top", fontFace: FONT, fontSize: 14, color: DARK, lineSpacingMultiple: 1.1,
  });
  s.addText("Økningen er størst i underentreprenørleddet", {
    x: 1.0, y: 5.2, w: 3.7, h: 0.6, margin: 0, align: "center", valign: "top", fontFace: FONT, fontSize: 10.5, color: SLATE,
  });
  sourceNote(s, 1.0, 6.35, 3.7, "center");

  // Tre forhold som gjør underentreprenørene utsatt
  s.addText(
    "Konkursene øker i hele næringen, men mest der bufferne er minst. Tre forhold gjør underentreprenørene særlig utsatt:",
    { x: 5.65, y: 1.9, w: 7.05, h: 0.9, margin: 0, valign: "top", fontFace: FONT, fontSize: 13.5, color: DARK, lineSpacingMultiple: 1.12 }
  );

  const rows = [
    { y: 3.0, ic: "link-2", h: "Sist i oppgjørskjeden", t: "Endringsordrer og sluttoppgjør skyves nedover i kontraktskjeden, og likviditetsbelastningen lander hos de minste." },
    { y: 4.35, ic: "trending-down", h: "Tynnest marginer", t: "Marginpresset gir minst buffer i leddet som allerede tjener minst – små prosjektavvik gir tap." },
    { y: 5.7, ic: "alert-triangle", h: "Kort vei til stans", t: "Uten reserver er veien fra forsinket oppgjør til betalingsstans kort." },
  ];
  rows.forEach((r) => {
    circleIcon(s, r.ic, 5.65, r.y + 0.04);
    s.addText(r.h, { x: 6.32, y: r.y, w: 6.35, h: 0.32, margin: 0, fontFace: FONT, fontSize: 14, bold: true, color: DARK });
    s.addText(r.t, { x: 6.32, y: r.y + 0.34, w: 6.35, h: 0.85, margin: 0, valign: "top", fontFace: FONT, fontSize: 12, color: DARK, lineSpacingMultiple: 1.1 });
  });

  s.addNotes(
    "Konkursene økte med 18 prosent siste år, og mest blant underentreprenørene. Mekanismen: oppgjør og endringsordrer forsinkes nedover i kjeden, og leddet med tynnest marginer og svakest likviditet rammes først. " +
    "Relevant for porteføljevurdering, going concern-vurderinger og kredittdialogen."
  );
}

// ============================================================================
// SLIDE 3 – 34 % bruker AI i prosjektering
// ============================================================================
{
  const s = baseSlide("BA-ANALYSEN 2026  ·  HOVEDFUNN 3", "Hvert tredje selskap bruker nå AI i prosjekteringen");

  // Donut (del av helhet, 2 deler) med nøkkeltall i midten
  s.addChart(pptx.charts.DOUGHNUT, [
    { name: "AI i prosjektering", labels: ["Bruker AI i prosjektering", "Bruker ikke AI"], values: [34, 66] },
  ], {
    x: MX, y: 2.05, w: 4.7, h: 4.25,
    holeSize: 62, chartColors: [RED, RESTGRAY],
    dataBorder: { pt: 1.5, color: "FFFFFF" },
    showLegend: false, showValue: false, showLabel: false, showPercent: false, showTitle: false,
    dataLabelFontFace: FONT, dataLabelColor: DARK, firstSliceAng: 0,
  });
  s.addText("34 %", { x: 1.85, y: 3.8, w: 2.2, h: 0.75, margin: 0, align: "center", valign: "middle", fontFace: FONT, fontSize: 34, bold: true, color: RED });
  s.addText("Andel som bruker AI i prosjektering. Kilde: BDOs bygg- og anleggsanalyse 2026", {
    x: MX, y: 6.5, w: 4.7, h: 0.55, margin: 0, align: "center", valign: "top", fontFace: FONT, fontSize: 9.5, color: GRAY, lineSpacingMultiple: 1.1,
  });

  s.addText(
    "I årets undersøkelse oppgir 34 prosent av selskapene at de bruker AI i prosjekteringen. Teknologien er på vei fra utprøving til standard arbeidsmåte i tidligfasen.",
    { x: 5.85, y: 2.05, w: 6.85, h: 1.35, margin: 0, valign: "top", fontFace: FONT, fontSize: 14, color: DARK, lineSpacingMultiple: 1.12 }
  );
  s.addText(
    "Selskapene som har kommet lengst, henter gevinstene i raskere kalkyler, færre feil og bedre beslutningsgrunnlag før byggestart.",
    { x: 5.85, y: 3.5, w: 6.85, h: 1.1, margin: 0, valign: "top", fontFace: FONT, fontSize: 14, color: DARK, lineSpacingMultiple: 1.12 }
  );

  s.addShape(pptx.shapes.ROUNDED_RECTANGLE, { x: 5.85, y: 4.85, w: 6.85, h: 1.7, rectRadius: 0.1, fill: { color: LIGHT } });
  circleIcon(s, "cpu", 6.15, 5.47);
  s.addText("To av tre står fortsatt utenfor", { x: 6.85, y: 5.12, w: 5.6, h: 0.32, margin: 0, fontFace: FONT, fontSize: 14, bold: true, color: DARK });
  s.addText("Det gir et forsprang til dem som effektiviserer nå – og et stort mulighetsrom for resten.", {
    x: 6.85, y: 5.46, w: 5.6, h: 0.85, margin: 0, valign: "top", fontFace: FONT, fontSize: 12, color: DARK, lineSpacingMultiple: 1.1,
  });

  s.addNotes(
    "34 prosent bruker AI i prosjekteringen – teknologien går fra pilot til praksis. To av tre står fortsatt utenfor, og der ligger både konkurranserisikoen for kundene og rådgivningsrommet for oss."
  );
}

// ============================================================================
// SLIDE 4 – Anbefaling: tettere likviditetsoppfølging
// ============================================================================
{
  const s = baseSlide("BA-ANALYSEN 2026  ·  ANBEFALING", "Utsatte kunder bør følges tettere på likviditet");

  s.addText(
    "Marginpress og konkursvekst flytter risikoen mot kundene med svakest buffere. Analysen anbefaler tettere likviditetsoppfølging – for rådgiver betyr det tre grep:",
    { x: MX, y: 1.92, w: CW, h: 0.85, margin: 0, valign: "top", fontFace: FONT, fontSize: 14, color: DARK, lineSpacingMultiple: 1.12 }
  );

  const cards = [
    { n: "1", h: "Identifiser de utsatte", t: "Kartlegg porteføljen mot funnene: fallende driftsmargin, svak arbeidskapital og høy eksponering mot underentrepriser." },
    { n: "2", h: "Følg likviditeten tett", t: "Etabler rullerende likviditetsprognoser og fast gjennomgang med kunden – månedlig rytme, ikke bare ved årsoppgjør." },
    { n: "3", h: "Ta dialogen tidlig", t: "Reforhandling, refinansiering og kostnadstiltak virker best før betalingsproblemene er et faktum." },
  ];
  cards.forEach((c, i) => {
    const x = MX + i * 4.13;
    s.addShape(pptx.shapes.ROUNDED_RECTANGLE, { x, y: 2.95, w: 3.87, h: 3.55, rectRadius: 0.1, fill: { color: LIGHT } });
    s.addShape(pptx.shapes.OVAL, { x: x + 0.32, y: 3.3, w: 0.5, h: 0.5, fill: { color: RED } });
    s.addText(c.n, { x: x + 0.32, y: 3.3, w: 0.5, h: 0.5, margin: 0, align: "center", valign: "middle", fontFace: FONT, fontSize: 18, bold: true, color: "FFFFFF" });
    s.addText(c.h, { x: x + 0.32, y: 4.05, w: 3.25, h: 0.4, margin: 0, fontFace: FONT, fontSize: 15, bold: true, color: DARK });
    s.addText(c.t, { x: x + 0.32, y: 4.5, w: 3.25, h: 1.8, margin: 0, valign: "top", fontFace: FONT, fontSize: 12.5, color: DARK, lineSpacingMultiple: 1.12 });
  });

  s.addNotes(
    "Analysens anbefaling: tettere likviditetsoppfølging hos utsatte kunder. Operasjonalisert i tre grep – identifiser risikokundene, etabler rullerende likviditetsprognoser, og ta dialogen om tiltak før betalingsproblemene inntreffer."
  );
}

// ============================================================================
// SLIDE 5 – Hva funnene betyr for BDOs rådgivningsarbeid
// ============================================================================
{
  const s = baseSlide("BA-ANALYSEN 2026  ·  BETYDNING FOR BDO", "Funnene peker ut tre satsinger for rådgivningen");

  s.addText(
    "For BDO er analysen mer enn en statusrapport – den viser hvor kundene trenger oss mest det neste året:",
    { x: MX, y: 1.92, w: CW, h: 0.6, margin: 0, valign: "top", fontFace: FONT, fontSize: 14, color: DARK }
  );

  const cards = [
    { ic: "life-buoy", h: "Likviditet og restrukturering", t: "Konkursveksten gir økt behov for tidlig restruktureringsbistand. Prioriter kundene med svakest buffere." },
    { ic: "message-circle", h: "Innsikt i kundedialogen", t: "Bruk funnene som faktagrunnlag i styremøter, kredittdialog og tilbud – analysen åpner dører hos kunder og banker." },
    { ic: "cpu", h: "AI-rådgivning i prosjektering", t: "To av tre selskaper har ennå ikke tatt steget. Teknologivalg, prosess og gevinstuttak blir et voksende rådgivningsområde." },
  ];
  cards.forEach((c, i) => {
    const x = MX + i * 4.13;
    s.addShape(pptx.shapes.ROUNDED_RECTANGLE, { x, y: 2.75, w: 3.87, h: 3.4, rectRadius: 0.1, fill: { color: LIGHT } });
    circleIcon(s, c.ic, x + 0.32, 3.07, 0.5);
    s.addText(c.h, { x: x + 0.32, y: 3.8, w: 3.25, h: 0.65, margin: 0, valign: "top", fontFace: FONT, fontSize: 15, bold: true, color: DARK, lineSpacingMultiple: 1.05 });
    s.addText(c.t, { x: x + 0.32, y: 4.5, w: 3.25, h: 1.55, margin: 0, valign: "top", fontFace: FONT, fontSize: 12.5, color: DARK, lineSpacingMultiple: 1.12 });
  });

  s.addText([
    { text: "Funnene gir konkrete knagger for høstens kundedialog: ", options: { bold: true, color: DARK } },
    { text: "likviditet der risikoen er størst, teknologi der mulighetene er størst.", options: { bold: true, color: RED } },
  ], { x: MX, y: 6.5, w: CW, h: 0.55, margin: 0, valign: "top", fontFace: FONT, fontSize: 14 });

  s.addNotes(
    "Avslutning: funnene omsatt til rådgivningsarbeidet. Tre satsinger – restrukturering og likviditetsbistand der risikoen er størst, BA-analysen som døråpner i kundedialogen, og AI-rådgivning i prosjektering som vekstområde. " +
    "Neste steg: bruk analysen aktivt i høstens kundemøter."
  );
}

pptx.writeFile({ fileName: path.join(__dirname, "ba2026_partner.pptx") }).then((f) => console.log("wrote", f));
