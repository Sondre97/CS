"""Find every place a metric is stated in a document, and rank them.

Why this exists: in a real annual report a metric like "verdijustert
egenkapital" is stated many times with DIFFERENT numbers — the group figure in
the highlights and the key-figures table, a smaller figure for each business
segment, and the whole history in a five-year note. Returning one number
without saying that is how an extractor confidently hands back a segment
figure as the group total.

So every extraction is accompanied by the full candidate list. The UI shows
how many other places the metric appears and lets the user switch to any of
them; the offline heuristic engine picks its answer from the same ranking.

Ranking signals, in order of weight:
  * label match — how well the text before the number matches the metric name
    (a table row "Verdijustert egenkapital  50,4" beats prose that merely
    mentions the words)
  * consensus — how many other places in the document state the same value.
    Headline figures get repeated (highlights, board report, key figures,
    five-year table); a segment figure usually appears once. This is the
    signal that separates the group total from a segment's share.
  * position — earlier pages first, since primary statements precede notes.
"""

import re
import unicodedata
from dataclasses import dataclass

from rapidfuzz import fuzz

_NUMBER_RE = re.compile(
    r"[-−(]?\d(?:[\d.,]|[    ](?=\d))*\)?(?: ?%)?"
)

_DATE_LIKE_RE = re.compile(
    r"^\(?[-−]?(?:\d{1,2}[./-]\d{1,2}[./-]\d{2,4}|(?:19|20)\d{2})\)?$"
)

_STRIP = " \t\u00a0\u202f\u2009\u200a\u2007\u2008"


@dataclass
class Occurrence:
    """One place in the document where the metric appears with a number."""

    page: int          # 0-based physical page index
    value: str         # verbatim number token as printed
    line: str          # the whole line it was read from
    label_score: float # 0-100, how table-row-like the label match is
    score: float = 0.0 # final ranking score, filled in by rank()


def _norm_value(value: str) -> str:
    """Compare values ignoring separators, so '1 234,5' == '1234,5'."""
    v = unicodedata.normalize("NFKC", value)
    for ch in _STRIP:
        v = v.replace(ch, "")
    return v.strip("()").lstrip("-−")


def _numbers_on(line: str):
    """(position, verbatim token) for each number-ish substring."""
    out = []
    for m in _NUMBER_RE.finditer(line):
        token = m.group(0).strip().rstrip(".,")
        if any(c.isdigit() for c in token):
            out.append((m.start(), token))
    return out


# "rose from 45,8 to 50,4" / "økte fra 45,8 til 50,4" — the figure being
# reported is the one after the "to" word, not the first number in the clause.
_FROM_TO_RE = re.compile(
    r"\b(?:from|fra)\b.{0,40}?\b(?:to|til)\b",
    re.IGNORECASE | re.DOTALL,
)


def _pick_value(candidates, label_end: int, line: str = ""):
    """The most value-like token on a line: prefer numbers after the label,
    skip years/dates when there is anything else, and step past the opening
    figure of a "from X to Y" comparison."""
    after = [c for c in candidates if c[0] >= label_end]
    pool = after or candidates
    non_date = [c for c in pool if not _DATE_LIKE_RE.match(c[1])]
    pool = non_date or pool

    if line and len(pool) > 1:
        match = _FROM_TO_RE.search(line, label_end)
        if match:
            beyond = [c for c in pool if c[0] >= match.end()]
            if beyond:
                return beyond[0]
    return pool[0]


def find_occurrences(page_texts: list[str], metric: str,
                     min_score: int = 82,
                     row_texts: list[str] | None = None) -> list[Occurrence]:
    """Every line that names `metric` and carries a number, ranked best first.

    ``row_texts`` is the same document re-read row by row from word geometry
    (see :func:`pdf_utils.extract_rows`). Table rows whose cells are separate
    text blocks only appear there, so both sources are searched and the
    results deduplicated.
    """
    target = metric.casefold().strip()
    if not target:
        return []

    found: list[Occurrence] = []
    seen: set[tuple[int, str, str]] = set()
    for source in (page_texts, row_texts or []):
        for page_index, text in enumerate(source):
            for line in text.splitlines():
                stripped = line.strip()
                if len(stripped) < 2:
                    continue
                hay = stripped.casefold()
                match = fuzz.partial_ratio(target, hay)
                if match < min_score:
                    continue
                numbers = _numbers_on(stripped)
                if not numbers:
                    continue
                try:
                    label_end = fuzz.partial_ratio_alignment(target, hay).dest_end
                except Exception:
                    label_end = 0
                position, value = _pick_value(numbers, label_end, stripped)
                key = (page_index, _norm_value(value),
                       "".join(hay.split())[:80])
                if key in seen:
                    continue
                seen.add(key)
                prefix = stripped[:position].strip(" .:·-–—").casefold()
                found.append(Occurrence(
                    page=page_index,
                    value=value,
                    line=stripped[:200],
                    label_score=match + 0.5 * fuzz.ratio(target, prefix),
                ))
    return rank(found)


def rank(occurrences: list[Occurrence]) -> list[Occurrence]:
    """Order occurrences best-first; see the module docstring for signals."""
    counts: dict[str, int] = {}
    for occ in occurrences:
        counts[_norm_value(occ.value)] = counts.get(_norm_value(occ.value), 0) + 1

    for occ in occurrences:
        repeats = counts[_norm_value(occ.value)] - 1
        # Consensus is capped so a long five-year series cannot outweigh a
        # decisively better label match.
        occ.score = occ.label_score + 12.0 * min(repeats, 3) - 0.05 * occ.page
    return sorted(occurrences, key=lambda o: -o.score)


def distinct_values(occurrences: list[Occurrence]) -> list[str]:
    """Distinct values across occurrences, best-ranked first."""
    seen, out = set(), []
    for occ in occurrences:
        key = _norm_value(occ.value)
        if key not in seen:
            seen.add(key)
            out.append(occ.value)
    return out
