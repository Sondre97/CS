/* Kvartalsstatus Q2 2026 – Rådgivning. BDO-branded deck (pptx-brand path B: pptxgenjs, alt eksplisitt). */
const fs = require('fs');
const path = require('path');
const React = require('react');
const ReactDOMServer = require('react-dom/server');
const sharp = require('sharp');
const Fi = require('react-icons/fi');
const pptxgen = require('pptxgenjs');

const OUT = __dirname;
const FONT = 'Trebuchet MS';
const NB = ' ';

// BDO-paletten (fasit fra bdo-design)
const C = {
  red: 'E81A3B', text: '333333', slate: '5B6E7F', burgundy: '98002E',
  orange: 'D67900', green: '009966', blue: '008FD2', link: '0062B8',
  light: 'F2F2F2', white: 'FFFFFF', grayTxt: '767676', grayBar: 'D9D9D9',
};
// Tint = lineær blanding mot hvit (godkjent av check_brand som tint av palettfarge)
function tint(hex, t) {
  const c = [0, 2, 4].map((i) => parseInt(hex.slice(i, i + 2), 16));
  return c.map((v) => Math.round(v * t + 255 * (1 - t)).toString(16).padStart(2, '0')).join('').toUpperCase();
}
const redCard = tint(C.red, 0.08);   // lys rød flate bak nøkkeltall
const redBar = tint(C.red, 0.30);    // mål-søyle (ikke oppnådd ennå)
const greenChip = tint(C.green, 0.12); // lys grønn chip-bakgrunn
const titleTint = tint(C.red, 0.30); // dempet tekst på rød bakgrunn

async function makeIcons() {
  const want = {
    trending: Fi.FiTrendingUp, clock: Fi.FiClock, percent: Fi.FiPercent,
    userplus: Fi.FiUserPlus, activity: Fi.FiActivity, users: Fi.FiUsers,
    filetext: Fi.FiFileText, target: Fi.FiTarget,
  };
  const dir = path.join(OUT, 'icons');
  fs.mkdirSync(dir, { recursive: true });
  const uris = {};
  for (const [name, Comp] of Object.entries(want)) {
    let svg = ReactDOMServer.renderToStaticMarkup(React.createElement(Comp, { size: 256, strokeWidth: 2 }));
    svg = svg.replace(/currentColor/g, '#FFFFFF');
    const buf = await sharp(Buffer.from(svg)).png().toBuffer();
    fs.writeFileSync(path.join(dir, name + '.png'), buf);
    uris[name] = 'image/png;base64,' + buf.toString('base64');
  }
  return uris;
}

(async () => {
  const IC = await makeIcons();
  const p = new pptxgen();
  p.layout = 'LAYOUT_WIDE'; // 13.33 x 7.5 => 16:9
  p.author = 'BDO Rådgivning';
  p.company = 'BDO';
  p.title = 'Kvartalsstatus Q2 2026 – Rådgivning';
  p.subject = 'Internt ledermøte';

  const footer = {
    text: {
      text: 'BDO · Rådgivning · Kvartalsstatus Q2 2026 · Internt',
      options: { x: 0.6, y: 7.08, w: 7.5, h: 0.3, fontFace: FONT, fontSize: 9, color: C.grayTxt, align: 'left', margin: 0 },
    },
  };
  const pageNum = { x: 12.55, y: 7.08, w: 0.55, h: 0.3, fontFace: FONT, fontSize: 9, color: C.grayTxt, align: 'right' };

  // Navngitte layouts i BDO-malens ånd (aldri Blank)
  p.defineSlideMaster({ title: 'Tittel A – Rød', background: { color: C.red } });
  p.defineSlideMaster({ title: 'Heading og nøkkeltall', background: { color: C.white }, objects: [footer], slideNumber: pageNum });
  p.defineSlideMaster({ title: 'Heading, graf og tekstfelt A', background: { color: C.white }, objects: [footer], slideNumber: pageNum });
  p.defineSlideMaster({ title: 'Heading, graf og tekstfelt B', background: { color: C.white }, objects: [footer], slideNumber: pageNum });
  p.defineSlideMaster({ title: 'Heading og tre felt', background: { color: C.light }, objects: [footer], slideNumber: pageNum });

  const kicker = (slide, txt) =>
    slide.addText(txt, { x: 0.6, y: 0.45, w: 11.5, h: 0.34, fontFace: FONT, fontSize: 11, bold: true, color: C.slate, charSpacing: 2, margin: 0 });
  const heading = (slide, txt) =>
    slide.addText(txt, { x: 0.6, y: 0.82, w: 12.13, h: 1.05, fontFace: FONT, fontSize: 27, bold: true, color: C.text, margin: 0, valign: 'top' });

  /* ---------- Slide 1: Tittel (rød) ---------- */
  {
    const s = p.addSlide({ masterName: 'Tittel A – Rød' });
    s.addShape(p.ShapeType.ellipse, { x: 9.5, y: 2.8, w: 5.7, h: 5.7, fill: { color: C.burgundy } });
    s.addShape(p.ShapeType.ellipse, { x: 11.5, y: 0.7, w: 3.3, h: 3.3, fill: { color: C.white, transparency: 88 } });
    s.addText('BDO', { x: 0.6, y: 0.5, w: 1.6, h: 0.6, fontFace: FONT, fontSize: 26, bold: true, color: C.white, margin: 0 });
    s.addText('INTERNT LEDERMØTE · AUGUST 2026', { x: 0.62, y: 2.55, w: 9, h: 0.4, fontFace: FONT, fontSize: 13, bold: true, color: C.white, charSpacing: 3, margin: 0 });
    s.addText('Kvartalsstatus Q2 2026', { x: 0.6, y: 3.0, w: 10.5, h: 1.05, fontFace: FONT, fontSize: 48, bold: true, color: C.white, margin: 0 });
    s.addText('Forretningsområdet Rådgivning', { x: 0.62, y: 4.15, w: 9, h: 0.6, fontFace: FONT, fontSize: 22, color: C.white, margin: 0 });
    s.addText('Internt arbeidsdokument – ikke for distribusjon', { x: 0.62, y: 6.9, w: 7, h: 0.35, fontFace: FONT, fontSize: 10, color: titleTint, margin: 0 });
    s.addNotes('Kvartalsstatus for forretningsområdet Rådgivning til internt ledermøte. Hovedbudskap: Q2 endte over budsjett, og driften bedret seg på alle nøkkeltall.');
  }

  /* ---------- Slide 2: Nøkkeltall ---------- */
  {
    const s = p.addSlide({ masterName: 'Heading og nøkkeltall' });
    kicker(s, 'NØKKELTALL · Q2 2026');
    heading(s, 'Q2 endte over budsjett – og driften bedret seg på alle nøkkeltall');

    // Hero-kort: omsetning
    s.addShape(p.ShapeType.roundRect, { x: 0.6, y: 2.0, w: 4.35, h: 4.8, fill: { color: redCard }, rectRadius: 0.12 });
    s.addShape(p.ShapeType.ellipse, { x: 0.95, y: 2.35, w: 0.62, h: 0.62, fill: { color: C.red } });
    s.addImage({ data: IC.trending, x: 1.09, y: 2.49, w: 0.34, h: 0.34 });
    s.addText('OMSETNING Q2', { x: 0.95, y: 3.25, w: 3.6, h: 0.32, fontFace: FONT, fontSize: 11, bold: true, color: C.slate, charSpacing: 2, margin: 0 });
    s.addText([
      { text: '182', options: { fontSize: 64, bold: true, color: C.red } },
      { text: ' MNOK', options: { fontSize: 20, bold: true, color: C.slate } },
    ], { x: 0.92, y: 3.6, w: 3.9, h: 1.1, fontFace: FONT, margin: 0, valign: 'bottom' });
    s.addShape(p.ShapeType.roundRect, { x: 0.95, y: 5.05, w: 3.62, h: 0.52, fill: { color: greenChip }, rectRadius: 0.26 });
    s.addText(`+18 MNOK mot Q1 (+11${NB}%)`, { x: 0.95, y: 5.05, w: 3.62, h: 0.52, fontFace: FONT, fontSize: 12, bold: true, color: C.green, align: 'center', margin: 0 });
    s.addShape(p.ShapeType.roundRect, { x: 0.95, y: 5.68, w: 3.62, h: 0.52, fill: { color: C.white }, rectRadius: 0.26 });
    s.addText('+7 MNOK mot budsjett (175)', { x: 0.95, y: 5.68, w: 3.62, h: 0.52, fontFace: FONT, fontSize: 12, bold: true, color: C.burgundy, align: 'center', margin: 0 });

    // Fire mindre kort
    const cards = [
      { x: 5.25, y: 2.0, icon: 'clock', label: 'SNITT TIMEPRIS', num: `1${NB}480`, suffix: ' kr', delta: '+25 kr mot Q1' },
      { x: 9.13, y: 2.0, icon: 'percent', label: 'UTFAKTURERINGSGRAD', num: '78', suffix: ` %`, delta: 'opp fra 74 % i Q1' },
      { x: 5.25, y: 4.52, icon: 'userplus', label: 'NYANSETTELSER', num: '12', suffix: '', delta: 'mot 8 i Q1' },
      { x: 9.13, y: 4.52, icon: 'activity', label: 'SYKEFRAVÆR', num: '3,1', suffix: ` %`, delta: 'ned fra 3,4 % i Q1' },
    ];
    for (const cd of cards) {
      s.addShape(p.ShapeType.roundRect, { x: cd.x, y: cd.y, w: 3.6, h: 2.28, fill: { color: C.light }, rectRadius: 0.12 });
      s.addShape(p.ShapeType.ellipse, { x: cd.x + 0.28, y: cd.y + 0.28, w: 0.5, h: 0.5, fill: { color: C.slate } });
      s.addImage({ data: IC[cd.icon], x: cd.x + 0.39, y: cd.y + 0.39, w: 0.28, h: 0.28 });
      s.addText(cd.label, { x: cd.x + 0.92, y: cd.y + 0.38, w: 2.6, h: 0.32, fontFace: FONT, fontSize: 10, bold: true, color: C.slate, charSpacing: 1.5, margin: 0 });
      s.addText([
        { text: cd.num, options: { fontSize: 30, bold: true, color: C.text } },
        { text: cd.suffix, options: { fontSize: 15, bold: true, color: C.slate } },
      ], { x: cd.x + 0.28, y: cd.y + 1.0, w: 3.05, h: 0.66, fontFace: FONT, margin: 0, valign: 'bottom' });
      s.addText(cd.delta, { x: cd.x + 0.28, y: cd.y + 1.74, w: 3.05, h: 0.4, fontFace: FONT, fontSize: 11.5, bold: true, color: C.green, margin: 0 });
    }
    s.addNotes('Alle fem nøkkeltall bedret seg fra Q1. Omsetningen på 182 MNOK ligger 7 MNOK over budsjettet på 175 MNOK.');
  }

  /* ---------- Slide 3: Omsetning (graf) ---------- */
  {
    const s = p.addSlide({ masterName: 'Heading, graf og tekstfelt A' });
    kicker(s, 'OMSETNING');
    heading(s, 'Omsetningen økte 11 prosent fra Q1 og endte 7 MNOK over budsjettet');
    s.addChart(p.ChartType.bar, [
      { name: 'Omsetning (MNOK)', labels: ['Q1 faktisk', 'Budsjett Q2', 'Q2 faktisk'], values: [164, 175, 182] },
    ], {
      x: 0.6, y: 2.05, w: 7.7, h: 4.7, barDir: 'col', barGapWidthPct: 60,
      chartColors: [C.slate, C.grayBar, C.red],
      showLegend: false,
      showTitle: true, title: 'Omsetning (MNOK)', titleFontFace: FONT, titleFontSize: 12, titleColor: C.slate,
      showValue: true, dataLabelPosition: 'outEnd', dataLabelFormatCode: '0',
      dataLabelFontFace: FONT, dataLabelFontSize: 13, dataLabelFontBold: true, dataLabelColor: C.text,
      catAxisLabelFontFace: FONT, catAxisLabelFontSize: 12, catAxisLabelColor: C.text,
      valAxisHidden: true, valAxisMinVal: 0, valAxisMaxVal: 200,
      valAxisLabelFontFace: FONT, valAxisLabelFontSize: 10, valAxisLabelColor: C.grayTxt,
      valGridLine: { style: 'none' }, catGridLine: { style: 'none' },
    });
    // Tekstfelt høyre
    s.addShape(p.ShapeType.roundRect, { x: 8.6, y: 2.05, w: 4.13, h: 4.7, fill: { color: C.light }, rectRadius: 0.12 });
    s.addText('KORT FORTALT', { x: 8.92, y: 2.35, w: 3.5, h: 0.32, fontFace: FONT, fontSize: 11, bold: true, color: C.slate, charSpacing: 2, margin: 0 });
    const rows = [
      { y: 3.0, t: '182 MNOK i Q2 – opp fra 164 i Q1' },
      { y: 4.1, t: 'Budsjettet på 175 MNOK ble slått med 7 MNOK' },
      { y: 5.2, t: 'Veksten er driftsdrevet: høyere utfakturering og timepris (neste side)' },
    ];
    for (const r of rows) {
      s.addShape(p.ShapeType.ellipse, { x: 8.92, y: r.y + 0.06, w: 0.14, h: 0.14, fill: { color: C.red } });
      s.addText(r.t, { x: 9.18, y: r.y, w: 3.33, h: 0.95, fontFace: FONT, fontSize: 12.5, color: C.text, margin: 0, valign: 'top', lineSpacingMultiple: 1.12 });
    }
    s.addNotes('Omsetningen økte fra 164 til 182 MNOK (+11 prosent). Budsjettet for Q2 var 175 MNOK – vi endte 7 MNOK over (+4 prosent).');
  }

  /* ---------- Slide 4: Drivere (graf + kort) ---------- */
  {
    const s = p.addSlide({ masterName: 'Heading, graf og tekstfelt B' });
    kicker(s, 'DRIFT OG KAPASITET');
    heading(s, 'Utfaktureringsgraden steg til 78 prosent – målet for Q3 er over 80');
    s.addChart(p.ChartType.bar, [
      { name: 'Utfaktureringsgrad (%)', labels: ['Q1', 'Q2', 'Mål Q3'], values: [74, 78, 80] },
    ], {
      x: 0.6, y: 2.05, w: 6.45, h: 4.7, barDir: 'col', barGapWidthPct: 70,
      chartColors: [C.slate, C.red, redBar],
      showLegend: false,
      showTitle: true, title: 'Utfaktureringsgrad (%)', titleFontFace: FONT, titleFontSize: 12, titleColor: C.slate,
      showValue: true, dataLabelPosition: 'outEnd', dataLabelFormatCode: `0" %"`,
      dataLabelFontFace: FONT, dataLabelFontSize: 13, dataLabelFontBold: true, dataLabelColor: C.text,
      catAxisLabelFontFace: FONT, catAxisLabelFontSize: 12, catAxisLabelColor: C.text,
      valAxisHidden: true, valAxisMinVal: 0, valAxisMaxVal: 90,
      valAxisLabelFontFace: FONT, valAxisLabelFontSize: 10, valAxisLabelColor: C.grayTxt,
      valGridLine: { style: 'none' }, catGridLine: { style: 'none' },
    });
    const rows = [
      { y: 2.05, icon: 'clock', label: 'SNITT TIMEPRIS', num: `1${NB}480 kr`, delta: `  opp fra 1${NB}455 kr i Q1`, dc: C.green },
      { y: 3.67, icon: 'userplus', label: 'NYANSETTELSER I Q2', num: '12', delta: '  mot 8 i Q1 (+50 %)', dc: C.green },
      { y: 5.29, icon: 'activity', label: 'SYKEFRAVÆR', num: `3,1${NB}%`, delta: '  ned fra 3,4 % i Q1', dc: C.green },
    ];
    for (const r of rows) {
      s.addShape(p.ShapeType.roundRect, { x: 7.4, y: r.y, w: 5.33, h: 1.46, fill: { color: C.light }, rectRadius: 0.12 });
      s.addShape(p.ShapeType.ellipse, { x: 7.68, y: r.y + 0.48, w: 0.5, h: 0.5, fill: { color: C.slate } });
      s.addImage({ data: IC[r.icon], x: 7.79, y: r.y + 0.59, w: 0.28, h: 0.28 });
      s.addText(r.label, { x: 8.35, y: r.y + 0.26, w: 4.2, h: 0.3, fontFace: FONT, fontSize: 10, bold: true, color: C.slate, charSpacing: 1.5, margin: 0 });
      s.addText([
        { text: r.num, options: { fontSize: 23, bold: true, color: C.text } },
        { text: r.delta, options: { fontSize: 11.5, bold: true, color: r.dc } },
      ], { x: 8.35, y: r.y + 0.58, w: 4.25, h: 0.62, fontFace: FONT, margin: 0, valign: 'bottom' });
    }
    s.addNotes('Driverne bak veksten: utfaktureringsgrad opp fra 74 til 78 prosent (mål over 80 i Q3), timepris opp 25 kr til 1 480 kr, 12 nyansettelser gir kapasitet, og sykefraværet falt til 3,1 prosent.');
  }

  /* ---------- Slide 5: Prioriteringer Q3 ---------- */
  {
    const s = p.addSlide({ masterName: 'Heading og tre felt' });
    kicker(s, 'VEIEN VIDERE · Q3 2026');
    heading(s, 'Q3 prioriterer seniorrekruttering, CSRD-team og utfakturering over 80 prosent');
    const cards = [
      {
        x: 0.6, icon: 'users', nr: 'PRIORITET 1', h: 'Rekruttering av seniorer',
        b: 'Forsterke leveransene med erfarne rådgivere som kan lede team og eie kundeansvar. Nyansettelsene i Q2 gir kapasitet – seniorene skal gi retning og kvalitet.',
      },
      {
        x: 4.725, icon: 'filetext', nr: 'PRIORITET 2', h: 'Etablere CSRD-team',
        b: 'Samle et dedikert fagmiljø for bærekraftsrapportering. Etterspørselen etter CSRD-støtte øker, og et eget team posisjonerer Rådgivning tidlig i markedet.',
      },
      {
        x: 8.85, icon: 'target', nr: 'PRIORITET 3', h: `Utfakturering over 80${NB}%`,
        b: 'Løfte utfaktureringsgraden fra 78 til over 80 prosent gjennom strammere bemanningsplanlegging og riktig prosjektmiks.',
      },
    ];
    for (const cd of cards) {
      s.addShape(p.ShapeType.roundRect, { x: cd.x, y: 2.05, w: 3.88, h: 4.35, fill: { color: C.white }, rectRadius: 0.12 });
      s.addText(cd.nr, { x: cd.x + 0.32, y: 2.4, w: 3.2, h: 0.3, fontFace: FONT, fontSize: 10, bold: true, color: C.slate, charSpacing: 2, margin: 0 });
      s.addShape(p.ShapeType.ellipse, { x: cd.x + 0.32, y: 2.8, w: 0.56, h: 0.56, fill: { color: C.red } });
      s.addImage({ data: IC[cd.icon], x: cd.x + 0.45, y: 2.93, w: 0.3, h: 0.3 });
      s.addText(cd.h, { x: cd.x + 0.32, y: 3.6, w: 3.3, h: 0.6, fontFace: FONT, fontSize: 16.5, bold: true, color: C.text, margin: 0, valign: 'top' });
      s.addText(cd.b, { x: cd.x + 0.32, y: 4.25, w: 3.26, h: 1.95, fontFace: FONT, fontSize: 12, color: C.text, margin: 0, valign: 'top', lineSpacingMultiple: 1.15 });
    }
    s.addText('Prioriteringene følges opp med status i kvartalsgjennomgangen for Q3.', { x: 0.6, y: 6.62, w: 12.1, h: 0.35, fontFace: FONT, fontSize: 11, italic: true, color: C.slate, margin: 0 });
    s.addNotes('Tre prioriteringer for Q3: rekruttering av seniorer, etablere CSRD-team og utfaktureringsgrad over 80 prosent.');
  }

  await p.writeFile({ fileName: path.join(OUT, 'q2_status_radgivning.pptx') });
  console.log('Wrote q2_status_radgivning.pptx');
})().catch((e) => { console.error(e); process.exit(1); });
