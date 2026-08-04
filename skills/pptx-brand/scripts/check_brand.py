#!/usr/bin/env python3
"""
check_brand.py - deterministisk merkevaresjekk for BDO-presentasjoner (.pptx/.potx).

Kjører uten tredjepartsbiblioteker: en .pptx er en ZIP med XML, og sjekkene
leser XML-en direkte. Brukes bade som selvkontroll i produksjon (fiks alle
FAIL for levering) og som kode-gradert eval i skill-malingen.

Bruk:
    python check_brand.py deck.pptx            # lesbar rapport
    python check_brand.py deck.pptx --json     # maskinlesbar (evals/CI)

Exit-kode 0 = ingen FAIL. Exit-kode 1 = minst en FAIL (WARN stopper ikke).

Sjekker:
  slide_size    16:9-format
  fonts         kun Trebuchet MS / Bliss i innhold (Office-kanal, jf. bdo-design)
  colors        alle eksplisitte farger pa BDO-paletten, som tint/skygge av den,
                eller noytrale (gratoner)
  theme         temafargene er BDO-temaet (WARN for genererte deck uten tema)
  scheme_usage  schemeClr-referanser nar temaet IKKE er BDO (arver feil farger)
  placeholders  ingen lorem/TODO/[sett inn]-rester i slidetekst
  layouts       layoutbruk per slide (WARN ved Blank/Tom)
"""

import json
import re
import signal
import sys
import zipfile
from fractions import Fraction

# Ufarlig ved `... | head`: avslutt stille i stedet for BrokenPipeError-traceback
if hasattr(signal, "SIGPIPE"):
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)

# Fasit fra bdo-design (offisiell PPT-mal, nov. 2023)
BRAND_COLORS = {
    "E81A3B": "primaer rod (accent1)",
    "333333": "tekst (dk2)",
    "5B6E7F": "slate (accent2)",
    "98002E": "burgunder (accent3)",
    "D67900": "oransje (accent4)",
    "009966": "gronn (accent5)",
    "008FD2": "bla (accent6)",
    "0062B8": "lenker (hlink)",
    "F2F2F2": "lys bakgrunn (lt2)",
}
EXPECTED_THEME = {
    "accent1": "E81A3B", "accent2": "5B6E7F", "accent3": "98002E",
    "accent4": "D67900", "accent5": "009966", "accent6": "008FD2",
    "dk2": "333333", "lt2": "F2F2F2", "hlink": "0062B8",
}
# Trebuchet MS er Office-typografien; Bliss (Pro) er hovedtypografien der den
# er tilgjengelig. "+mj-lt"/"+mn-lt" er referanser til temaets fonter og
# vurderes via theme-sjekken i stedet.
ALLOWED_FONT = re.compile(r"^(\+m[jn]-(lt|ea|cs)|Trebuchet MS|Bliss.*)$")

PLACEHOLDER_RX = re.compile(
    r"lorem|ipsum|\bTODO\b|\bXXXX*\b|\[sett inn|\[insert|"
    r"klikk for [aå] (legge til|redigere)|click to (add|edit)|placeholder",
    re.IGNORECASE,
)

EMU_PER_INCH = 914400


def hex_to_rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def is_neutral(rgb, tol=6):
    """Gratoner (inkl. svart/hvit) er alltid lov."""
    r, g, b = rgb
    return max(r, g, b) - min(r, g, b) <= tol


def is_tint_or_shade(rgb, brand_rgb, tol=8):
    """Ligger fargen pa linjen mellom en merkefarge og hvit/svart?

    Tint (mot hvit) og skygge (mot svart) av palettfargene er vanlig og lov,
    f.eks. lys rod flate bak et nokkeltall.
    """
    for base in (255, 0):
        ts = []
        informative = True
        for c, bc in zip(rgb, brand_rgb):
            denom = bc - base
            if abs(denom) < 8:  # kanalen skiller ikke merkefarge fra basen
                if abs(c - base) > tol:
                    informative = False
                    break
                continue
            ts.append((c - base) / denom)
        if not informative or not ts:
            continue
        t = sum(ts) / len(ts)
        if not 0.0 <= t <= 1.02:
            continue
        if all(abs(bc * t + base * (1 - t) - c) <= tol for c, bc in zip(rgb, brand_rgb)):
            return True
    return False


def classify_color(hexval):
    """Returnerer (klasse, referansefarge). Klasser: brand, neutral, near, tint, violation.

    "near" = innenfor +-8 per kanal av en palettfarge uten aa vaere eksakt -
    typisk en feilhusket hex (f.eks. ED1A3B for E81A3B). Teller ikke som brudd,
    men rapporteres saa den kan rettes til eksakt verdi.
    """
    hexval = hexval.upper()
    if hexval in BRAND_COLORS:
        return "brand", hexval
    rgb = hex_to_rgb(hexval)
    if is_neutral(rgb):
        return "neutral", None
    for bh in BRAND_COLORS:
        if all(abs(c - b) <= 8 for c, b in zip(rgb, hex_to_rgb(bh))):
            return "near", bh
    for bh in BRAND_COLORS:
        if is_tint_or_shade(rgb, hex_to_rgb(bh)):
            return "tint", bh
    return "violation", None


class Deck:
    def __init__(self, path):
        self.zf = zipfile.ZipFile(path)
        names = self.zf.namelist()
        num = lambda p: int(re.search(r"(\d+)\.xml$", p).group(1))
        self.slides = sorted((n for n in names if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)), key=num)
        self.layouts = sorted((n for n in names if re.fullmatch(r"ppt/slideLayouts/slideLayout\d+\.xml", n)), key=num)
        self.masters = sorted((n for n in names if re.fullmatch(r"ppt/slideMasters/slideMaster\d+\.xml", n)), key=num)
        self.charts = sorted(n for n in names if re.match(r"ppt/charts/chart\d+\.xml$", n))
        self.themes = sorted(n for n in names if re.match(r"ppt/theme/theme\d+\.xml$", n))
        self._cache = {}

    def read(self, name):
        if name not in self._cache:
            self._cache[name] = self.zf.read(name).decode("utf-8", errors="ignore")
        return self._cache[name]

    def content_files(self):
        """Filene der farger og fonter faktisk brukes (ikke tema, ikke notater)."""
        return self.slides + self.layouts + self.masters + self.charts

    def layout_name(self, slide):
        rels = slide.replace("ppt/slides/", "ppt/slides/_rels/") + ".rels"
        try:
            m = re.search(r'Target="[^"]*?(slideLayout\d+\.xml)"', self.read(rels))
            if not m:
                return None
            layout = "ppt/slideLayouts/" + m.group(1)
            name = re.search(r'<p:cSld[^>]*name="([^"]*)"', self.read(layout))
            return name.group(1) if name and name.group(1) else "(uten navn)"
        except KeyError:
            return None


def short(files_counter, limit=4):
    items = sorted(files_counter.items(), key=lambda kv: -kv[1])[:limit]
    return ", ".join(f"{f.split('/')[-1]}:{c}" for f, c in items)


def run_checks(path):
    deck = Deck(path)
    checks = []

    def add(cid, status, message, details=None):
        checks.append({"id": cid, "status": status, "message": message,
                       "details": details or []})

    # -- slide_size ----------------------------------------------------------
    pres = deck.read("ppt/presentation.xml")
    m = re.search(r'<p:sldSz[^>]*cx="(\d+)"[^>]*cy="(\d+)"', pres)
    if not m:
        add("slide_size", "FAIL", "Fant ikke slidestorrelse i presentation.xml")
    else:
        cx, cy = int(m.group(1)), int(m.group(2))
        ratio = Fraction(cx, cy)
        if abs(cx / cy - 16 / 9) < 0.01:
            add("slide_size", "PASS",
                f"16:9 ({cx / EMU_PER_INCH:.2f}\" x {cy / EMU_PER_INCH:.2f}\")")
        else:
            add("slide_size", "FAIL",
                f"Format er {ratio} ({cx / EMU_PER_INCH:.2f}\" x {cy / EMU_PER_INCH:.2f}\"), ikke 16:9")

    # -- fonts ---------------------------------------------------------------
    font_hits = {}
    for f in deck.content_files():
        for tf in re.findall(r'<a:latin[^>]*typeface="([^"]*)"', deck.read(f)):
            if tf and not ALLOWED_FONT.match(tf):
                font_hits.setdefault(tf, {}).setdefault(f, 0)
                font_hits[tf][f] += 1
    if font_hits:
        det = [f"'{tf}' ({sum(fs.values())} steder: {short(fs)})" for tf, fs in sorted(font_hits.items())]
        add("fonts", "FAIL", f"{len(font_hits)} ikke-godkjente fonter i bruk "
            "(tillatt: Trebuchet MS, Bliss)", det)
    else:
        add("fonts", "PASS", "Kun Trebuchet MS / Bliss / temafonter i innholdet")

    # -- theme ---------------------------------------------------------------
    theme_ok = False
    if deck.themes:
        theme_xml = deck.read(deck.themes[0])
        diffs = []
        for slot, want in EXPECTED_THEME.items():
            tm = re.search(rf'<a:{slot}>\s*<a:(?:srgbClr|sysClr)[^>]*(?:val|lastClr)="([0-9A-Fa-f]{{6}})"',
                           theme_xml)
            got = tm.group(1).upper() if tm else "mangler"
            if got != want:
                diffs.append(f"{slot}: {got} (skal vaere {want})")
        theme_ok = not diffs
        theme_fonts = re.findall(r'<a:(?:majorFont|minorFont)>\s*<a:latin[^>]*typeface="([^"]*)"', theme_xml)
        bad_theme_fonts = [tf for tf in theme_fonts if tf and not ALLOWED_FONT.match(tf)]
        if theme_ok and not bad_theme_fonts:
            add("theme", "PASS", "Temafarger og temafonter folger BDO-temaet")
        elif theme_ok:
            add("theme", "WARN", "Temafarger OK, men temafontene er ikke "
                f"Trebuchet/Bliss: {', '.join(bad_theme_fonts)}. Ufarlig hvis all "
                "tekst setter font eksplisitt.")
        else:
            add("theme", "WARN", "Temaet er ikke BDO-temaet. Malbasert deck: bruk "
                "den offisielle malen. Generert deck: greit sa lenge alle farger "
                "settes eksplisitt (se colors/scheme_usage).", diffs)
    else:
        add("theme", "WARN", "Ingen temafil funnet")

    # -- colors --------------------------------------------------------------
    usage = {}
    for f in deck.content_files():
        if "notesSlide" in f or "notesMaster" in f or "handout" in f:
            continue
        for hexval in re.findall(r'<a:srgbClr val="([0-9A-Fa-f]{6})"', deck.read(f)):
            h = hexval.upper()
            usage.setdefault(h, {}).setdefault(f, 0)
            usage[h][f] += 1
    classified = {h: classify_color(h) for h in usage}
    violations = {h: usage[h] for h, (cls, _) in classified.items() if cls == "violation"}
    nears = {h: ref for h, (cls, ref) in classified.items() if cls == "near"}
    if violations:
        det = [f"#{h} ({sum(fs.values())} steder: {short(fs)})"
               for h, fs in sorted(violations.items(), key=lambda kv: -sum(kv[1].values()))]
        add("colors", "FAIL", f"{len(violations)} farger utenfor BDO-paletten "
            "(tillatt: palettfargene, tint/skygge av dem, gratoner)", det)
    elif nears:
        det = [f"#{h} skal vaere #{ref} ({BRAND_COLORS[ref]}) - {sum(usage[h].values())} steder: {short(usage[h])}"
               for h, ref in sorted(nears.items())]
        add("colors", "WARN", f"{len(nears)} nesten-palettfarger (feilhusket hex?) "
            "- bytt til eksakt verdi", det)
    else:
        n_brand = sum(1 for h, (cls, _) in classified.items() if cls == "brand")
        add("colors", "PASS", f"Alle {len(usage)} eksplisitte farger er pa "
            f"paletten eller noytrale ({n_brand} rene palettfarger)")

    # -- scheme_usage --------------------------------------------------------
    # schemeClr-referanser arver fra temaet. Med BDO-tema er de riktige; uten
    # BDO-tema gir accent1-6/dk2/lt2/hlink Office-standardfarger (blatt osv.).
    if theme_ok:
        add("scheme_usage", "PASS", "Temafarge-referanser arver fra BDO-temaet")
    else:
        hits = {}
        for f in deck.slides + deck.charts:
            for slot in re.findall(r'<a:schemeClr val="(accent[1-6]|dk2|lt2|hlink)"', deck.read(f)):
                hits.setdefault(slot, {}).setdefault(f, 0)
                hits[slot][f] += 1
        if hits:
            det = [f"{slot} ({sum(fs.values())} steder: {short(fs)})" for slot, fs in sorted(hits.items())]
            add("scheme_usage", "FAIL", "Temafarge-referanser i et deck uten "
                "BDO-tema gir feil farger - sett fargene eksplisitt eller bruk BDO-malen", det)
        else:
            add("scheme_usage", "PASS", "Ingen temafarge-referanser som arver feil farger")

    # -- placeholders --------------------------------------------------------
    leftovers = []
    for i, f in enumerate(deck.slides, 1):
        for text in re.findall(r"<a:t>([^<]*)</a:t>", deck.read(f)):
            if PLACEHOLDER_RX.search(text):
                leftovers.append(f"slide {i}: '{text.strip()[:60]}'")
    if leftovers:
        add("placeholders", "FAIL", f"{len(leftovers)} rester av plassholdertekst", leftovers[:10])
    else:
        add("placeholders", "PASS", "Ingen plassholder-/lorem-rester i slidetekst")

    # -- layouts -------------------------------------------------------------
    names = [(i, deck.layout_name(s)) for i, s in enumerate(deck.slides, 1)]
    blanks = [i for i, n in names if n and n.strip().lower() in ("blank", "tom", "tom side")]
    det = [f"slide {i}: {n or '(ukjent)'}" for i, n in names]
    if blanks:
        add("layouts", "WARN", f"Slide {', '.join(map(str, blanks))} bruker "
            "Blank-layout - velg en navngitt layout fra malen", det)
    else:
        add("layouts", "PASS", f"{len(deck.slides)} slides, ingen pa Blank-layout", det)

    summary = {s: sum(1 for c in checks if c["status"] == s) for s in ("PASS", "WARN", "FAIL")}
    return {
        "file": path,
        "slide_count": len(deck.slides),
        "chart_count": len(deck.charts),
        "checks": checks,
        "summary": summary,
        "ok": summary["FAIL"] == 0,
    }


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__)
        sys.exit(2)
    result = run_checks(args[0])
    if "--json" in sys.argv:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"Merkevaresjekk: {result['file']}  "
              f"({result['slide_count']} slides, {result['chart_count']} grafer)")
        for c in result["checks"]:
            print(f"  {c['status']:<5} {c['id']:<13} {c['message']}")
            for d in c["details"]:
                print(f"        - {d}")
        s = result["summary"]
        print(f"Resultat: {s['PASS']} PASS, {s['WARN']} WARN, {s['FAIL']} FAIL")
    sys.exit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
