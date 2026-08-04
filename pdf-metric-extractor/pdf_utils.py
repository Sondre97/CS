"""PDF text extraction, metric localisation and highlight rendering.

Localisation strategy (per finding):
  1. The verbatim value is matched against the page's word stream after
     separator normalisation — numbers like "1 234,5" are often split into
     several words or use non-breaking/thin spaces — with digit boundaries
     enforced so "12" never pins inside "2012".
  2. Labels and quotes go through ``page.search_for`` first (case-insensitive,
     multi-line capable), falling back to the normalised word stream.
  3. The claimed page is tried first, then neighbouring pages, then the whole
     document, in case the model cited a printed page number instead of the
     physical one. A page containing both the value and the label wins over a
     page containing the value alone.

When several occurrences of the value exist on a page, the one closest to an
occurrence of the metric's label wins (same-line matches strongly preferred).
"""

import io
import unicodedata

import pymupdf as fitz
from PIL import Image, ImageDraw

from models import Finding

# BDO palette (see bdo_theme.py)
_VALUE_FILL = (232, 26, 59, 70)      # #E81A3B, translucent
_VALUE_OUTLINE = (232, 26, 59, 255)
_LABEL_FILL = (91, 110, 127, 45)     # #5B6E7F, translucent
_CONTEXT_FILL = (214, 121, 0, 35)    # #D67900, very soft

_STRIP_CHARS = " \t\u00a0\u202f\u2009\u200a\u2007\u2008"  # incl. NBSP/thin/figure spaces
_CHAR_MAP = str.maketrans({
    "−": "-",  # minus sign
    "–": "-",  # en dash
    "—": "-",  # em dash
    "’": "'",
    "‘": "'",
    "“": '"',
    "”": '"',
})


def doc_from_bytes(pdf_bytes: bytes) -> fitz.Document:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    if doc.needs_pass:
        doc.close()
        raise ValueError("PDF is password-protected")
    return doc


def extract_pages(pdf_bytes: bytes) -> list[str]:
    """Plain text per page, in physical page order."""
    with doc_from_bytes(pdf_bytes) as doc:
        return [page.get_text("text") for page in doc]


def extract_rows(pdf_bytes: bytes) -> list[str]:
    """Per page, text rebuilt row by row from word geometry.

    ``get_text("text")`` walks blocks, and a table cell is often its own
    block — so a key-figures row comes out as "Verdijustert egenkapital",
    "50,4" and "45,8" on three separate lines, with no line that carries both
    the label and its number. Regrouping words by vertical band puts the row
    back together. Used alongside the plain text, never instead of it: on a
    two-column page this can join text across the gutter, so it only ever
    adds candidates for the ranking to sort out.
    """
    out = []
    with doc_from_bytes(pdf_bytes) as doc:
        for page in doc:
            words = page.get_text("words")
            if not words:
                out.append("")
                continue
            heights = sorted(w[3] - w[1] for w in words)
            tol = max(1.0, 0.5 * heights[len(heights) // 2])
            bands: list[tuple[float, list]] = []
            for w in sorted(words, key=lambda w: ((w[1] + w[3]) / 2, w[0])):
                center = (w[1] + w[3]) / 2
                if bands and abs(center - bands[-1][0]) <= tol:
                    bands[-1][1].append(w)
                else:
                    bands.append((center, [w]))
            lines = []
            for _, band in bands:
                band.sort(key=lambda w: w[0])
                parts = [band[0][4]]
                for prev, word in zip(band, band[1:]):
                    # Preserve the difference between a thousands separator and
                    # a column gap: "67 259" is one number, "67 259  58 156" is
                    # two. Joining everything with the same separator would
                    # either fuse the columns or split the number.
                    gap = word[0] - prev[2]
                    height = max(prev[3] - prev[1], 1.0)
                    parts.append(" " if gap < 0.5 * height else "  ")
                    parts.append(word[4])
                lines.append("".join(parts))
            out.append("\n".join(lines))
    return out


def _normalize(text: str, casefold: bool = False) -> str:
    """Strip all space-like chars and unify unicode punctuation."""
    text = unicodedata.normalize("NFKC", text).translate(_CHAR_MAP)
    for ch in _STRIP_CHARS:
        text = text.replace(ch, "")
    text = text.replace("\n", "").replace("\r", "")
    return text.casefold() if casefold else text


def _rect_center(r: tuple[float, float, float, float]) -> tuple[float, float]:
    return ((r[0] + r[2]) / 2.0, (r[1] + r[3]) / 2.0)


def _rect_distance(a, b) -> float:
    """Distance between rect centers, penalising vertical offset so that
    same-row label/value pairs (typical for tables) rank first."""
    ax, ay = _rect_center(a)
    bx, by = _rect_center(b)
    return abs(ax - bx) + 6.0 * abs(ay - by)


def _as_tuples(rects) -> list[tuple[float, float, float, float]]:
    return [(float(r.x0), float(r.y0), float(r.x1), float(r.y1)) for r in rects]


def _count_occurrences(page: fitz.Page, needle: str) -> int:
    """Non-overlapping occurrences of `needle` in the page text, both sides
    normalised and casefolded."""
    hay = _normalize(page.get_text("text"), casefold=True)
    target = _normalize(needle, casefold=True)
    if not target:
        return 0
    count = start = 0
    while True:
        idx = hay.find(target, start)
        if idx < 0:
            return count
        count += 1
        start = idx + len(target)


def _group_search_hits(page: fitz.Page, needle: str, hits):
    """``search_for`` returns one rect per printed-line fragment; fragments of
    a single multi-line occurrence must stay one group so the whole quote gets
    highlighted, not one arbitrary line of it."""
    if len(hits) <= 1:
        return [[r] for r in hits]
    count = _count_occurrences(page, needle)
    if count >= len(hits):
        return [[r] for r in hits]
    if count == 1:
        return [list(hits)]
    # Ambiguous: cluster fragments that continue on the next printed line.
    groups, current = [], [hits[0]]
    for prev, r in zip(hits, hits[1:]):
        line_h = max(prev.y1 - prev.y0, 1.0)
        if r.y0 > prev.y0 and (r.y0 - prev.y1) <= 0.8 * line_h:
            current.append(r)
        else:
            groups.append(current)
            current = [r]
    groups.append(current)
    return groups


def _touching(line_words, a: int, b: int) -> bool:
    """True when words a and b sit closer than a space — i.e. any gap between
    them is a thousands separator, not a column gap."""
    if a == b:
        return True
    left, right = (a, b) if a < b else (b, a)
    gap = line_words[right][0] - line_words[left][2]
    height = max(line_words[left][3] - line_words[left][1], 1.0)
    return gap < 0.28 * height


def _runs_into_digit(line_words, line_norm, char_owner, target, idx, end) -> bool:
    """Does the match bump into a digit that belongs to the same number?"""
    if target[0].isdigit() and idx > 0 and line_norm[idx - 1].isdigit():
        if _touching(line_words, char_owner[idx - 1], char_owner[idx]):
            return True
    if target[-1].isdigit() and end < len(line_norm) and line_norm[end].isdigit():
        if _touching(line_words, char_owner[end], char_owner[end - 1]):
            return True
    return False


def _search_words_normalized(page: fitz.Page, needle: str, casefold: bool = False,
                             digit_boundaries: bool = False):
    """Find `needle` in the page word stream after separator normalisation.

    Returns a list of rect-groups; each group is the list of word rects that
    together make up one occurrence. With ``digit_boundaries`` a match whose
    numeric edge runs into an adjacent digit is rejected, so value "12" never
    pins inside "2012" or "3.125".

    Adjacency is judged geometrically, not from the normalised string: spaces
    are stripped before matching (so "1 234,5" matches however it is spaced),
    which would otherwise fuse neighbouring table columns — "50,4    45,8"
    becomes "50,445,8" and a search for "50,4" would look digit-adjacent. A
    neighbouring digit only counts when it sits in the same word or less than
    a space away, i.e. is really part of the same number.
    """
    target = _normalize(needle, casefold=casefold)
    if not target:
        return []

    words = page.get_text("words")  # (x0, y0, x1, y1, word, block, line, word_no)
    # Group words by (block, line) so matches never leak across columns/rows.
    lines: dict[tuple[int, int], list] = {}
    for w in words:
        lines.setdefault((w[5], w[6]), []).append(w)

    groups = []
    for line_words in lines.values():
        line_words.sort(key=lambda w: w[7])
        norm_chars = []
        char_owner = []  # word index within line_words per normalised char
        for wi, w in enumerate(line_words):
            for ch in _normalize(w[4], casefold=casefold):
                norm_chars.append(ch)
                char_owner.append(wi)
        line_norm = "".join(norm_chars)
        start = 0
        while True:
            idx = line_norm.find(target, start)
            if idx < 0:
                break
            end = idx + len(target)
            if digit_boundaries and _runs_into_digit(
                    line_words, line_norm, char_owner, target, idx, end):
                start = idx + 1
                continue
            owners = sorted(set(char_owner[idx:end]))
            rects = [fitz.Rect(line_words[wi][:4]) for wi in owners]
            groups.append(rects)
            start = idx + 1
    return groups


def _find_on_page(page: fitz.Page, needle: str, casefold: bool = False,
                  numeric: bool = False):
    """All occurrences of `needle` on the page as rect-groups.

    ``numeric=True`` (used for metric values) skips ``search_for`` — which
    happily matches "12" inside "2012" — and goes straight to the normalised
    word stream with digit-boundary enforcement.
    """
    needle = needle.strip()
    if not needle:
        return []
    if numeric:
        return _search_words_normalized(page, needle, casefold=casefold,
                                        digit_boundaries=True)
    try:
        hits = page.search_for(needle)
    except Exception:
        hits = []
    if hits:
        return _group_search_hits(page, needle, hits)
    return _search_words_normalized(page, needle, casefold=casefold)


def _pick_nearest(groups, anchors):
    """Pick the rect-group nearest to any anchor rect."""
    if not groups:
        return None
    if not anchors or len(groups) == 1:
        return groups[0]

    def group_score(group):
        return min(
            _rect_distance((r.x0, r.y0, r.x1, r.y1), a)
            for r in group
            for a in anchors
        )

    return min(groups, key=group_score)


def locate_finding(pdf_bytes: bytes, finding: Finding, total_pages: int) -> Finding:
    """Resolve a finding's value/label/quote to rectangles on a page.

    Mutates and returns `finding`. Never raises on unlocatable content —
    `finding.located` stays False instead.
    """
    if not finding.found or not finding.value:
        return finding

    with doc_from_bytes(pdf_bytes) as doc:
        claimed = finding.page if finding.page is not None else 0
        claimed = max(0, min(claimed, total_pages - 1))

        # Claimed page first, then neighbours, then everything else.
        order = [claimed, claimed - 1, claimed + 1]
        order += [p for p in range(total_pages) if p not in order]
        order = [p for p in order if 0 <= p < total_pages]

        label_text = finding.label or finding.metric
        # A page with value AND label beats a page with the value alone —
        # the whole-document fallback would otherwise happily pin a bare
        # number inside unrelated text.
        value_only_fallback = None  # (page_index, value_groups)

        for page_index in order:
            page = doc[page_index]
            value_groups = _find_on_page(page, finding.value, numeric=True)
            if not value_groups:
                continue
            label_groups = _find_on_page(page, label_text, casefold=True)
            if not label_groups and value_only_fallback is None:
                value_only_fallback = (page_index, value_groups)
            if label_groups or page_index == claimed:
                break
        else:
            if value_only_fallback is None:
                return finding
            page_index, value_groups = value_only_fallback
            page = doc[page_index]
            label_groups = []

        label_anchor_rects = [
            (r.x0, r.y0, r.x1, r.y1) for g in label_groups for r in g
        ]
        chosen_value = _pick_nearest(value_groups, label_anchor_rects)
        chosen_label = _pick_nearest(
            label_groups,
            [(r.x0, r.y0, r.x1, r.y1) for r in chosen_value],
        )

        context_rects: list[fitz.Rect] = []
        if finding.quote and len(finding.quote) >= 12:
            quote_groups = _find_on_page(page, finding.quote)
            chosen_quote = _pick_nearest(
                quote_groups,
                [(r.x0, r.y0, r.x1, r.y1) for r in chosen_value],
            )
            if chosen_quote:
                context_rects = chosen_quote

        finding.page = page_index
        finding.located = True
        finding.value_rects = _as_tuples(chosen_value)
        finding.label_rects = _as_tuples(chosen_label or [])
        finding.context_rects = _as_tuples(context_rects)
        return finding


def merge_rects(rects, gap_ratio: float = 0.6):
    """Join rects that sit on one line and nearly touch.

    A value like "69 787" is two words, so it comes back as two rectangles;
    outlining each separately reads as two different highlights rather than
    one number.
    """
    remaining = [tuple(map(float, r)) for r in rects]
    merged = []
    while remaining:
        x0, y0, x1, y1 = remaining.pop(0)
        changed = True
        while changed:
            changed = False
            for other in list(remaining):
                ox0, oy0, ox1, oy1 = other
                same_line = min(y1, oy1) - max(y0, oy0) > 0.4 * min(y1 - y0, oy1 - oy0)
                gap = max(x0, ox0) - min(x1, ox1)
                if same_line and gap < gap_ratio * max(y1 - y0, oy1 - oy0):
                    x0, y0 = min(x0, ox0), min(y0, oy0)
                    x1, y1 = max(x1, ox1), max(y1, oy1)
                    remaining.remove(other)
                    changed = True
        merged.append((x0, y0, x1, y1))
    return merged


def render_page_with_highlights(
    pdf_bytes: bytes,
    page_index: int,
    value_rects,
    label_rects=(),
    context_rects=(),
    target_width: int = 1600,
) -> bytes:
    """Render one page as PNG with translucent highlight overlays.

    Stored rects live in the UNROTATED page coordinate space (that is what
    ``search_for``/``get_text`` return), while ``get_pixmap`` renders with the
    page's /Rotate applied — so every rect is mapped through
    ``page.rotation_matrix`` before scaling.
    """
    with doc_from_bytes(pdf_bytes) as doc:
        page = doc[page_index]
        zoom = min(3.0, max(1.0, target_width / max(1.0, page.rect.width)))
        rotation = page.rotation_matrix
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples).convert("RGBA")

        def to_display(rect):
            r = fitz.Rect(rect) * rotation
            r.normalize()
            return (r.x0, r.y0, r.x1, r.y1)

        value_rects = merge_rects([to_display(r) for r in value_rects])
        label_rects = merge_rects([to_display(r) for r in label_rects])
        context_rects = merge_rects([to_display(r) for r in context_rects])

    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    def scaled(rect, pad=1.5):
        x0 = min(max((rect[0] - pad) * zoom, 0), img.width)
        y0 = min(max((rect[1] - pad) * zoom, 0), img.height)
        x1 = min(max((rect[2] + pad) * zoom, 0), img.width)
        y1 = min(max((rect[3] + pad) * zoom, 0), img.height)
        if x1 - x0 < 1 or y1 - y0 < 1:
            return None
        return (x0, y0, x1, y1)

    for r in context_rects:
        if (box := scaled(r)) is not None:
            draw.rectangle(box, fill=_CONTEXT_FILL)
    for r in label_rects:
        if (box := scaled(r)) is not None:
            draw.rectangle(box, fill=_LABEL_FILL)
    for r in value_rects:
        if (box := scaled(r, pad=2.5)) is not None:
            draw.rectangle(box, fill=_VALUE_FILL,
                           outline=_VALUE_OUTLINE, width=max(2, int(zoom)))

    out = Image.alpha_composite(img, overlay).convert("RGB")
    buf = io.BytesIO()
    out.save(buf, format="PNG")
    return buf.getvalue()


def build_annotated_pdf(pdf_bytes: bytes, findings: list[Finding]) -> bytes:
    """Return a copy of the PDF with real highlight annotations per finding.

    ``add_highlight_annot`` interprets rects in the unrotated page space, so
    no rotation transform is needed here (unlike the PNG overlay path).
    """
    doc = doc_from_bytes(pdf_bytes)
    try:
        for f in findings:
            if not f.located or f.page is None:
                continue
            page = doc[f.page]
            for rect in f.value_rects:
                annot = page.add_highlight_annot(fitz.Rect(rect))
                annot.set_colors(stroke=(232 / 255, 26 / 255, 59 / 255))
                annot.set_info(title="PDF Metric Extractor",
                               content=f"{f.metric}: {f.value} {f.unit}".strip())
                annot.update()
            for rect in f.label_rects:
                annot = page.add_highlight_annot(fitz.Rect(rect))
                annot.set_colors(stroke=(91 / 255, 110 / 255, 127 / 255))
                annot.update()
        return doc.tobytes(deflate=True, garbage=3)
    finally:
        doc.close()
