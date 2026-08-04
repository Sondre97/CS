/* Bygger bergheim_csrd.pptx – BDO-førstemøte om bærekraftsrapportering og CSRD */
const path = require("path");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const Fi = require("react-icons/fi");
const pptxgen = require("pptxgenjs");

const OUT = path.join(__dirname, "bergheim_csrd.pptx");

/* ---------- farger og typografi ---------- */
const RED = "ED1A3B"; // BDO-rød
const DARK = "2B2B2B"; // mørk bakgrunn (forside/avslutning)
const TITLE = "222222";
const BODY = "3C3C3C";
const MUT = "6E6E6E";
const FAINT = "A9A9A9";
const CARD = "F6F6F6";
const HAIR = "E3E3E3";
const WHITE = "FFFFFF";
const ON_DARK = "C9C9C9";
const ON_DARK_MUT = "9C9C9C";
const F = "Arial";

const MX = 0.6; // sidemarg
const CW = 13.333 - 2 * MX;

/* ---------- ikoner (react-icons -> PNG data-URI) ---------- */
async function iconData(Comp) {
  let svg = ReactDOMServer.renderToStaticMarkup(
    React.createElement(Comp, { size: 256, color: "#FFFFFF" })
  );
  if (!svg.includes("xmlns=")) {
    svg = svg.replace("<svg ", '<svg xmlns="http://www.w3.org/2000/svg" ');
  }
  svg = svg.replace(/currentColor/g, "#FFFFFF");
  const buf = await sharp(Buffer.from(svg)).resize(256, 256).png().toBuffer();
  return "image/png;base64," + buf.toString("base64");
}

/* ---------- småhjelpere ---------- */
const shadow = () => ({ type: "outer", color: "000000", opacity: 0.16, blur: 7, offset: 2, angle: 90 });

function kicker(slide, txt, color) {
  slide.addText(txt, {
    x: MX, y: 0.44, w: CW, h: 0.3, margin: 0, fontFace: F, fontSize: 10.5,
    bold: true, color: color || RED, charSpacing: 2.5, align: "left", valign: "middle",
  });
}
function bigTitle(slide, txt, color) {
  slide.addText(txt, {
    x: MX, y: 0.72, w: CW, h: 0.62, margin: 0, fontFace: F, fontSize: 32,
    bold: true, color: color || TITLE, align: "left", valign: "middle",
  });
}
function footer(slide, n, onDark) {
  if (!onDark) {
    slide.addText("BDO  |  Bærekraftsrapportering og CSRD", {
      x: MX, y: 7.12, w: 6.5, h: 0.24, margin: 0, fontFace: F, fontSize: 8.5, color: FAINT,
      align: "left", valign: "middle",
    });
  }
  slide.addText(String(n), {
    x: 12.35, y: 7.12, w: 0.38, h: 0.24, margin: 0, fontFace: F, fontSize: 8.5,
    color: onDark ? "8A8A8A" : FAINT, align: "right", valign: "middle",
  });
}
function card(slide, x, y, w, h, fill) {
  slide.addShape("roundRect", {
    x, y, w, h, rectRadius: 0.09, fill: { color: fill || CARD }, shadow: shadow(),
  });
}
function iconCircle(slide, data, x, y, d) {
  d = d || 0.44;
  slide.addShape("ellipse", { x, y, w: d, h: d, fill: { color: RED } });
  const di = d * 0.56;
  slide.addImage({ data, x: x + (d - di) / 2, y: y + (d - di) / 2, w: di, h: di });
}
function numCircle(slide, num, x, y, d, fs) {
  slide.addText(String(num), {
    shape: "ellipse", x, y, w: d, h: d, fill: { color: RED }, margin: 0,
    fontFace: F, fontSize: fs, bold: true, color: WHITE, align: "center", valign: "middle",
  });
}

(async () => {
  const IC = {
    target: await iconData(Fi.FiTarget),
    users: await iconData(Fi.FiUsers),
    file: await iconData(Fi.FiFileText),
    credit: await iconData(Fi.FiCreditCard),
    check: await iconData(Fi.FiCheckCircle),
    compass: await iconData(Fi.FiCompass),
    layers: await iconData(Fi.FiLayers),
    tool: await iconData(Fi.FiTool),
    pin: await iconData(Fi.FiMapPin),
  };

  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE";
  pres.author = "BDO";
  pres.company = "BDO AS";
  pres.title = "Bærekraftsrapportering og CSRD – Bergheim Entreprenør AS";
  pres.subject = "Førstemøte om bærekraftsrapportering";

  /* ================= 1 – FORSIDE ================= */
  {
    const s = pres.addSlide();
    s.background = { color: DARK };

    // sirkelmotiv høyre side
    s.addShape("ellipse", { x: 9.3, y: -1.1, w: 5.0, h: 5.0, fill: { type: "none" }, line: { color: RED, width: 2.25 } });
    s.addShape("ellipse", { x: 10.85, y: 3.15, w: 2.5, h: 2.5, fill: { type: "none" }, line: { color: "4A4A4A", width: 1.5 } });
    s.addShape("ellipse", { x: 10.28, y: 2.6, w: 0.3, h: 0.3, fill: { color: RED } });

    s.addText("BDO", { x: MX, y: 0.45, w: 2.2, h: 0.7, margin: 0, fontFace: F, fontSize: 34, bold: true, color: WHITE, charSpacing: 1 });

    s.addText("FØRSTEMØTE  |  BÆREKRAFT OG RAPPORTERING", {
      x: MX, y: 2.25, w: 8.6, h: 0.3, margin: 0, fontFace: F, fontSize: 11, bold: true, color: "D8D8D8", charSpacing: 3,
    });
    s.addText("Bærekraftsrapportering og CSRD", {
      x: MX, y: 2.6, w: 8.8, h: 0.85, margin: 0, fontFace: F, fontSize: 40, bold: true, color: WHITE,
    });
    s.addText("Fra krav til konkurransekraft i bygg og anlegg", {
      x: MX, y: 3.55, w: 8.6, h: 0.4, margin: 0, fontFace: F, fontSize: 17, color: ON_DARK,
    });

    s.addText("Bergheim Entreprenør AS", {
      x: MX, y: 4.65, w: 6.5, h: 0.4, margin: 0, fontFace: F, fontSize: 15, bold: true, color: WHITE,
    });
    s.addText("3. august 2026  |  BDO Rådgivning – Bærekraft", {
      x: MX, y: 5.05, w: 6.5, h: 0.35, margin: 0, fontFace: F, fontSize: 12, color: ON_DARK_MUT,
    });

    s.addText("Revisjon  •  Rådgivning  •  Advokater  •  Regnskap og lønn", {
      x: MX, y: 6.95, w: 6.5, h: 0.3, margin: 0, fontFace: F, fontSize: 9.5, color: "8A8A8A",
    });
    s.addText("bdo.no", {
      x: 11.4, y: 6.95, w: 1.33, h: 0.3, margin: 0, fontFace: F, fontSize: 9.5, color: "8A8A8A", align: "right",
    });

    s.addNotes("Ønsk velkommen og sett rammen: 45 minutter, dialog underveis. Målet er en felles forståelse av kravbildet – ikke å selge et ferdig prosjekt.");
  }

  /* ================= 2 – AGENDA ================= */
  {
    const s = pres.addSlide();
    s.background = { color: WHITE };
    kicker(s, "FØRSTEMØTE  |  3. AUGUST 2026");
    bigTitle(s, "Agenda");

    const items = [
      "Kravbildet – CSRD, ESRS og terskelverdier",
      "Hva betyr det for Bergheim Entreprenør?",
      "Vår tilnærming – tre faser",
      "Hvorfor BDO?",
      "Neste steg",
    ];
    items.forEach((t, i) => {
      const y = 1.85 + i * 0.88;
      numCircle(s, i + 1, 0.62, y, 0.42, 13);
      s.addText(t, {
        x: 1.28, y: y - 0.02, w: 6.3, h: 0.46, margin: 0, fontFace: F, fontSize: 14.5,
        bold: true, color: "333333", valign: "middle",
      });
    });

    // mørkt kort: målet med møtet
    card(s, 8.05, 1.8, 4.68, 4.1, DARK);
    iconCircle(s, IC.target, 8.37, 2.14, 0.46);
    s.addText("Målet med møtet", {
      x: 9.0, y: 2.18, w: 3.5, h: 0.4, margin: 0, fontFace: F, fontSize: 15, bold: true, color: WHITE, valign: "middle",
    });
    s.addText(
      [
        { text: "Felles bilde av kravene – og hva de faktisk betyr for dere", options: { bullet: true, breakLine: true } },
        { text: "Vise hvordan vi kan hjelpe – konkret og skalerbart", options: { bullet: true, breakLine: true } },
        { text: "Enighet om neste steg før høstens anbudsrunder", options: { bullet: true } },
      ],
      {
        x: 8.37, y: 2.95, w: 4.05, h: 2.6, margin: 0, fontFace: F, fontSize: 11.5,
        color: ON_DARK, valign: "top", paraSpaceAfter: 10,
      }
    );

    footer(s, 2);
    s.addNotes("Avstem agendaen: Er dette de riktige temaene? Hva er viktigst for dere i dag? Noter forventninger.");
  }

  /* ================= 3 – KRAVBILDET ================= */
  {
    const s = pres.addSlide();
    s.background = { color: WHITE };
    kicker(s, "KRAVBILDET  |  CSRD OG ESRS");
    bigTitle(s, "Kravene treffer de store først – tersklene avgjør");

    const pts = [
      "CSRD er EUs direktiv for bærekraftsrapportering – innført i norsk rett gjennom regnskapsloven i 2024.",
      "Rapportering etter ESRS-standardene: miljø, sosiale forhold og styring – basert på dobbel vesentlighet.",
      "Rapporten inngår i årsberetningen og skal attesteres av revisor.",
      "Omnibus-pakken i EU: innfasing utsatt to år og terskler foreslått hevet – kravbildet er i bevegelse.",
    ];
    pts.forEach((t, i) => {
      const y = 1.62 + i * 0.78;
      s.addShape("ellipse", { x: 0.63, y: y + 0.08, w: 0.11, h: 0.11, fill: { color: RED } });
      s.addText(t, {
        x: 0.92, y, w: 6.0, h: 0.66, margin: 0, fontFace: F, fontSize: 12.5, color: BODY, valign: "top",
      });
    });

    // terskelverdi-kort
    const cx = 7.1, cy = 1.58, cw = 5.63, ch = 3.0;
    card(s, cx, cy, cw, ch);
    s.addText("STORE FORETAK – MINST TO AV TRE OVERSKRIDES", {
      x: cx + 0.28, y: cy + 0.2, w: cw - 0.56, h: 0.3, margin: 0, fontFace: F, fontSize: 10.5,
      bold: true, color: MUT, charSpacing: 1.5, valign: "middle",
    });
    const rows = [
      ["580 MNOK", "salgsinntekter"],
      ["290 MNOK", "balansesum"],
      ["250", "årsverk i gjennomsnitt"],
    ];
    rows.forEach((r, i) => {
      const ry = cy + 0.62 + i * 0.76;
      s.addText(r[0], { x: cx + 0.28, y: ry, w: 2.1, h: 0.6, margin: 0, fontFace: F, fontSize: 23, bold: true, color: RED, valign: "middle" });
      s.addText(r[1], { x: cx + 2.5, y: ry, w: cw - 2.8, h: 0.6, margin: 0, fontFace: F, fontSize: 11, color: MUT, valign: "middle" });
      if (i < 2) s.addShape("line", { x: cx + 0.28, y: ry + 0.68, w: cw - 0.56, h: 0, line: { color: HAIR, width: 0.75 } });
    });

    // innfasing – tidslinje
    s.addText("INNFASING ETTER TOÅRSUTSETTELSEN I EU (2025) – REGNSKAPSÅR", {
      x: MX, y: 4.92, w: CW, h: 0.3, margin: 0, fontFace: F, fontSize: 10.5, bold: true, color: MUT, charSpacing: 1.5,
    });
    s.addShape("line", { x: 0.7, y: 5.88, w: 11.85, h: 0, line: { color: "D9D9D9", width: 1.5 } });
    const tl = [
      ["2024", "Noterte foretak, banker og forsikring med over 500 ansatte – rapporterer allerede", 1.05],
      ["2027", "Øvrige store foretak – første rapport publiseres i 2028", 5.05],
      ["2028", "Noterte SMB – foreslått tatt ut av virkeområdet i omnibus-pakken", 9.05],
    ];
    tl.forEach(([yr, d, x]) => {
      s.addText(yr, {
        shape: "ellipse", x, y: 5.56, w: 0.64, h: 0.64, fill: { color: RED }, margin: 0,
        fontFace: F, fontSize: 11.5, bold: true, color: WHITE, align: "center", valign: "middle",
      });
      s.addText(d, {
        x, y: 6.34, w: 3.55, h: 0.68, margin: 0, fontFace: F, fontSize: 10, color: MUT, valign: "top",
      });
    });

    footer(s, 3);
    s.addNotes("Hold det overordnet – ikke gå inn i enkeltstandarder. Hovedbudskap: regelverket er i bevegelse (omnibus), men retningen står fast, og verdikjedekravene forsvinner ikke.");
  }

  /* ================= 4 – HVA BETYR DET FOR BERGHEIM ================= */
  {
    const s = pres.addSlide();
    s.background = { color: WHITE };
    kicker(s, "HVA BETYR DETTE FOR BERGHEIM?");
    bigTitle(s, "Under terskelen i dag – men kravene når dere likevel");

    // statuskort + intro
    card(s, MX, 1.5, 3.3, 1.12, DARK);
    s.addText("450 MNOK", { x: MX + 0.25, y: 1.64, w: 2.8, h: 0.42, margin: 0, fontFace: F, fontSize: 26, bold: true, color: WHITE });
    s.addText("omsetning i dag (ca.) – terskel: 580 MNOK", {
      x: MX + 0.25, y: 2.1, w: 2.85, h: 0.4, margin: 0, fontFace: F, fontSize: 10, color: ON_DARK, valign: "top",
    });
    s.addText(
      "To av tre terskler må overskrides – Bergheim er derfor trolig ikke direkte rapporteringspliktig de nærmeste årene. Presset kommer likevel, fra flere kanter samtidig:",
      { x: 4.2, y: 1.5, w: 8.53, h: 1.12, margin: 0, fontFace: F, fontSize: 13, color: BODY, valign: "middle" }
    );

    const cards = [
      [IC.users, "Byggherrer og hovedentreprenører", "CSRD-pliktige kunder trenger tall fra leverandørkjeden – klima, HMS og seriøsitet. Frivillig SMB-standard (VSME) er blitt malen for bestillingene."],
      [IC.file, "Offentlige anbud", "Klima og miljø vektes som hovedregel 30 %. Utslippsfrie byggeplasser og klimagassregnskap (NS 3720) etterspørres stadig oftere."],
      [IC.credit, "Bank og forsikring", "ESG-status påvirker finansiering, garantier og pris på risiko. God dokumentasjon åpner for grønne lån og bedre betingelser."],
      [IC.check, "Krav som allerede gjelder", "Åpenhetsloven omfatter dere i dag: aktsomhetsvurderinger og årlig redegjørelse. TEK17 krever 70 % kildesortering på byggeplass."],
    ];
    cards.forEach(([ic, t, d], i) => {
      const x = i % 2 === 0 ? MX : 6.84;
      const y = i < 2 ? 2.92 : 4.86;
      card(s, x, y, 5.89, 1.78);
      iconCircle(s, ic, x + 0.24, y + 0.26, 0.44);
      s.addText(t, { x: x + 0.86, y: y + 0.22, w: 4.85, h: 0.32, margin: 0, fontFace: F, fontSize: 13, bold: true, color: TITLE, valign: "middle" });
      s.addText(d, { x: x + 0.86, y: y + 0.58, w: 4.8, h: 1.08, margin: 0, fontFace: F, fontSize: 11, color: MUT, valign: "top" });
    });

    s.addText("Vekst, oppkjøp eller endrede terskler kan dessuten gjøre dere direkte rapporteringspliktige på kort varsel.", {
      x: MX, y: 6.78, w: CW, h: 0.3, margin: 0, fontFace: F, fontSize: 10.5, italic: true, color: MUT, valign: "middle",
    });

    footer(s, 4);
    s.addNotes("Møtets kjernebudskap: plikten treffer trolig ikke Bergheim direkte ennå – presset kommer via kunder, anbud, bank og forsikring. Spør: Hvilke ESG-krav har dere allerede møtt i anbud eller fra byggherrer?");
  }

  /* ================= 5 – TRE FASER ================= */
  {
    const s = pres.addSlide();
    s.background = { color: WHITE };
    kicker(s, "VÅR TILNÆRMING");
    bigTitle(s, "Tre faser – i deres tempo");

    const phases = [
      {
        n: 1, t: "Innsikt og vesentlighet", uke: "UKE 1–6",
        pts: [
          "Ambisjonsnivå og kartlegging av krav fra kunder, anbud og bank",
          "Dobbel vesentlighetsanalyse – tilpasset deres størrelse",
          "Prioriterte bærekraftstemaer",
        ],
        lev: "Vesentlighetsanalyse og målbilde",
      },
      {
        n: 2, t: "Gap-analyse og datagrunnlag", uke: "UKE 6–12",
        pts: [
          "Status på data: klimaregnskap (scope 1–3), HMS, avfall, leverandører",
          "Gap mot VSME/ESRS og kundenes bestillinger",
          "Veikart med tiltak, ansvar og KPI-er",
        ],
        lev: "Gap-rapport og prioritert veikart",
      },
      {
        n: 3, t: "Rapportering og forankring", uke: "FRA UKE 12",
        pts: [
          "Klimaregnskap og nøkkeltall settes i system",
          "Første bærekraftsrapport – VSME eller forenklet ESRS",
          "Policyer, opplæring og forankring i drift",
        ],
        lev: "Publiseringsklar rapport – forberedt for attestasjon",
      },
    ];
    const xs = [0.6, 4.81, 9.02];
    phases.forEach((p, i) => {
      const x = xs[i], y = 1.55, w = 3.7, h = 4.55;
      card(s, x, y, w, h);
      numCircle(s, p.n, x + 0.26, y + 0.28, 0.5, 15);
      s.addText(p.t, { x: x + 0.9, y: y + 0.24, w: w - 1.1, h: 0.58, margin: 0, fontFace: F, fontSize: 14, bold: true, color: TITLE, valign: "middle" });
      s.addText(p.uke, { x: x + 0.9, y: y + 0.86, w: w - 1.1, h: 0.26, margin: 0, fontFace: F, fontSize: 9.5, bold: true, color: RED, charSpacing: 1.5, valign: "middle" });
      s.addText(
        p.pts.map((t, j) => ({ text: t, options: { bullet: true, breakLine: j < p.pts.length - 1 } })),
        { x: x + 0.26, y: y + 1.3, w: w - 0.52, h: 2.15, margin: 0, fontFace: F, fontSize: 11, color: BODY, valign: "top", paraSpaceAfter: 8 }
      );
      s.addText("LEVERANSE", { x: x + 0.26, y: y + 3.55, w: w - 0.52, h: 0.24, margin: 0, fontFace: F, fontSize: 8.5, bold: true, color: MUT, charSpacing: 1.5 });
      s.addText(p.lev, { x: x + 0.26, y: y + 3.8, w: w - 0.52, h: 0.62, margin: 0, fontFace: F, fontSize: 11, bold: true, color: TITLE, valign: "top" });
    });
    // piler mellom fasene
    s.addShape("chevron", { x: 4.38, y: 3.62, w: 0.34, h: 0.4, fill: { color: RED } });
    s.addShape("chevron", { x: 8.59, y: 3.62, w: 0.34, h: 0.4, fill: { color: RED } });

    s.addText("Skalerbart opplegg: omfang, standardvalg og tempo tilpasses en mellomstor entreprenør – ikke et børsnotert konsern.", {
      x: MX, y: 6.4, w: CW, h: 0.32, margin: 0, fontFace: F, fontSize: 11.5, color: MUT, valign: "middle",
    });

    footer(s, 5);
    s.addNotes("Understrek at opplegget er skalerbart – vi starter med innsikt, ikke systemkjøp. Fase 1 kan starte innen to uker etter avtale.");
  }

  /* ================= 6 – HVORFOR BDO ================= */
  {
    const s = pres.addSlide();
    s.background = { color: WHITE };
    kicker(s, "OM BDO");
    bigTitle(s, "Hvorfor BDO?");

    s.addText(
      "BDO er blant landets største kompetansemiljøer innen revisjon og rådgivning – med et dedikert bærekraftsteam og lang fartstid i bygg og anlegg.",
      { x: MX, y: 1.6, w: 3.5, h: 1.45, margin: 0, fontFace: F, fontSize: 12.5, color: BODY, valign: "top" }
    );
    s.addText("2 000+", { x: MX, y: 3.2, w: 3.3, h: 0.5, margin: 0, fontFace: F, fontSize: 30, bold: true, color: RED });
    s.addText("medarbeidere over hele landet", { x: MX, y: 3.72, w: 3.4, h: 0.3, margin: 0, fontFace: F, fontSize: 10.5, color: MUT });
    s.addText("BA-analysen", { x: MX, y: 4.3, w: 3.3, h: 0.4, margin: 0, fontFace: F, fontSize: 19, bold: true, color: TITLE });
    s.addText("vår årlige analyse av bygg- og anleggsnæringen", { x: MX, y: 4.72, w: 3.4, h: 0.5, margin: 0, fontFace: F, fontSize: 10.5, color: MUT, valign: "top" });

    const cards = [
      [IC.compass, "Bransjeinnsikt", "Vi analyserer byggenæringen årlig og kjenner marginene, kontraktene og anbudshverdagen."],
      [IC.layers, "Tverrfaglig lag", "Bærekraftsrådgivere, revisorer og advokater – ett team fra strategi til ferdig attestert rapport."],
      [IC.tool, "Metode for mellomstore", "Verktøy og maler skalert for virksomheter som deres – ikke for børsnoterte konsern."],
      [IC.pin, "Nær dere", "Kontorer over hele landet – rådgiverne sitter i regionen og er tilgjengelige gjennom hele året."],
    ];
    cards.forEach(([ic, t, d], i) => {
      const x = i % 2 === 0 ? 4.5 : 8.78;
      const y = i < 2 ? 1.6 : 4.2;
      card(s, x, y, 3.95, 2.35);
      iconCircle(s, ic, x + 0.26, y + 0.28, 0.44);
      s.addText(t, { x: x + 0.85, y: y + 0.3, w: 3.0, h: 0.4, margin: 0, fontFace: F, fontSize: 12.5, bold: true, color: TITLE, valign: "middle" });
      s.addText(d, { x: x + 0.26, y: y + 0.95, w: 3.42, h: 1.25, margin: 0, fontFace: F, fontSize: 11, color: MUT, valign: "top" });
    });

    footer(s, 6);
    s.addNotes("Kort her – ikke selg for hardt. Tilby å sende BA-analysen og et eksempel på VSME-rapport i etterkant.");
  }

  /* ================= 7 – NESTE STEG ================= */
  {
    const s = pres.addSlide();
    s.background = { color: DARK };

    s.addShape("ellipse", { x: 11.3, y: -1.5, w: 4.0, h: 4.0, fill: { type: "none" }, line: { color: "3E3E3E", width: 1.5 } });
    s.addShape("ellipse", { x: 12.35, y: 2.05, w: 0.26, h: 0.26, fill: { color: RED } });

    kicker(s, "VEIEN VIDERE", ON_DARK_MUT);
    bigTitle(s, "Neste steg", WHITE);

    const steps = [
      ["Arbeidsmøte (2 timer)", "Vi går gjennom kundekrav, anbud og ambisjonsnivå sammen med dere – og avgrenser hva som faktisk haster.", "UKE 1–2"],
      ["Kostnadsfri modenhetsvurdering", "Kort statusgjennomgang med konkrete anbefalinger for de neste tolv månedene.", "UKE 3–4"],
      ["Forslag til fase 1", "Fast pris, team og tidsplan – et beslutningsgrunnlag dere kan ta til styret.", "UKE 5"],
    ];
    steps.forEach(([t, d, uke], i) => {
      const y = 1.9 + i * 1.18;
      numCircle(s, i + 1, 0.62, y + 0.06, 0.5, 14);
      s.addText(t, { x: 1.4, y, w: 9.0, h: 0.36, margin: 0, fontFace: F, fontSize: 15, bold: true, color: WHITE, valign: "middle" });
      s.addText(d, { x: 1.4, y: y + 0.4, w: 8.9, h: 0.55, margin: 0, fontFace: F, fontSize: 11.5, color: ON_DARK, valign: "top" });
      s.addShape("roundRect", { x: 10.85, y: y + 0.08, w: 1.85, h: 0.44, rectRadius: 0.22, fill: { color: DARK }, line: { color: "6E6E6E", width: 1 } });
      s.addText(uke, { x: 10.85, y: y + 0.08, w: 1.85, h: 0.44, margin: 0, fontFace: F, fontSize: 9.5, bold: true, color: ON_DARK, charSpacing: 1.5, align: "center", valign: "middle" });
    });

    s.addText("Kan vi sette datoen for arbeidsmøtet i dag?", {
      x: MX, y: 5.85, w: 9.0, h: 0.45, margin: 0, fontFace: F, fontSize: 16, bold: true, color: WHITE, valign: "middle",
    });
    s.addText("BDO Bærekraftstjenester  |  bdo.no", {
      x: MX, y: 6.4, w: 9.0, h: 0.35, margin: 0, fontFace: F, fontSize: 11.5, color: ON_DARK_MUT, valign: "middle",
    });

    footer(s, 7, true);
    s.addNotes("Vær konkret: foreslå dato for arbeidsmøtet før møtet heves. Avklar hvem som bør delta fra Bergheim (økonomi, KS/HMS, kalkyle).");
  }

  await pres.writeFile({ fileName: OUT });
  console.log("Wrote", OUT);
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
