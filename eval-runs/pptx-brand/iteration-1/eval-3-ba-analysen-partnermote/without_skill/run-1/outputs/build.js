/* BA-analysen 2026 – partnermøtedeck, BDO-profil (5 slides, 16:9) */
const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const Fi = require("react-icons/fi");
const sharp = require("sharp");

/* ---------- BDO palette ---------- */
const RED = "ED1A3B"; // BDO red
const RED_DARKSLIDE = "FF5A70"; // red with enough contrast on dark bg
const INK = "333333"; // charcoal text
const BODY = "55555A";
const MUTED = "6E6E73";
const FOOT = "8A8A8F";
const TINT = "F5F5F7"; // light grey card
const TINT_RED = "F9E9EC"; // light red tint card
const GREY_1 = "DEDEE3";
const GREY_2 = "CFCFD6";
const ARROW = "B9B9C1";
const DARK_BG = "26262C";
const DARK_CARD = "32323A";
const DARK_BODY = "C9C9D1";
const DARK_FOOT = "9B9BA3";
const FONT = "Trebuchet MS"; // BDO substitute font for Bliss

const W = 13.333;

/* ---------- icon rendering (react-icons -> png data uri) ---------- */
async function iconData(name) {
  const el = React.createElement(Fi[name], { size: 256, strokeWidth: 2 });
  let svg = ReactDOMServer.renderToStaticMarkup(el);
  svg = svg.replace(/currentColor/g, "#FFFFFF");
  const buf = await sharp(Buffer.from(svg)).resize(256, 256).png().toBuffer();
  return "image/png;base64," + buf.toString("base64");
}

/* ---------- shared chrome ---------- */
function chrome(slide, { kicker, title, page, dark = false }) {
  slide.background = { color: dark ? DARK_BG : "FFFFFF" };
  slide.addText(kicker, {
    x: 0.62, y: 0.46, w: 9.6, h: 0.3, margin: 0,
    fontFace: FONT, fontSize: 10, bold: true, charSpacing: 2,
    color: dark ? RED_DARKSLIDE : RED,
  });
  slide.addText(title, {
    x: 0.62, y: 0.8, w: 11.2, h: 0.92, margin: 0, valign: "top",
    fontFace: FONT, fontSize: 28, bold: true,
    color: dark ? "FFFFFF" : INK,
  });
  slide.addText("BDO", {
    x: 11.9, y: 0.44, w: 0.83, h: 0.42, margin: 0, align: "right", valign: "top",
    fontFace: FONT, fontSize: 19, bold: true,
    color: dark ? "FFFFFF" : RED,
  });
  slide.addText("BDO | BA-analysen 2026 · Partnermøte", {
    x: 0.62, y: 7.13, w: 6.0, h: 0.25, margin: 0,
    fontFace: FONT, fontSize: 8.5, color: dark ? DARK_FOOT : FOOT,
  });
  slide.addText(page + " / 5", {
    x: 11.73, y: 7.13, w: 1.0, h: 0.25, margin: 0, align: "right",
    fontFace: FONT, fontSize: 8.5, color: dark ? DARK_FOOT : FOOT,
  });
}

/* two-run paragraph: bold lead + regular rest */
function para(lead, rest, { last = false, dark = false } = {}) {
  return [
    {
      text: lead,
      options: {
        bold: true, color: dark ? "FFFFFF" : INK, fontFace: FONT,
        lineSpacingMultiple: 1.18,
      },
    },
    {
      text: rest,
      options: {
        color: dark ? DARK_BODY : BODY, fontFace: FONT,
        lineSpacingMultiple: 1.18, breakLine: true,
        paraSpaceAfter: last ? 0 : 14,
      },
    },
  ];
}

(async () => {
  const icons = {};
  for (const n of ["FiSearch", "FiActivity", "FiClock", "FiBarChart2", "FiShield", "FiDroplet", "FiCpu"]) {
    icons[n] = await iconData(n);
  }

  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5
  pres.theme = { headFontFace: FONT, bodyFontFace: FONT };
  pres.author = "BDO";
  pres.company = "BDO";
  pres.subject = "BA-analysen 2026";
  pres.title = "BA-analysen 2026 – hovedfunn til partnermøtet";

  /* ================= Slide 1 – vekst og marginpress ================= */
  {
    const s = pres.addSlide();
    chrome(s, { kicker: "BA-ANALYSEN 2026 · HOVEDFUNN 1 AV 4", title: "Omsetningen vokser – lønnsomheten faller", page: "1" });

    s.addText(
      [
        ...para("Omsetningsveksten ble 4,2 % ", "det siste året – aktivitetsnivået i bygg- og anleggsnæringen holder seg oppe."),
        ...para("Driftsmarginen falt fra 3,8 % til 3,1 %. ", "Kostnadsvekst og hard priskonkurranse presser lønnsomheten i alle ledd."),
        ...para("Vekst uten lønnsomhet: ", "næringen omsetter mer, men sitter igjen med mindre. Marginpresset er analysens tydeligste signal.", { last: true }),
      ],
      { x: 0.62, y: 1.95, w: 6.25, h: 4.7, margin: 0, valign: "middle", fontSize: 14.5 }
    );

    // stat card
    s.addShape(pres.ShapeType.roundRect, { x: 7.35, y: 1.85, w: 5.35, h: 1.45, rectRadius: 0.08, fill: { color: TINT_RED } });
    s.addText("+4,2 %", { x: 7.7, y: 2.0, w: 3.0, h: 0.62, margin: 0, fontFace: FONT, fontSize: 38, bold: true, color: RED });
    s.addText("omsetningsvekst i bygg- og anleggsnæringen siste år", {
      x: 7.7, y: 2.66, w: 4.7, h: 0.5, margin: 0, fontFace: FONT, fontSize: 11, color: MUTED,
    });

    // margin chart
    s.addText("Driftsmargin i næringen (%)", { x: 7.35, y: 3.62, w: 5.0, h: 0.3, margin: 0, fontFace: FONT, fontSize: 12.5, bold: true, color: INK });
    s.addChart(pres.ChartType.bar, [
      { name: "Driftsmargin", labels: ["I fjor", "Siste år"], values: [3.8, 3.1] },
    ], {
      x: 7.35, y: 3.98, w: 5.35, h: 2.85,
      barDir: "col", barGapWidthPct: 90,
      chartColors: [RED],
      showLegend: false, showTitle: false,
      showValue: true, dataLabelPosition: "outEnd", dataLabelColor: INK,
      dataLabelFontSize: 13, dataLabelFontBold: true, dataLabelFontFace: FONT,
      dataLabelFormatCode: '0.0" %"',
      valAxisHidden: true, valAxisMaxVal: 4.4, valAxisMinVal: 0,
      valGridLine: { style: "none" }, catGridLine: { style: "none" },
      catAxisLabelColor: BODY, catAxisLabelFontSize: 11.5, catAxisLabelFontFace: FONT,
      catAxisLineColor: "D8D8DC",
    });

    s.addNotes("Hovedbildet i BA-analysen 2026: aktiviteten holder seg oppe med 4,2 prosent omsetningsvekst, men driftsmarginen faller fra 3,8 til 3,1 prosent. Budskapet til partnergruppen: næringen vokser uten å tjene mer.");
  }

  /* ================= Slide 2 – konkurser ================= */
  {
    const s = pres.addSlide();
    chrome(s, { kicker: "BA-ANALYSEN 2026 · HOVEDFUNN 2 AV 4", title: "Konkursene øker mest blant underentreprenørene", page: "2" });

    s.addText("+18 %", { x: 0.62, y: 1.82, w: 3.4, h: 0.8, margin: 0, fontFace: FONT, fontSize: 46, bold: true, color: RED });
    s.addText("flere konkurser i bygg- og anleggsnæringen det siste året", {
      x: 0.62, y: 2.68, w: 6.25, h: 0.3, margin: 0, fontFace: FONT, fontSize: 11.5, color: MUTED,
    });

    s.addText(
      [
        ...para("Økningen er særlig sterk blant underentreprenører ", "– leddet med tynnest marginer og minst buffere."),
        ...para("Risikoen smitter i verdikjeden: ", "når underleverandører faller fra, øker leveranse- og motpartsrisikoen for hovedentreprenører og byggherrer."),
        ...para("Kredittvurdering og løpende oppfølging ", "av samarbeidspartnere blir stadig viktigere i prosjektgjennomføringen.", { last: true }),
      ],
      { x: 0.62, y: 3.55, w: 6.3, h: 3.2, margin: 0, valign: "top", fontSize: 14 }
    );

    // value-chain panel
    s.addShape(pres.ShapeType.roundRect, { x: 7.35, y: 1.78, w: 5.35, h: 5.0, rectRadius: 0.08, fill: { color: TINT } });
    s.addText("Hvor i verdikjeden treffer konkursene?", { x: 7.65, y: 2.02, w: 4.75, h: 0.3, margin: 0, fontFace: FONT, fontSize: 12.5, bold: true, color: INK });

    s.addShape(pres.ShapeType.roundRect, { x: 7.85, y: 2.5, w: 4.35, h: 0.62, rectRadius: 0.06, fill: { color: GREY_1 } });
    s.addText("Byggherre", { x: 7.85, y: 2.5, w: 4.35, h: 0.62, margin: 0, align: "center", valign: "middle", fontFace: FONT, fontSize: 12.5, bold: true, color: "4A4A50" });
    s.addShape(pres.ShapeType.triangle, { x: 9.84, y: 3.2, w: 0.36, h: 0.2, rotate: 180, fill: { color: ARROW } });

    s.addShape(pres.ShapeType.roundRect, { x: 7.85, y: 3.48, w: 4.35, h: 0.62, rectRadius: 0.06, fill: { color: GREY_2 } });
    s.addText("Hovedentreprenør", { x: 7.85, y: 3.48, w: 4.35, h: 0.62, margin: 0, align: "center", valign: "middle", fontFace: FONT, fontSize: 12.5, bold: true, color: "44444A" });
    s.addShape(pres.ShapeType.triangle, { x: 9.84, y: 4.18, w: 0.36, h: 0.2, rotate: 180, fill: { color: ARROW } });

    s.addShape(pres.ShapeType.roundRect, { x: 7.85, y: 4.46, w: 4.35, h: 0.82, rectRadius: 0.06, fill: { color: RED } });
    s.addText(
      [
        { text: "Underentreprenør", options: { bold: true, fontSize: 13, color: "FFFFFF", fontFace: FONT, breakLine: true } },
        { text: "størst økning i konkurser", options: { fontSize: 10, color: "FFE1E6", fontFace: FONT } },
      ],
      { x: 7.85, y: 4.46, w: 4.35, h: 0.82, margin: 0, align: "center", valign: "middle" }
    );

    s.addText("Presset nederst i kjeden forplanter seg oppover: konkurs hos én underleverandør kan velte fremdrift og økonomi i hele prosjektet.", {
      x: 7.65, y: 5.52, w: 4.75, h: 1.0, margin: 0, fontFace: FONT, fontSize: 10.5, italic: true, color: MUTED, valign: "top",
    });

    s.addNotes("Konkursene økte 18 prosent siste år, og økningen er størst blant underentreprenørene. Understrek smitteeffekten i verdikjeden – motpartsrisiko må inn i kundedialogen.");
  }

  /* ================= Slide 3 – AI i prosjektering ================= */
  {
    const s = pres.addSlide();
    chrome(s, { kicker: "BA-ANALYSEN 2026 · HOVEDFUNN 3 AV 4", title: "AI er i ferd med å bli standard i prosjekteringen", page: "3" });

    s.addText(
      [
        ...para("34 % av selskapene bruker nå AI i prosjekteringen ", "– omtrent hvert tredje selskap i næringen."),
        ...para("Gevinstene hentes tidlig i prosjektene: ", "raskere prosjektering, færre feil og bedre beslutningsgrunnlag."),
        ...para("Et kompetanseskille er i emning ", "mellom selskapene som investerer i AI, og de som avventer – det vil merkes i konkurransen om både oppdrag og folk.", { last: true }),
      ],
      { x: 0.62, y: 1.95, w: 6.45, h: 4.7, margin: 0, valign: "middle", fontSize: 14.5 }
    );

    s.addChart(pres.ChartType.doughnut, [
      { name: "AI i prosjektering", labels: ["Bruker AI", "Bruker ikke AI"], values: [34, 66] },
    ], {
      x: 7.6, y: 1.95, w: 4.6, h: 4.1,
      holeSize: 62,
      chartColors: [RED, "E6E6EA"],
      showLegend: false, showTitle: false, showValue: false, showLabel: false, showPercent: false,
      dataBorder: { pt: 2, color: "FFFFFF" },
    });
    s.addText("34 %", { x: 8.9, y: 3.58, w: 2.0, h: 0.55, margin: 0, align: "center", fontFace: FONT, fontSize: 32, bold: true, color: RED });
    s.addText("av selskapene", { x: 8.9, y: 4.16, w: 2.0, h: 0.3, margin: 0, align: "center", fontFace: FONT, fontSize: 10, color: MUTED });
    s.addText("Andel av selskapene i næringen som bruker AI i prosjekteringen", {
      x: 7.6, y: 6.18, w: 4.6, h: 0.55, margin: 0, align: "center", fontFace: FONT, fontSize: 11, color: MUTED, valign: "top",
    });

    s.addNotes("34 prosent av selskapene bruker AI i prosjekteringen. Poenget til partnerne: skillet mellom de som investerer og de som venter vokser – relevant både for kundedialogen og for våre egne leveranser.");
  }

  /* ================= Slide 4 – anbefaling ================= */
  {
    const s = pres.addSlide();
    chrome(s, { kicker: "BA-ANALYSEN 2026 · ANBEFALING", title: "Tettere likviditetsoppfølging hos utsatte kunder", page: "4" });

    s.addText("Marginpress og konkursvekst treffer likviditeten først. BA-analysen 2026 anbefaler én tydelig prioritet i kundeoppfølgingen:", {
      x: 0.62, y: 1.72, w: 12.0, h: 0.42, margin: 0, fontFace: FONT, fontSize: 13.5, color: BODY,
    });

    const cards = [
      {
        icon: "FiSearch", head: "1 · Identifiser de utsatte",
        body: "Bruk funnene i analysen til å fange opp kunder med svak inntjening, presset arbeidskapital og endret betalingsatferd.",
      },
      {
        icon: "FiActivity", head: "2 · Følg likviditeten tett",
        body: "Hyppigere likviditetsprognoser og tett oppfølging av ordrereserve, fakturering og utestående fordringer.",
      },
      {
        icon: "FiClock", head: "3 · Reager tidlig",
        body: "Ta dialogen om tiltak, finansiering og restrukturering før utfordringene blir akutte – tidlig innsats gir flest muligheter.",
      },
    ];
    cards.forEach((c, i) => {
      const cx = 0.62 + i * 4.135;
      s.addShape(pres.ShapeType.roundRect, { x: cx, y: 2.4, w: 3.85, h: 3.85, rectRadius: 0.08, fill: { color: TINT } });
      s.addShape(pres.ShapeType.ellipse, { x: cx + 0.32, y: 2.74, w: 0.62, h: 0.62, fill: { color: RED } });
      s.addImage({ data: icons[c.icon], x: cx + 0.46, y: 2.88, w: 0.34, h: 0.34 });
      s.addText(c.head, { x: cx + 0.32, y: 3.62, w: 3.21, h: 0.62, margin: 0, fontFace: FONT, fontSize: 14.5, bold: true, color: INK, valign: "top" });
      s.addText(c.body, { x: cx + 0.32, y: 4.28, w: 3.21, h: 1.8, margin: 0, fontFace: FONT, fontSize: 12.5, color: BODY, valign: "top", lineSpacingMultiple: 1.15 });
    });

    s.addNotes("Analysens hovedanbefaling: tettere likviditetsoppfølging hos utsatte kunder. Tre steg – identifisere de utsatte, følge likviditeten tett og reagere tidlig.");
  }

  /* ================= Slide 5 – betydning for BDO (mørk avslutning) ================= */
  {
    const s = pres.addSlide();
    chrome(s, { kicker: "BA-ANALYSEN 2026 · IMPLIKASJONER FOR BDO", title: "Hva funnene betyr for BDOs rådgivningsarbeid", page: "5", dark: true });

    const blocks = [
      {
        icon: "FiBarChart2", head: "Lønnsomhet og prosjektøkonomi",
        body: "Marginpresset gjør kostnadsstyring, prising og løpende prosjektoppfølging til kjerneleveranser i rådgivningen.",
      },
      {
        icon: "FiShield", head: "Risiko og restrukturering",
        body: "Flere konkurser øker behovet for tidlig varsling, motpartsvurderinger og restruktureringsbistand i hele verdikjeden.",
      },
      {
        icon: "FiDroplet", head: "Likviditet og finansiering",
        body: "Anbefalingen forplikter: tettere likviditetsoppfølging av utsatte kunder må inn i revisjons- og rådgivningsleveransene.",
      },
      {
        icon: "FiCpu", head: "Digitalisering og AI",
        body: "AI-skiftet i prosjekteringen åpner et nytt rådgivningsrom – fra gevinstrealisering og kompetanse til styring og kontroll.",
      },
    ];
    blocks.forEach((b, i) => {
      const cx = i % 2 === 0 ? 0.62 : 6.78;
      const cy = i < 2 ? 1.8 : 4.13;
      s.addShape(pres.ShapeType.roundRect, { x: cx, y: cy, w: 5.95, h: 2.13, rectRadius: 0.08, fill: { color: DARK_CARD } });
      s.addShape(pres.ShapeType.ellipse, { x: cx + 0.3, y: cy + 0.32, w: 0.52, h: 0.52, fill: { color: RED } });
      s.addImage({ data: icons[b.icon], x: cx + 0.42, y: cy + 0.44, w: 0.28, h: 0.28 });
      s.addText(b.head, { x: cx + 1.0, y: cy + 0.28, w: 4.65, h: 0.6, margin: 0, fontFace: FONT, fontSize: 14.5, bold: true, color: "FFFFFF", valign: "middle" });
      s.addText(b.body, { x: cx + 0.3, y: cy + 1.02, w: 5.35, h: 1.0, margin: 0, fontFace: FONT, fontSize: 11.5, color: DARK_BODY, valign: "top", lineSpacingMultiple: 1.12 });
    });

    s.addText(
      [
        { text: "BA-analysen 2026 ", options: { bold: true, color: RED_DARKSLIDE, fontFace: FONT } },
        { text: "gir oss en konkret inngang til styrerommet – bruk funnene aktivt i kundedialogen.", options: { bold: true, color: "FFFFFF", fontFace: FONT } },
      ],
      { x: 0.62, y: 6.52, w: 12.1, h: 0.45, margin: 0, fontSize: 13.5 }
    );

    s.addNotes("Avslutning: funnene omsatt til BDOs rådgivningsarbeid på tvers av tjenesteområdene. Oppfordring til partnerne: bruk analysen aktivt i kundedialogen.");
  }

  await pres.writeFile({ fileName: "ba2026_partner.pptx" });
  console.log("written ba2026_partner.pptx");
})().catch((e) => { console.error(e); process.exit(1); });
