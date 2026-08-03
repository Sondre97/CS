"""End-to-end pipeline test on a synthetic quarterly report.

Covers PDF text extraction, heuristic extraction, localisation (including
NBSP-formatted numbers and label-based disambiguation), highlight rendering
and annotated-PDF generation — everything except the live serving endpoint,
whose response parsing is covered separately below.
"""

import sys
from pathlib import Path

import pymupdf as fitz

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from llm_extractor import _extract_json, _merge, chunk_pages, extract_heuristic  # noqa: E402
from models import Finding  # noqa: E402
from pdf_utils import (  # noqa: E402
    build_annotated_pdf,
    extract_pages,
    locate_finding,
    render_page_with_highlights,
)


def make_report() -> bytes:
    doc = fitz.open()
    page = doc.new_page()  # A4-ish default 612x792
    lines = [
        "BDO Demo ASA",
        "Quarterly Report Q2 2025",
        "",
        "Highlights",
        "Revenue growth of 12 % compared with Q2 2024.",
        "",
        "Key figures (MNOK)",
        "Revenue  1 234,5",
        "EBITDA  210,7",
        "Operating profit  148,2",
        "Net income  98,3",
    ]
    y = 72
    for line in lines:
        page.insert_text((72, y), line, fontsize=11)
        y += 20

    page2 = doc.new_page()
    page2.insert_text((72, 72), "Notes", fontsize=11)
    page2.insert_text((72, 100), "Revenue in the segment was 55,0 MNOK.", fontsize=11)
    return doc.tobytes()


def test_extract_pages():
    pages = extract_pages(make_report())
    assert len(pages) == 2
    assert "Quarterly Report" in pages[0]


def test_heuristic_finds_metrics():
    pages = extract_pages(make_report())
    findings = extract_heuristic(pages, ["Revenue", "EBITDA", "Net income", "Bogus metric"])
    by_name = {f.metric: f for f in findings}
    assert by_name["Revenue"].found
    assert by_name["EBITDA"].found and by_name["EBITDA"].value == "210,7"
    assert by_name["Net income"].found and by_name["Net income"].value == "98,3"
    assert not by_name["Bogus metric"].found


def test_locate_nbsp_number():
    """A value quoted with NBSP ('1<NBSP>234,5') must still be pinned to the
    'Revenue  1 234,5' row printed with regular spaces."""
    pdf = make_report()
    f = Finding(metric="Revenue", found=True, value="1\u00a0234,5", page=0, label="Revenue")
    f = locate_finding(pdf, f, 2)
    assert f.located and f.page == 0
    assert f.value_rects, "value rectangles expected"
    assert f.label_rects, "label rectangles expected"


def test_locate_disambiguates_by_label():
    """Two 'Revenue' occurrences exist; the value pins to the right page."""
    pdf = make_report()
    f = Finding(metric="Revenue", found=True, value="55,0", page=1, label="Revenue")
    f = locate_finding(pdf, f, 2)
    assert f.located and f.page == 1


def test_locate_recovers_from_wrong_page():
    pdf = make_report()
    f = Finding(metric="EBITDA", found=True, value="210,7", page=1, label="EBITDA")
    f = locate_finding(pdf, f, 2)
    assert f.located and f.page == 0


def test_render_and_annotate():
    pdf = make_report()
    f = Finding(metric="EBITDA", found=True, value="210,7", page=0, label="EBITDA")
    f = locate_finding(pdf, f, 2)
    png = render_page_with_highlights(pdf, f.page, f.value_rects, f.label_rects, f.context_rects)
    assert png[:8] == b"\x89PNG\r\n\x1a\n"

    annotated = build_annotated_pdf(pdf, [f])
    assert annotated[:5] == b"%PDF-"
    with fitz.open(stream=annotated, filetype="pdf") as doc:
        annots = list(doc[0].annots())
        assert len(annots) >= 1


def test_extract_json_variants():
    assert _extract_json('{"results": []}') == {"results": []}
    assert _extract_json('```json\n{"results": []}\n```') == {"results": []}
    assert _extract_json('Here you go: {"results": [{"a": 1}]} hope it helps')["results"] == [{"a": 1}]


def test_chunking_and_merge():
    pages = ["x" * 30, "y" * 30, "z" * 30]
    chunks = list(chunk_pages(pages, chunk_chars=60))
    assert [c[0] for c in chunks] == [0, 2]

    low = Finding(metric="Revenue", found=True, value="1", confidence="low", page=3)
    high = Finding(metric="revenue", found=True, value="2", confidence="high", page=7)
    merged = _merge(["Revenue"], [[low], [high]])
    assert len(merged) == 1 and merged[0].value == "2"


# --- Regression tests for review findings ------------------------------------


def make_rotated_report() -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 90), "Landscape appendix", fontsize=11)
    page.insert_text((72, 110), "EBITDA  210,7", fontsize=11)
    page.set_rotation(90)
    return doc.tobytes()


def test_rotated_page_highlight_position():
    """Rects come back in unrotated space; the PNG overlay must land on the
    ink of the rendered (rotated) page."""
    pdf = make_rotated_report()
    f = Finding(metric="EBITDA", found=True, value="210,7", page=0, label="EBITDA")
    f = locate_finding(pdf, f, 1)
    assert f.located
    png = render_page_with_highlights(pdf, 0, f.value_rects, f.label_rects, [])

    import io
    from PIL import Image
    img = Image.open(io.BytesIO(png)).convert("RGB")
    with fitz.open(stream=pdf, filetype="pdf") as doc:
        page = doc[0]
        zoom = min(3.0, max(1.0, 1600 / page.rect.width))
        r = fitz.Rect(f.value_rects[0]) * page.rotation_matrix
        r.normalize()
    cx, cy = int((r.x0 + r.x1) / 2 * zoom), int((r.y0 + r.y1) / 2 * zoom)
    pr, pg, pb = img.getpixel((cx, cy))
    # Inside the translucent red fill the red channel dominates.
    assert pr > pg and pr > pb, f"highlight not at rotated position: {(pr, pg, pb)}"


def test_render_out_of_bounds_rect_does_not_crash():
    pdf = make_report()
    png = render_page_with_highlights(pdf, 0, [(10000.0, 10000.0, 10100.0, 10050.0)])
    assert png[:8] == b"\x89PNG\r\n\x1a\n"


def test_value_not_pinned_inside_other_number():
    """Value '12' must not match the tail of '2012'."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 90), "Annual Report 2012", fontsize=11)
    page.insert_text((72, 130), "Growth was 12 percent", fontsize=11)
    pdf = doc.tobytes()
    f = Finding(metric="Growth", found=True, value="12", page=0, label="Growth")
    f = locate_finding(pdf, f, 1)
    assert f.located
    # the pinned rect must sit on the 'Growth was 12' line (y ~118-131), not the title
    assert f.value_rects[0][1] > 110


def test_multiline_quote_grouped():
    doc = fitz.open()
    page = doc.new_page()
    quote = ("Revenue for the second quarter came in at 1 234,5 MNOK, an "
             "increase of 12 % compared with the same period last year")
    # wrap the sentence over three printed lines
    page.insert_text((72, 90), quote[:55], fontsize=11)
    page.insert_text((72, 104), quote[55:110], fontsize=11)
    page.insert_text((72, 118), quote[110:], fontsize=11)
    pdf = doc.tobytes()
    f = Finding(metric="Revenue", found=True, value="1 234,5", page=0,
                label="Revenue", quote=quote)
    f = locate_finding(pdf, f, 1)
    assert f.located
    assert len(f.context_rects) >= 3, f"expected all quote lines highlighted, got {f.context_rects}"


def test_columns_not_fused():
    from llm_extractor import _line_number_candidates
    tokens = [tok for _, tok in _line_number_candidates("Revenue  1 234,5  1 100,2")]
    assert tokens == ["1 234,5", "1 100,2"]


def test_heuristic_skips_dates():
    findings = extract_heuristic(
        ["Total equity as of 31.12.2025 was 500,0 MNOK."], ["Total equity"]
    )
    assert findings[0].found and findings[0].value == "500,0"


def test_merge_no_aliasing_between_metrics():
    a = Finding(metric="Revenue FY2024", found=True, value="100")
    b = Finding(metric="Revenue FY2023", found=True, value="90")
    merged = _merge(["Revenue 2024", "Revenue 2023"], [[a, b]])
    assert merged[0] is not merged[1]
    assert {merged[0].value, merged[1].value} == {"100", "90"}
    # originals must not be renamed in place
    assert a.metric == "Revenue FY2024" and b.metric == "Revenue FY2023"


def test_password_protected_pdf_raises():
    doc = fitz.open()
    doc.new_page().insert_text((72, 90), "secret", fontsize=11)
    encrypted = doc.tobytes(encryption=fitz.PDF_ENCRYPT_AES_256, user_pw="pw")
    import pytest
    with pytest.raises(Exception):
        extract_pages(encrypted)
