// Kvartalspresentasjon Q2 2026 – Forretningsområde Rådgivning (BDO, internt ledermøte)
const pptxgen = require("pptxgenjs");

const p = new pptxgen();
p.layout = "LAYOUT_WIDE"; // 13.33 x 7.5
p.author = "BDO Radgivning";
p.company = "BDO";
p.title = "Kvartalsstatus Q2 2026 - Radgivning";

// BDO-farger
const RED = "ED1A3B"; // BDO-rød
const DARKBG = "26262E"; // mørk koks
const CARDDARK = "32323C";
const INK = "2E2E38"; // tekst
const MUTED = "6A6A72"; // dempet tekst
const LIGHT = "F4F4F6"; // lys kortbakgrunn
const TINT = "FCE8EC"; // lys rød tint
const GRAY = "C7C9D1"; // grå søyler (budsjett/mål)
const FOOT = "9A9AA2";
const DARKMUTED = "ABABB6";
const DARKBODY = "C9C9D2";
const F = "Arial";

function footer(slide, num, dark) {
  const c = dark ? "8A8A94" : FOOT;
  slide.addText("BDO Rådgivning – Kvartalsstatus Q2 2026", {
    x: 0.6, y: 7.06, w: 5.5, h: 0.28, fontFace: F, fontSize: 9, color: c, align: "left", margin: 0,
  });
  slide.addText(String(num), {
    x: 12.3, y: 7.06, w: 0.43, h: 0.28, fontFace: F, fontSize: 9, color: c, align: "right", margin: 0,
  });
}

function bdoMark(slide) {
  slide.addText("BDO", {
    x: 11.75, y: 0.45, w: 0.98, h: 0.4, fontFace: F, fontSize: 20, bold: true, color: RED, align: "right", margin: 0,
  });
}

function headerBlock(slide, title, subtitle) {
  slide.addText(title, {
    x: 0.6, y: 0.42, w: 11.0, h: 0.55, fontFace: F, fontSize: 27, bold: true, color: INK, align: "left", margin: 0,
  });
  slide.addText(subtitle, {
    x: 0.6, y: 1.0, w: 11.0, h: 0.35, fontFace: F, fontSize: 13, color: MUTED, align: "left", margin: 0,
  });
}

// ---------------------------------------------------------------- Slide 1: Tittel
{
  const s = p.addSlide();
  s.background = { color: DARKBG };

  s.addText("BDO", { x: 0.6, y: 0.5, w: 2.0, h: 0.6, fontFace: F, fontSize: 34, bold: true, color: RED, align: "left", margin: 0 });

  s.addText("FORRETNINGSOMRÅDE RÅDGIVNING", {
    x: 0.6, y: 2.0, w: 9.5, h: 0.4, fontFace: F, fontSize: 13, bold: true, color: RED, charSpacing: 3, align: "left", margin: 0,
  });
  s.addText("Kvartalsstatus Q2 2026", {
    x: 0.6, y: 2.4, w: 11.5, h: 0.95, fontFace: F, fontSize: 44, bold: true, color: "FFFFFF", align: "left", margin: 0,
  });
  s.addText("Internt ledermøte · august 2026", {
    x: 0.6, y: 3.5, w: 9.0, h: 0.4, fontFace: F, fontSize: 14, color: DARKMUTED, align: "left", margin: 0,
  });

  const stats = [
    { x: 0.6, v: "182 MNOK", c: RED, l: "omsetning i Q2" },
    { x: 4.55, v: "104 %", c: "FFFFFF", l: "av budsjett" },
    { x: 8.5, v: "78 %", c: "FFFFFF", l: "utfaktureringsgrad" },
  ];
  stats.forEach((st) => {
    s.addText(st.v, { x: st.x, y: 5.25, w: 3.6, h: 0.55, fontFace: F, fontSize: 30, bold: true, color: st.c, align: "left", margin: 0 });
    s.addText(st.l, { x: st.x, y: 5.85, w: 3.6, h: 0.35, fontFace: F, fontSize: 12, color: DARKMUTED, align: "left", margin: 0 });
  });

  s.addNotes("Statusgjennomgang for forretningsområdet Rådgivning, andre kvartal 2026. Hovedbudskap: sterk vekst, drift over budsjett og bedring på alle nøkkeltall.");
}

// ---------------------------------------------------------------- Slide 2: Hovedtall (KPI-kort)
{
  const s = p.addSlide();
  s.background = { color: "FFFFFF" };
  headerBlock(s, "Hovedtall Q2 – fremgang på alle nøkkeltall", "Rådgivning · andre kvartal 2026, endring mot Q1");
  bdoMark(s);

  const xs = [0.6, 4.74, 8.88];
  const W = 3.85, H = 2.3, Y1 = 1.75, Y2 = 4.35;

  function card(x, y, label, valueRuns, deltaRuns, fillColor, labelColor) {
    const runs = [
      { text: label, options: { fontFace: F, fontSize: 10, bold: true, color: labelColor || MUTED, charSpacing: 1.2, breakLine: true, paraSpaceAfter: 10 } },
      ...valueRuns,
      ...deltaRuns,
    ];
    s.addText(runs, {
      shape: p.shapes.ROUNDED_RECTANGLE, rectRadius: 0.07, fill: { color: fillColor || LIGHT },
      x: x, y: y, w: W, h: H, align: "left", valign: "middle", margin: 16,
    });
  }

  const val = (t) => ({ text: t, options: { fontFace: F, fontSize: 34, bold: true, color: INK, breakLine: false } });
  const unit = (t) => ({ text: t, options: { fontFace: F, fontSize: 15, bold: true, color: INK, breakLine: true, paraSpaceAfter: 8 } });
  const up = () => ({ text: "▲ ", options: { fontFace: F, fontSize: 11, bold: true, color: RED, breakLine: false } });
  const down = () => ({ text: "▼ ", options: { fontFace: F, fontSize: 11, bold: true, color: RED, breakLine: false } });
  const dtxt = (t, last) => ({ text: t, options: { fontFace: F, fontSize: 11, color: MUTED, breakLine: !last ? true : false, paraSpaceAfter: 4 } });

  card(xs[0], Y1, "OMSETNING", [val("182"), unit(" MNOK")], [
    up(), dtxt("+18 MNOK mot Q1 (+11 %)"),
    { text: "+4 % over budsjett (175)", options: { fontFace: F, fontSize: 11, bold: true, color: RED } },
  ]);
  card(xs[1], Y1, "SNITT TIMEPRIS", [val("1 480"), unit(" kr")], [up(), dtxt("+25 kr mot Q1", true)]);
  card(xs[2], Y1, "UTFAKTURERINGSGRAD", [val("78"), unit(" %")], [up(), dtxt("+4 prosentpoeng mot Q1", true)]);

  card(xs[0], Y2, "NYANSETTELSER", [val("12"), unit(" i Q2")], [
    up(), dtxt("+4 mot Q1"),
    { text: "20 nyansatte hittil i år", options: { fontFace: F, fontSize: 11, color: MUTED } },
  ]);
  card(xs[1], Y2, "SYKEFRAVÆR", [val("3,1"), unit(" %")], [down(), dtxt("−0,3 prosentpoeng mot Q1", true)]);
  card(xs[2], Y2, "OPPSUMMERT", [], [
    { text: "Alle nøkkeltall i bedring – omsetningen endte 7 MNOK over budsjett.", options: { fontFace: F, fontSize: 13, color: INK, lineSpacingMultiple: 1.15 } },
  ], TINT, RED);

  footer(s, 2);
  s.addNotes("Alle fem nøkkeltall bedret seg fra Q1 til Q2. Omsetningen på 182 MNOK er 7 MNOK over budsjett og 18 MNOK over Q1.");
}

// ---------------------------------------------------------------- Slide 3: Omsetning (graf)
{
  const s = p.addSlide();
  s.background = { color: "FFFFFF" };
  headerBlock(s, "Omsetning godt over budsjett", "MNOK per kvartal – faktisk mot budsjett");
  bdoMark(s);

  s.addChart(p.ChartType.bar, [
    { name: "Faktisk", labels: ["Q1 2026", "Q2 2026"], values: [164, 182] },
    { name: "Budsjett", labels: ["Q1 2026", "Q2 2026"], values: [null, 175] },
  ], {
    x: 0.6, y: 1.9, w: 7.3, h: 4.6,
    barDir: "col", barGapWidthPct: 60, barOverlapPct: -15,
    chartColors: [RED, GRAY],
    showTitle: false,
    showLegend: true, legendPos: "b", legendFontSize: 11, legendColor: MUTED, legendFontFace: F,
    showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0", dataLabelColor: INK, dataLabelFontSize: 12, dataLabelFontBold: true, dataLabelFontFace: F,
    catAxisLabelColor: MUTED, catAxisLabelFontSize: 12, catAxisLabelFontFace: F, catAxisLineColor: "D9D9DE",
    valAxisHidden: true, valAxisMinVal: 0, valAxisMaxVal: 210,
    valGridLine: { style: "none" }, catGridLine: { style: "none" },
  });

  s.addText("104 %", { x: 8.35, y: 2.05, w: 4.35, h: 0.65, fontFace: F, fontSize: 38, bold: true, color: RED, align: "left", margin: 0 });
  s.addText("budsjettoppnåelse i Q2 – 182 MNOK mot budsjett på 175 MNOK", {
    x: 8.35, y: 2.75, w: 4.35, h: 0.65, fontFace: F, fontSize: 12, color: MUTED, align: "left", margin: 0,
  });

  s.addText("+11 %", { x: 8.35, y: 3.85, w: 4.35, h: 0.65, fontFace: F, fontSize: 38, bold: true, color: INK, align: "left", margin: 0 });
  s.addText("omsetningsvekst fra Q1 – en økning på 18 MNOK", {
    x: 8.35, y: 4.55, w: 4.35, h: 0.65, fontFace: F, fontSize: 12, color: MUTED, align: "left", margin: 0,
  });

  s.addText("Veksten er drevet av høyere utfaktureringsgrad og økt snitt timepris.", {
    x: 8.35, y: 5.6, w: 4.35, h: 0.85, fontFace: F, fontSize: 12.5, italic: true, color: MUTED, align: "left", margin: 0,
  });

  footer(s, 3);
  s.addNotes("Omsetningen i Q2 ble 182 MNOK – 4 % over budsjett og 11 % over Q1. Veksten er drevet av både høyere utfaktureringsgrad og økt timepris.");
}

// ---------------------------------------------------------------- Slide 4: Drift og medarbeidere (grafer)
{
  const s = p.addSlide();
  s.background = { color: "FFFFFF" };
  headerBlock(s, "Drift og medarbeidere i riktig retning", "Utvikling fra Q1 til Q2 2026");
  bdoMark(s);

  s.addText("Utfaktureringsgrad (%)", { x: 0.6, y: 1.58, w: 5.9, h: 0.32, fontFace: F, fontSize: 13, bold: true, color: INK, align: "left", margin: 0 });
  s.addChart(p.ChartType.bar, [
    { name: "Faktisk", labels: ["Q1 2026", "Q2 2026", "Mål Q3"], values: [74, 78, null] },
    { name: "Mål", labels: ["Q1 2026", "Q2 2026", "Mål Q3"], values: [null, null, 80] },
  ], {
    x: 0.6, y: 1.95, w: 5.9, h: 3.45,
    barDir: "col", barGapWidthPct: 80, barOverlapPct: 100,
    chartColors: [RED, GRAY],
    showTitle: false, showLegend: false,
    showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: '0" %"', dataLabelColor: INK, dataLabelFontSize: 12, dataLabelFontBold: true, dataLabelFontFace: F,
    catAxisLabelColor: MUTED, catAxisLabelFontSize: 12, catAxisLabelFontFace: F, catAxisLineColor: "D9D9DE",
    valAxisHidden: true, valAxisMinVal: 0, valAxisMaxVal: 92,
    valGridLine: { style: "none" }, catGridLine: { style: "none" },
  });

  s.addText("Nyansettelser (antall)", { x: 6.83, y: 1.58, w: 5.9, h: 0.32, fontFace: F, fontSize: 13, bold: true, color: INK, align: "left", margin: 0 });
  s.addChart(p.ChartType.bar, [
    { name: "Nyansettelser", labels: ["Q1 2026", "Q2 2026"], values: [8, 12] },
  ], {
    x: 6.83, y: 1.95, w: 5.9, h: 3.45,
    barDir: "col", barGapWidthPct: 120,
    chartColors: [RED],
    showTitle: false, showLegend: false,
    showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0", dataLabelColor: INK, dataLabelFontSize: 12, dataLabelFontBold: true, dataLabelFontFace: F,
    catAxisLabelColor: MUTED, catAxisLabelFontSize: 12, catAxisLabelFontFace: F, catAxisLineColor: "D9D9DE",
    valAxisHidden: true, valAxisMinVal: 0, valAxisMaxVal: 14,
    valGridLine: { style: "none" }, catGridLine: { style: "none" },
  });

  function strip(x, label, big, arrowRun, tail) {
    s.addText([
      { text: label, options: { fontFace: F, fontSize: 9.5, bold: true, color: MUTED, charSpacing: 1.2, breakLine: true, paraSpaceAfter: 6 } },
      { text: big, options: { fontFace: F, fontSize: 20, bold: true, color: INK, breakLine: false } },
      { text: "   " + arrowRun + " ", options: { fontFace: F, fontSize: 11, bold: true, color: RED, breakLine: false } },
      { text: tail, options: { fontFace: F, fontSize: 11, color: MUTED } },
    ], {
      shape: p.shapes.ROUNDED_RECTANGLE, rectRadius: 0.07, fill: { color: LIGHT },
      x: x, y: 5.62, w: 5.9, h: 1.1, align: "left", valign: "middle", margin: 16,
    });
  }
  strip(0.6, "SNITT TIMEPRIS", "1 480 kr", "▲", "+25 kr mot Q1 (1 455 kr)");
  strip(6.83, "SYKEFRAVÆR", "3,1 %", "▼", "−0,3 prosentpoeng mot Q1 (3,4 %)");

  footer(s, 4);
  s.addNotes("Utfaktureringsgraden økte fra 74 til 78 prosent – målet for Q3 er over 80. Tolv nyansettelser i Q2 mot åtte i Q1. Timeprisen opp 25 kroner, sykefraværet ned til 3,1 prosent.");
}

// ---------------------------------------------------------------- Slide 5: Prioriteringer Q3
{
  const s = p.addSlide();
  s.background = { color: DARKBG };

  s.addText("BDO", { x: 0.6, y: 0.5, w: 2.0, h: 0.5, fontFace: F, fontSize: 24, bold: true, color: RED, align: "left", margin: 0 });

  s.addText("Prioriteringer for Q3", {
    x: 0.6, y: 0.95, w: 11.5, h: 0.7, fontFace: F, fontSize: 34, bold: true, color: "FFFFFF", align: "left", margin: 0,
  });
  s.addText("Tre hovedgrep for tredje kvartal 2026", {
    x: 0.6, y: 1.68, w: 11.5, h: 0.4, fontFace: F, fontSize: 14, color: DARKMUTED, align: "left", margin: 0,
  });

  const xs = [0.6, 4.74, 8.88];
  const cards = [
    { n: "1", t: "Rekruttering av seniorer", d: "Målrettet rekruttering av erfarne rådgivere for å sikre leveransekapasitet og kvalitet i takt med veksten." },
    { n: "2", t: "Etablere CSRD-team", d: "Dedikert team for bærekraftsrapportering som posisjonerer oss for økende etterspørsel etter CSRD-tjenester." },
    { n: "3", t: "Utfakturering over 80 %", d: "Løfte utfaktureringsgraden fra 78 % til over 80 % gjennom tettere kapasitetsstyring og prioritering av fakturerbare timer." },
  ];

  cards.forEach((c, i) => {
    const x = xs[i];
    s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: x, y: 2.35, w: 3.85, h: 3.75, rectRadius: 0.09, fill: { color: CARDDARK } });
    s.addText(c.n, {
      shape: p.shapes.OVAL, fill: { color: RED },
      x: x + 0.32, y: 2.72, w: 0.62, h: 0.62,
      fontFace: F, fontSize: 22, bold: true, color: "FFFFFF", align: "center", valign: "middle", margin: 0,
    });
    s.addText(c.t, {
      x: x + 0.32, y: 3.55, w: 3.2, h: 0.65, fontFace: F, fontSize: 17, bold: true, color: "FFFFFF", align: "left", valign: "top", margin: 0,
    });
    s.addText(c.d, {
      x: x + 0.32, y: 4.25, w: 3.2, h: 1.6, fontFace: F, fontSize: 12, color: DARKBODY, align: "left", valign: "top", margin: 0, lineSpacingMultiple: 1.2,
    });
  });

  footer(s, 5, true);
  s.addNotes("Tre prioriteringer for Q3: målrettet rekruttering av seniorer, etablering av et dedikert CSRD-team, og å løfte utfaktureringsgraden til over 80 prosent.");
}

p.writeFile({ fileName: "/home/user/CS/eval-runs/pptx-brand/iteration-1/eval-2-kvartalsstatus-radgivning/without_skill/run-1/outputs/q2_status_radgivning.pptx" })
  .then((f) => console.log("Wrote", f))
  .catch((e) => { console.error(e); process.exit(1); });
