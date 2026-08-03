"""PDF Metric Extractor — Databricks App (Streamlit).

Upload one or more report PDFs (e.g. annual/quarterly reports), list the
metrics you need, and get every value collected into one table — company,
report, year, metric, value — where each row can be verified against visual
evidence: the exact spot in the source PDF, highlighted on a rendering of the
page, plus a downloadable annotated copy of each PDF.
"""

import hashlib
import html
import re

import pandas as pd
import streamlit as st

import bdo_theme
from llm_extractor import (
    DEFAULT_ENDPOINT,
    extract_heuristic,
    extract_with_llm,
)
from models import Finding
from pdf_utils import (
    build_annotated_pdf,
    extract_pages,
    locate_finding,
    render_page_with_highlights,
)
from ui_strings import DEFAULT_METRICS, STRINGS

st.set_page_config(
    page_title="PDF Metric Extractor",
    page_icon="📄",
    layout="wide",
)
bdo_theme.inject_theme()

# Model output and PDF text end up inside st.caption/markdown — escape
# CommonMark punctuation so "$" doesn't trigger LaTeX and nothing injects
# formatting. html.escape alone doesn't cover markdown.
_MD_ESCAPE = str.maketrans({c: "\\" + c for c in "\\`*_{}[]()#+-.!$~|<>"})

_YEAR_RE = re.compile(r"\b(?:19|20)\d{2}\b")


def _md(text: str) -> str:
    return (text or "").translate(_MD_ESCAPE)


@st.cache_data(show_spinner=False, max_entries=16)
def cached_pages(pdf_bytes: bytes) -> list[str]:
    return extract_pages(pdf_bytes)


@st.cache_data(show_spinner=False, max_entries=64)
def cached_render(pdf_bytes: bytes, page_index: int, value_rects: tuple,
                  label_rects: tuple, context_rects: tuple) -> bytes:
    return render_page_with_highlights(
        pdf_bytes, page_index,
        [tuple(r) for r in value_rects],
        [tuple(r) for r in label_rects],
        [tuple(r) for r in context_rects],
    )


@st.cache_data(show_spinner=False, max_entries=16)
def cached_annotated_pdf(pdf_bytes: bytes, findings_sig: tuple) -> bytes:
    findings = [
        Finding(metric=m, value=v, unit=u, found=True, located=True, page=p,
                value_rects=[tuple(r) for r in vr],
                label_rects=[tuple(r) for r in lr])
        for (m, v, u, p, vr, lr) in findings_sig
    ]
    return build_annotated_pdf(pdf_bytes, findings)


def _annotation_signature(findings: list[Finding]) -> tuple:
    return tuple(
        (f.metric, f.value, f.unit, f.page,
         tuple(map(tuple, f.value_rects)), tuple(map(tuple, f.label_rects)))
        for f in findings
    )


_REPORT_WORDS = re.compile(
    r"\b(?:[aå]rsrapport\w*|[aå]rsregnskap\w*|annual|quarterly|interim|report\w*"
    r"|rapport\w*|kvartal\w*|result\w*|regnskap\w*)\b",
    re.IGNORECASE,
)


def _guess_company(filename: str) -> str:
    stem = filename.rsplit(".", 1)[0]
    head = re.split(r"\d", stem, maxsplit=1)[0]
    head = re.sub(r"[-_.]+", " ", head)
    head = _REPORT_WORDS.sub("", head)
    head = re.sub(r"\s+", " ", head).strip(" -–—")
    return head or stem


def _guess_year(filename: str, first_page_text: str) -> str:
    m = _YEAR_RE.search(filename)
    if m:
        return m.group(0)
    m = _YEAR_RE.search(first_page_text[:2000])
    return m.group(0) if m else ""


def _status(f: Finding, t: dict) -> tuple[str, str]:
    """(text, badge-css-class) for a finding."""
    if f.found and f.located:
        return t["status_located"], "green"
    if f.found:
        return t["status_found"], "orange"
    return t["status_missing"], "slate"


def _results_frame(rows: list[dict], t: dict) -> pd.DataFrame:
    out = []
    for r in rows:
        f = r["finding"]
        out.append({
            t["col_company"]: r["company"],
            t["col_report"]: r["report"],
            t["col_year"]: r["year"],
            t["col_metric"]: f.metric,
            t["col_value"]: f.value if f.found else "",
            t["col_unit"]: f.unit,
            t["col_period"]: f.period,
            t["col_page"]: str(f.page + 1) if (f.found and f.page is not None) else "",
            t["col_confidence"]: f.confidence,
            t["col_status"]: _status(f, t)[0],
        })
    return pd.DataFrame(out)


def _finding_card(f: Finding, t: dict, report: str) -> None:
    status_text, badge = _status(f, t)
    value = html.escape(f.value) if f.found else "—"
    unit = html.escape(f.unit)
    meta_bits = [html.escape(report)]
    if f.period:
        meta_bits.append(f'{t["period"]}: {html.escape(f.period)}')
    if f.found and f.page is not None:
        meta_bits.append(f'{t["page_label"]} {f.page + 1}')
    if f.confidence:
        meta_bits.append(f'{t["confidence"]}: {html.escape(f.confidence)}')
    meta = " · ".join(meta_bits)
    st.markdown(
        f"""<div class="bdo-card">
<div class="metric-name">{html.escape(f.metric)}
<span class="bdo-badge {badge}">{status_text}</span></div>
<div class="metric-value">{value} <span style="font-size:0.9rem;font-weight:400">{unit}</span></div>
<div class="metric-meta">{meta}</div>
</div>""",
        unsafe_allow_html=True,
    )


def _extract_one(pages: list[str], metrics: list[str], engine: str,
                 endpoint: str, t: dict) -> list[Finding]:
    findings = None
    if engine == "llm":
        try:
            findings = extract_with_llm(pages, metrics, endpoint=endpoint)
        except Exception as exc:  # endpoint missing / permissions / network
            st.error(f'{t["llm_error"]}\n\n`{type(exc).__name__}: {_md(str(exc))}`')
    if findings is None:
        findings = extract_heuristic(pages, metrics)
    return findings


def main() -> None:
    with st.sidebar:
        lang = st.radio("Language / Språk", ["en", "no"], horizontal=True,
                        format_func=lambda x: {"en": "English", "no": "Norsk"}[x],
                        key="lang")
        t = STRINGS[lang]
        st.divider()
        st.subheader(t["settings"])
        engine = st.radio(
            t["engine"],
            ["llm", "heuristic"],
            format_func=lambda x: t["engine_llm"] if x == "llm" else t["engine_heuristic"],
            key="engine",
        )
        endpoint = st.text_input(
            t["endpoint_label"], value=DEFAULT_ENDPOINT,
            help=t["endpoint_help"], disabled=(engine != "llm"),
            key="endpoint",
        )

    bdo_theme.header(t["title"], t["subtitle"])

    uploads = st.file_uploader(t["upload_label"], type=["pdf"],
                               accept_multiple_files=True, key="pdfs")
    metrics_raw = st.text_area(
        t["metrics_label"], value=DEFAULT_METRICS[lang],
        height=140, help=t["metrics_help"], key="metrics",
    )
    metrics = [m.strip() for m in metrics_raw.splitlines() if m.strip()]

    if not uploads:
        st.info(t["upload_first"])
        return

    # Per-file: bytes, readability, metadata (company/year, user-editable).
    files = []
    for up in uploads:
        pdf_bytes = up.getvalue()
        pdf_hash = hashlib.sha256(pdf_bytes).hexdigest()
        try:
            pages = cached_pages(pdf_bytes)
        except Exception:
            st.error(f'{t["skipped_file"]} **{_md(up.name)}** — {t["pdf_error"]}')
            continue
        files.append({
            "name": up.name, "bytes": pdf_bytes, "hash": pdf_hash, "pages": pages,
        })
    if not files:
        return

    with st.expander(t["meta_header"], expanded=False):
        st.caption(t["meta_help"])
        for fl in files:
            c1, c2, c3 = st.columns([4, 3, 2])
            c1.markdown(f"**{_md(fl['name'])}** · {len(fl['pages'])} {t['pages']}")
            fl["company"] = c2.text_input(
                t["company_label"], value=_guess_company(fl["name"]),
                key=f"company_{fl['hash'][:16]}",
            )
            fl["year"] = c3.text_input(
                t["year_label"],
                value=_guess_year(fl["name"], fl["pages"][0] if fl["pages"] else ""),
                key=f"year_{fl['hash'][:16]}",
            )

    thin = [fl for fl in files
            if sum(len(p.strip()) for p in fl["pages"]) < 25 * max(1, len(fl["pages"]))]
    if thin:
        st.warning(t["no_text_warning"] + " (" +
                   ", ".join(_md(fl["name"]) for fl in thin) + ")")

    # Results are stored per (file, metrics, engine, endpoint) — adding another
    # report later reuses what is already extracted and only processes the new
    # file, so the table accumulates across runs.
    store = st.session_state.setdefault("per_file_results", {})

    def result_key(fl):
        return hashlib.sha256(
            (fl["hash"] + repr((metrics, engine, endpoint, "v2"))).encode()
        ).hexdigest()

    if st.button(t["extract_button"], type="primary", disabled=not metrics):
        for fl in files:
            key = result_key(fl)
            if key in store:
                continue
            with st.spinner(f'{t["extracting"]} — {fl["name"]}'):
                findings = _extract_one(fl["pages"], metrics, engine, endpoint, t)
            with st.spinner(t["locating"]):
                findings = [locate_finding(fl["bytes"], f, len(fl["pages"]))
                            for f in findings]
            store[key] = findings
        while len(store) > 64:  # bound session memory
            store.pop(next(iter(store)))

    rows = []
    missing = False
    for fl in files:
        findings = store.get(result_key(fl))
        if findings is None:
            missing = True
            continue
        for f in findings:
            rows.append({
                "company": fl["company"], "report": fl["name"],
                "year": fl["year"], "finding": f, "file": fl,
            })
    if not rows:
        return
    if missing:
        st.caption(t["stale_settings"])

    st.subheader(t["results_header"])
    left, right = st.columns([6, 6], gap="large")

    with left:
        frame = _results_frame(rows, t)
        st.dataframe(frame, use_container_width=True, hide_index=True)
        st.download_button(
            t["download_csv"],
            data=frame.to_csv(index=False).encode("utf-8-sig"),
            file_name="metrics.csv", mime="text/csv",
            key="dl_csv",
        )

    with right:
        st.markdown(f"#### {t['evidence_header']}")
        showable = [r for r in rows if r["finding"].found]
        if not showable:
            st.info(t["not_found"])
            return
        labels = [
            t["evidence_pick_fmt"].format(report=r["report"], metric=r["finding"].metric)
            for r in showable
        ]
        chosen_label = st.selectbox(t["select_metric"], labels, key="evidence_for")
        chosen_row = showable[labels.index(chosen_label)] if chosen_label in labels else showable[0]
        chosen = chosen_row["finding"]
        chosen_file = chosen_row["file"]

        _finding_card(chosen, t, chosen_row["report"])

        if not chosen.located:
            st.warning(t["found_not_located"])
            if chosen.quote:
                st.caption(f'{t["quote_caption"]}: “{_md(chosen.quote)}”')
            return

        st.markdown(
            f"""<div class="bdo-legend">{t['page_label']} {chosen.page + 1} —
<span class="swatch" style="background:#E81A3B55;border:2px solid #E81A3B"></span>{t['legend_value']}
<span class="swatch" style="background:#5B6E7F55"></span>{t['legend_label']}
<span class="swatch" style="background:#D6790040"></span>{t['legend_context']}</div>""",
            unsafe_allow_html=True,
        )
        png = cached_render(
            chosen_file["bytes"], chosen.page,
            tuple(map(tuple, chosen.value_rects)),
            tuple(map(tuple, chosen.label_rects)),
            tuple(map(tuple, chosen.context_rects)),
        )
        st.image(png, use_container_width=True)
        if chosen.quote:
            st.caption(f'{t["quote_caption"]}: “{_md(chosen.quote)}”')
        if chosen.comment:
            st.caption(f'{t["comment_caption"]}: {_md(chosen.comment)}')

        located_here = [
            r["finding"] for r in rows
            if r["file"] is chosen_file and r["finding"].located
        ]
        if located_here:
            st.download_button(
                t["download_pdf_one"],
                data=cached_annotated_pdf(
                    chosen_file["bytes"], _annotation_signature(located_here)),
                file_name=chosen_file["name"].replace(".pdf", "") + "_annotated.pdf",
                mime="application/pdf",
                key="dl_pdf",
            )


main()
