"""Generate demo annual reports for trying the app: Norwegian investment
companies, metric "Verdijustert egenkapital" (value-adjusted equity).

THESE ARE NOT THE COMPANIES' REPORTS. They are synthetic stand-ins, stamped as
such on every page. What is real is the figures — each company's publicly
reported value-adjusted equity, so the extracted table is a true time series
(see SOURCES). They were read off public summaries and press releases rather
than the audited PDFs, so treat them as indicative; for real work, run the app
on the real reports.

The point of the corpus is that the three companies report the SAME metric in
genuinely different ways, which is what breaks naive extraction:

  Ferd       billions, one decimal        "55,3 milliarder kroner"
  Aker ASA   millions, space-separated    "67 259 millioner kroner", plus a
                                          per-share figure on the same page
  Sundt      billions, via a percentage   "steg 12 prosent til 16,3 milliarder"

Every report also states the metric several times — group highlights, a
key-figures table with the prior year beside it, and business-segment rows
with smaller numbers — so only one of the numbers on the page is the answer.

Typeset with ReportLab's document engine — real paragraph and table
flowables, so the text runs, kerning and per-cell layout are produced the way
a publishing tool produces them rather than by placing strings at
coordinates. Table cells come out as separate text objects, exactly as they
do in a real report.

Usage:  python make_demo_reports.py [output_dir]
"""

import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

SOURCES = [
    "Ferd 2021: ferd.no/ferdmagasinet — 'Historisk høyt årsresultat for Ferd'",
    "Ferd 2022: aarsrapport2022.ferd.no/oppsummering-av-ferds-2022-resultat/",
    "Ferd 2023: kommunikasjon.ntb.no — 'God verdiøkning for Ferd i 2023'",
    "Ferd 2024: aarsrapport2024.ferd.no/en/financial-results-for-2024/",
    "Ferd 2025: kommunikasjon.ntb.no — 'Ferd styrker posisjonen – passerer 55 milliarder'",
    "Aker 2021-2025: Aker ASA årsrapporter / E24 kvartalsdekning",
    "Sundt 2019-2022: kommunikasjon.ntb.no — Sundt AS pressemeldinger",
]

STAMP = "SYNTETISK DEMODOKUMENT — ikke selskapets årsrapport"

# (year, value-adjusted equity at year end, at year start) as each company
# prints it. "~" marks a figure published only rounded to the billion.
COMPANIES = {
    "Ferd": {
        "unit": "milliarder kroner",
        "unit_short": "mrd. kroner",
        "segments": [("Ferd Capital", "37,9"), ("Ferd Eiendom", "5,1"),
                     ("Ferd Ekstern Forvaltning", "8,4")],
        "series": [
            (2021, "48,0", "41,1"),
            (2022, "43,0", "48,0"),
            (2023, "45,8", "43,0"),
            (2024, "50,4", "45,8"),
            (2025, "55,3", "50,4"),
        ],
    },
    "Aker ASA": {
        "unit": "millioner kroner",
        "unit_short": "mill. kroner",
        # Aker also prints a per-share figure right next to the total — a
        # number of the same shape, on the same page, that is not the answer.
        "per_share": "905",
        "segments": [("Industrielle investeringer", "48 120"),
                     ("Finansielle investeringer", "19 139")],
        "series": [
            (2021, "69 787", "53 354"),
            (2022, "66 900", "69 787"),
            (2023, "63 200", "66 900"),
            (2024, "58 156", "63 200"),
            (2025, "67 259", "58 156"),
        ],
    },
    "Sundt": {
        "unit": "milliarder kroner",
        "unit_short": "mrd. kroner",
        "segments": [("Pandox", "6,2"), ("Finansielle investeringer", "4,4")],
        "series": [
            (2019, "15,9", "12,4"),
            (2020, "14,5", "15,9"),
            (2021, "16,3", "14,5"),
            (2022, "13,9", "16,3"),
        ],
    },
}

_styles = getSampleStyleSheet()
_H1 = ParagraphStyle("h1", parent=_styles["Title"], fontSize=24, alignment=TA_LEFT,
                     spaceAfter=2)
_SUB = ParagraphStyle("sub", parent=_styles["Normal"], fontSize=13, spaceAfter=2)
_STAMP = ParagraphStyle("stamp", parent=_styles["Normal"], fontSize=7.5,
                        textColor=colors.grey, spaceAfter=14)
_H2 = ParagraphStyle("h2", parent=_styles["Heading2"], fontSize=13, spaceBefore=14,
                     spaceAfter=6)
_BODY = ParagraphStyle("body", parent=_styles["Normal"], fontSize=10.5, leading=15,
                       spaceAfter=6)
_NOTE = ParagraphStyle("note", parent=_styles["Normal"], fontSize=8.5,
                       textColor=colors.grey, spaceBefore=4)

_TABLE_STYLE = TableStyle([
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTSIZE", (0, 0), (-1, -1), 10),
    ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
    ("LINEBELOW", (0, 0), (-1, 0), 0.6, colors.HexColor("#444444")),
    ("LINEBELOW", (0, 1), (-1, -1), 0.25, colors.HexColor("#dddddd")),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ("TOPPADDING", (0, 0), (-1, -1), 5),
])


def _story(company: str, spec: dict, year: int, vek: str, prev: str):
    unit, short = spec["unit"], spec["unit_short"]

    if company == "Sundt":
        lead = (f"Verdijustert egenkapital steg gjennom {year} til "
                f"{vek} {unit} ved årsskiftet, fra {prev} {unit}.")
    else:
        lead = (f"Konsernets verdijusterte egenkapital var {vek} {unit} ved "
                f"utgangen av {year}, mot {prev} {unit} ved inngangen til året.")

    story = [
        Paragraph(company, _H1),
        Paragraph(f"Årsrapport {year}", _SUB),
        Paragraph(STAMP, _STAMP),
        Paragraph("Hovedpunkter", _H2),
        Paragraph(lead, _BODY),
    ]
    if spec.get("per_share"):
        story.append(Paragraph(
            f"Verdijustert egenkapital per aksje var {spec['per_share']} kroner "
            f"ved utgangen av {year}.", _BODY))
    story.append(Paragraph(
        "Avkastningen måles på verdijustert egenkapital og er konsernets "
        "viktigste styringsparameter.", _BODY))

    story.append(Paragraph("Forretningsområder", _H2))
    seg_data = [["Verdijustert egenkapital per område", str(year), str(year - 1)]]
    seg_data += [[name, value, "–"] for name, value in spec["segments"]]
    seg = Table(seg_data, colWidths=[9.5 * cm, 3.2 * cm, 3.2 * cm])
    seg.setStyle(_TABLE_STYLE)
    story += [seg, Paragraph(f"Beløp i {short}.", _NOTE), PageBreak()]

    story.append(Paragraph("Nøkkeltall for konsernet", _H2))
    key_data = [
        [f"Beløp i {short}", str(year), str(year - 1)],
        ["Verdijustert egenkapital", vek, prev],
        ["Bokført egenkapital", "–", "–"],
    ]
    key = Table(key_data, colWidths=[9.5 * cm, 3.2 * cm, 3.2 * cm])
    key.setStyle(_TABLE_STYLE)
    story += [key, Spacer(1, 18), Paragraph(STAMP, _NOTE)]
    return story


def build(out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for company, spec in COMPANIES.items():
        slug = company.replace(" ", "-")
        for year, vek, prev in spec["series"]:
            target = out_dir / f"{slug}-Arsrapport-{year}-DEMO.pdf"
            doc = SimpleDocTemplate(
                str(target), pagesize=A4,
                leftMargin=2.2 * cm, rightMargin=2.2 * cm,
                topMargin=2.2 * cm, bottomMargin=2.2 * cm,
                title=f"{company} Årsrapport {year} (demo)",
            )
            doc.build(_story(company, spec, year, vek, prev))
            written.append(target)
            print(f"wrote {target}")
    return written


def main() -> None:
    out_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "out"
    build(out_dir)
    print("\nSynthetic demo documents — not the companies' annual reports.")
    print("Figures as publicly reported:")
    for src in SOURCES:
        print(f"  {src}")


if __name__ == "__main__":
    main()
