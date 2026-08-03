"""Generate demo report PDFs for trying the app: Ferd (family office),
annual reports 2021-2025, metric "Verdijustert egenkapital".

The FIGURES are Ferd's real published numbers (from the public annual-report
summaries at aarsrapportNNNN.ferd.no / NTB press releases). The PDFs
themselves are reconstructed two-page extracts — clearly labelled as such —
because the original report PDFs cannot be redistributed here. Layout mimics
a typical report: a highlights page with prose (decoy numbers included) and a
key-figures table where the metric appears with the comparative year next to
it, so label-proximity disambiguation actually gets exercised.

Usage:  python make_ferd_demo.py [output_dir]
"""

import sys
from pathlib import Path

import pymupdf as fitz

# (year, VEK at year end in NOK billion, previous year VEK, return %)
FERD_VEK = [
    (2021, "48,0", "41,1", "17,7"),
    (2022, "43,0", "48,0", "-10,0"),
    (2023, "45,8", "43,0", "8,9"),
    (2024, "50,4", "45,8", "12,0"),
    (2025, "55,3", "50,4", "11,1"),
]


def build_report(year: int, vek: str, prev: str, ret: str) -> bytes:
    doc = fitz.open()

    page = doc.new_page()
    y = 80
    page.insert_text((72, y), "Ferd", fontsize=26, fontname="hebo"); y += 26
    page.insert_text((72, y), f"Årsrapport {year}", fontsize=15); y += 16
    page.insert_text((72, y), "(rekonstruert utdrag — demo, ikke originaldokumentet)",
                     fontsize=8, color=(0.45, 0.45, 0.45)); y += 40
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

    return doc.tobytes()


def main() -> None:
    out_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    for year, vek, prev, ret in FERD_VEK:
        path = out_dir / f"Ferd-Arsrapport-{year}.pdf"
        path.write_bytes(build_report(year, vek, prev, ret))
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
