"""Generate demo report PDFs for trying the app: Ferd (family office),
annual reports 2021-2025, metric "Verdijustert egenkapital".

THESE ARE NOT FERD'S REPORTS. They are synthetic two-page stand-ins, stamped
as such on every page, written so the app has something realistic to chew on
when the real PDFs are not at hand. The layout mimics a real report: a
highlights page with prose (decoy numbers alongside the metric) and a
key-figures table where the metric row carries both the current and the prior
year, so label-proximity and column disambiguation actually get exercised.

The value-adjusted-equity figures below are Ferd's publicly reported ones, so
the demo shows a true time series — see SOURCES. They were read off public
summaries and press releases rather than the audited PDFs, so treat them as
indicative: for real work, run the app on the real reports from ferd.no.

Usage:  python make_ferd_demo.py [output_dir]
"""

import sys
from pathlib import Path

import pymupdf as fitz

SOURCES = [
    "2021: ferd.no/ferdmagasinet/2022/utgave-1-2022/historisk-hoyt-arsresultat-for-ferd/",
    "2022: aarsrapport2022.ferd.no/oppsummering-av-ferds-2022-resultat/",
    "2023: kommunikasjon.ntb.no — 'God verdiøkning for Ferd i 2023'",
    "2024: aarsrapport2024.ferd.no/en/financial-results-for-2024/",
    "2025: kommunikasjon.ntb.no — 'Ferd styrker posisjonen – passerer 55 milliarder kroner'",
]

# (year, VEK at year end in NOK billion, VEK at year start, return on VEK in %)
# Returns are as reported: whole percent for 2022/2023, one decimal elsewhere.
FERD_VEK = [
    (2021, "48,0", "41,1", "17,7"),
    (2022, "43,0", "48,0", "-9"),
    (2023, "45,8", "43,0", "9"),
    (2024, "50,4", "45,8", "12,0"),
    (2025, "55,3", "50,4", "11,1"),
]


STAMP = "SYNTETISK DEMODOKUMENT — ikke Ferds årsrapport"


def _stamp(page: fitz.Page) -> None:
    page.insert_text((72, page.rect.height - 48), STAMP,
                     fontsize=8, color=(0.62, 0.62, 0.62))


def build_report(year: int, vek: str, prev: str, ret: str) -> bytes:
    doc = fitz.open()

    page = doc.new_page()
    y = 80
    page.insert_text((72, y), "Ferd", fontsize=26, fontname="hebo"); y += 26
    page.insert_text((72, y), f"Årsrapport {year}", fontsize=15); y += 16
    page.insert_text((72, y), STAMP, fontsize=8, color=(0.45, 0.45, 0.45)); y += 40
    page.insert_text((72, y), "Hovedpunkter", fontsize=13, fontname="hebo"); y += 22
    for line in [
        f"Ferd oppnådde i {year} en avkastning på verdijustert egenkapital på {ret} prosent.",
        f"Konsernets verdijusterte egenkapital var {vek} milliarder kroner ved utgangen av {year},",
        f"mot {prev} milliarder kroner ved inngangen til året.",
        "Ferd Capital var konsernets største forretningsområde målt i kapital.",
    ]:
        page.insert_text((72, y), line, fontsize=10.5); y += 16

    page2 = doc.new_page()
    y = 80
    page2.insert_text((72, y), "Nøkkeltall for konsernet", fontsize=13, fontname="hebo"); y += 14
    page2.insert_text((72, y), "Beløp i milliarder kroner", fontsize=8.5,
                      color=(0.45, 0.45, 0.45)); y += 22
    page2.insert_text((300, y), str(year), fontsize=10, fontname="hebo")
    page2.insert_text((380, y), str(year - 1), fontsize=10, fontname="hebo"); y += 18
    rows = [
        ("Verdijustert egenkapital", vek, prev),
        ("Avkastning verdijustert egenkapital (%)", ret, "—"),
        ("Bokført egenkapital", "—", "—"),
    ]
    for label, v1, v0 in rows:
        page2.insert_text((72, y), label, fontsize=10)
        page2.insert_text((300, y), v1, fontsize=10)
        page2.insert_text((380, y), v0, fontsize=10)
        y += 17

    for page in doc:
        _stamp(page)
    return doc.tobytes()


def main() -> None:
    out_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    for year, vek, prev, ret in FERD_VEK:
        path = out_dir / f"Ferd-Arsrapport-{year}-DEMO.pdf"
        path.write_bytes(build_report(year, vek, prev, ret))
        print(f"wrote {path}")
    print("\nSynthetic demo documents — not Ferd's annual reports.")
    print("Figures as publicly reported:")
    for src in SOURCES:
        print(f"  {src}")


if __name__ == "__main__":
    main()
