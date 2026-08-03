"""Metric extraction engines.

Two modes:

* ``extract_with_llm`` — queries a Databricks Model Serving endpoint (Claude or
  any chat-capable Foundation Model API endpoint) through the workspace's
  OpenAI-compatible API. Auth comes from the app's service principal via
  ``databricks-sdk`` (env vars are injected automatically inside Databricks
  Apps; a local ``databricks auth login`` profile works for development).
* ``extract_heuristic`` — fully offline fallback: fuzzy label matching per
  line + the most value-like number on that line. Lower quality, but keeps the
  app usable before a serving endpoint has been bound, and makes the pipeline
  testable.

Both return :class:`models.Finding` with a verbatim ``value`` string so that
``pdf_utils.locate_finding`` can pin it to exact coordinates afterwards.
"""

import dataclasses
import json
import os
import re

from rapidfuzz import fuzz

from models import Finding

DEFAULT_ENDPOINT = os.getenv("SERVING_ENDPOINT", "databricks-claude-sonnet-4-5")

# Roughly 15-20k tokens per chunk — safe for every FMAPI chat model.
CHUNK_CHARS = 60_000

_CONFIDENCE_RANK = {"high": 3, "medium": 2, "low": 1, "heuristic": 0, "": 0}

_SYSTEM_PROMPT = """\
You are a meticulous financial-report analyst. You extract requested metrics
from document text and always answer with a single JSON object — no prose, no
markdown fences.

Rules:
1. "value" must be copied VERBATIM from the document: identical digits,
   decimal/thousand separators and sign, exactly as printed. Never reformat,
   never compute. This string is used to locate the number in the PDF.
2. "quote" is a verbatim snippet (max 200 characters) surrounding the value —
   the table row or sentence it appears in.
3. "page" is the integer N from the "=== PAGE N ===" marker the value
   appears under.
4. "label_in_document" is the exact wording the document uses for the metric
   (e.g. "Driftsinntekter" when asked for "Revenue").
5. If a metric appears in several places, prefer the primary financial
   statements or the highlights table over running text.
6. If a metric is not present in the supplied text, return found=false for it
   and leave the other fields empty.
7. Report the value for the most recent period unless the metric name says
   otherwise; state the period you picked in "period".

Answer with exactly this shape:
{"results": [{"metric": "...", "found": true, "value": "...", "unit": "...",
"period": "...", "page": 1, "quote": "...", "label_in_document": "...",
"confidence": "high|medium|low", "comment": ""}]}
"""


def build_document_text(page_texts: list[str]) -> str:
    """Concatenate page texts with 1-based physical page markers."""
    parts = []
    for i, text in enumerate(page_texts):
        parts.append(f"=== PAGE {i + 1} ===\n{text.strip()}\n")
    return "\n".join(parts)


def chunk_pages(page_texts: list[str], chunk_chars: int = CHUNK_CHARS):
    """Split pages into contiguous chunks of at most ~chunk_chars characters.

    Yields (first_page_index, page_texts_slice). A single oversized page gets
    truncated rather than dropped.
    """
    start = 0
    while start < len(page_texts):
        size = 0
        end = start
        while end < len(page_texts) and (size == 0 or size + len(page_texts[end]) <= chunk_chars):
            size += len(page_texts[end])
            end += 1
        chunk = [t[:chunk_chars] for t in page_texts[start:end]]
        yield start, chunk
        start = end


def _extract_json(text: str) -> dict:
    """Parse the first JSON object found in a model response."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Fall back to the outermost brace pair.
    depth = 0
    start = None
    for i, ch in enumerate(text):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start is not None:
                return json.loads(text[start:i + 1])
    raise ValueError("No JSON object found in model response")


def get_openai_client():
    """OpenAI-compatible client for this workspace's serving endpoints."""
    from databricks.sdk import WorkspaceClient

    return WorkspaceClient().serving_endpoints.get_open_ai_client()


def _query_chunk(client, endpoint: str, metrics: list[str],
                 first_page: int, chunk: list[str]) -> list[Finding]:
    doc_text = "\n".join(
        f"=== PAGE {first_page + i + 1} ===\n{t.strip()}\n" for i, t in enumerate(chunk)
    )
    metric_list = "\n".join(f"- {m}" for m in metrics)
    user_prompt = (
        f"Extract the following metrics:\n{metric_list}\n\n"
        f"Document text (with physical page markers):\n\n{doc_text}"
    )

    response = client.chat.completions.create(
        model=endpoint,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.0,
        max_tokens=4000,
    )
    payload = _extract_json(response.choices[0].message.content)

    findings = []
    for item in payload.get("results", []):
        page_raw = item.get("page")
        try:
            page = int(page_raw) - 1 if page_raw is not None else None
        except (TypeError, ValueError):
            page = None
        findings.append(Finding(
            metric=str(item.get("metric", "")).strip(),
            found=bool(item.get("found")),
            value=str(item.get("value", "") or "").strip(),
            unit=str(item.get("unit", "") or "").strip(),
            period=str(item.get("period", "") or "").strip(),
            page=page,
            quote=str(item.get("quote", "") or "").strip(),
            label=str(item.get("label_in_document", "") or "").strip(),
            confidence=str(item.get("confidence", "") or "").strip().lower(),
            comment=str(item.get("comment", "") or "").strip(),
        ))
    return findings


def _merge(metrics: list[str], per_chunk: list[list[Finding]]) -> list[Finding]:
    """One finding per requested metric: best confidence wins, earliest page
    breaks ties (primary statements usually precede notes)."""
    best: dict[str, Finding] = {}
    for findings in per_chunk:
        for f in findings:
            key = f.metric.casefold()
            current = best.get(key)
            if current is None:
                best[key] = f
                continue
            if not current.found and f.found:
                best[key] = f
            elif current.found and f.found:
                if _CONFIDENCE_RANK.get(f.confidence, 0) > _CONFIDENCE_RANK.get(current.confidence, 0):
                    best[key] = f

    # Exact-name matches claim their finding first; the remaining metrics get
    # the best-ratio unclaimed candidate (the model may have echoed slightly
    # different names). Each candidate serves at most one metric, and results
    # are copies — never aliased, never mutated in place.
    claimed = {m.casefold() for m in metrics if m.casefold() in best}
    results = []
    for metric in metrics:
        key = metric.casefold()
        f = best.get(key)
        if f is None:
            scored = sorted(
                ((fuzz.ratio(key, k), k) for k in best if k not in claimed),
                reverse=True,
            )
            if scored and scored[0][0] >= 85:
                claimed.add(scored[0][1])
                f = best[scored[0][1]]
        if f is None:
            f = Finding(metric=metric, found=False)
        results.append(dataclasses.replace(f, metric=metric))
    return results


def extract_with_llm(page_texts: list[str], metrics: list[str],
                     endpoint: str = "", client=None) -> list[Finding]:
    """Extract `metrics` from the document via a serving endpoint.

    Raises on connectivity/permission errors so the UI can surface them; a
    metric missing from the document is reported as found=False, not an error.
    """
    endpoint = endpoint or DEFAULT_ENDPOINT
    if client is None:
        client = get_openai_client()

    per_chunk = [
        _query_chunk(client, endpoint, metrics, first_page, chunk)
        for first_page, chunk in chunk_pages(page_texts)
    ]
    return _merge(metrics, per_chunk)


# --- Offline heuristic fallback ---------------------------------------------

# A number token: optional sign/parenthesis, digits, with separators that must
# each be followed IMMEDIATELY by a digit — a single space/NBSP/thin space is a
# thousands separator, two spaces is a column gap, so adjacent table columns
# never fuse into one value.
_NUMBER_RE = re.compile(
    "[-\u2212(]?\\d(?:[\\d.,]|[ \u00a0\u202f\u2009](?=\\d))*\\)?(?: ?%)?"
)

# Years and dates are rarely the metric value the user asked for.
_DATE_LIKE_RE = re.compile(
    "^\\(?[-\u2212]?(?:\\d{1,2}[./-]\\d{1,2}[./-]\\d{2,4}|(?:19|20)\\d{2})\\)?$"
)


def _line_number_candidates(line: str):
    """(position, verbatim token) for each number-ish substring on a line."""
    out = []
    for m in _NUMBER_RE.finditer(line):
        token = m.group(0).strip().rstrip(".,")
        if any(c.isdigit() for c in token):
            out.append((m.start(), token))
    return out


def _pick_value(candidates, label_end: int):
    """Choose the most value-like token: prefer numbers positioned after the
    matched label, and skip year/date tokens when anything else exists."""
    after = [c for c in candidates if c[0] >= label_end]
    pool = after or candidates
    non_date = [c for c in pool if not _DATE_LIKE_RE.match(c[1])]
    return (non_date or pool)[0][1]


def extract_heuristic(page_texts: list[str], metrics: list[str],
                      min_score: int = 82) -> list[Finding]:
    """Fuzzy line search: best-scoring line containing the metric label and at
    least one number. Quality is below the LLM path — results are flagged with
    confidence='heuristic'."""
    results = []
    for metric in metrics:
        target = metric.casefold()
        best = None  # (score, page_index, line, value)
        for page_index, text in enumerate(page_texts):
            for line in text.splitlines():
                stripped = line.strip()
                if len(stripped) < 2:
                    continue
                hay = stripped.casefold()
                score = fuzz.partial_ratio(target, hay)
                if score < min_score:
                    continue
                candidates = _line_number_candidates(stripped)
                if not candidates:
                    continue
                first_num = candidates[0][0]
                # Table rows ("Revenue  1 234,5") beat prose ("Revenue growth
                # of 12 % ..."): reward lines whose text before the first
                # number is essentially just the label, and earlier pages
                # (primary statements come first).
                prefix = stripped[:first_num].strip(" .:\u00b7-\u2013\u2014").casefold()
                prefix_score = fuzz.ratio(target, prefix)
                try:
                    label_end = fuzz.partial_ratio_alignment(target, hay).dest_end
                except Exception:
                    label_end = 0
                ranked = (score + 0.5 * prefix_score, -page_index)
                if best is None or ranked > best[0]:
                    best = (ranked, page_index, stripped,
                            _pick_value(candidates, label_end))

        if best is None:
            results.append(Finding(metric=metric, found=False,
                                   confidence="heuristic",
                                   comment="No matching line with a number found."))
        else:
            _, page_index, line, value = best
            results.append(Finding(
                metric=metric, found=True, value=value, page=page_index,
                quote=line[:200], label=metric, confidence="heuristic",
                comment="Heuristic match \u2014 verify against the highlight.",
            ))
    return results
