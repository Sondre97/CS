"""PDF Metric Extractor — Databricks App (Streamlit).

Upload a PDF (e.g. a quarterly report), list the metrics you need, and get
each value together with visual evidence: the exact spot in the PDF where the
value was read, highlighted on a rendering of the page, plus a downloadable
annotated copy of the PDF.
"""

import hashlib
import html

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


def _md(text: str) -> str:
    return (text or "").translate(_MD_ESCAPE)


@st.cache_data(show_spinner=False, max_entries=8)
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


@st.cache_data(show_spinner=False, max_entries=8)
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


def _status(f: Finding, t: dict) -> tuple[str, str]:
    """(text, badge-css-class) for a finding."""
    if f.found and f.located:
        return t["status_located"], "green"
    if f.found:
        return t["status_found"], "orange"
    return t["status_missing"], "slate"


def _results_frame(findings: list[Finding], t: dict) -> pd.DataFrame:
    rows = []
    for f in findings:
        rows.append({
            t["col_metric"]: f.metric,
            t["col_value"]: f.value if f.found else "",
            t["col_unit"]: f.unit,
            t["col_period"]: f.period,
            t["col_page"]: str(f.page + 1) if (f.found and f.page is not None) else "",
            t["col_confidence"]: f.confidence,
            t["col_status"]: _status(f, t)[0],
        })
    return pd.DataFrame(rows)


def _finding_card(f: Finding, t: dict) -> None:
    status_text, badge = _status(f, t)
    value = html.escape(f.value) if f.found else "—"
    unit = html.escape(f.unit)
    meta_bits = []
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

    uploaded = st.file_uploader(t["upload_label"], type=["pdf"], key="pdf")
    metrics_raw = st.text_area(
        t["metrics_label"], value=DEFAULT_METRICS[lang],
        height=140, help=t["metrics_help"], key="metrics",
    )
    metrics = [m.strip() for m in metrics_raw.splitlines() if m.strip()]

    if uploaded is None:
        st.info(t["upload_first"])
        return

    pdf_bytes = uploaded.getvalue()
    pdf_hash = hashlib.sha256(pdf_bytes).hexdigest()
    try:
        pages = cached_pages(pdf_bytes)
    except Exception:
        st.error(t["pdf_error"])
        return
    n_chars = sum(len(p.strip()) for p in pages)
    st.caption(f"**{_md(uploaded.name)}** · {len(pages)} {t['pages']}")
    if not pages or n_chars < 25 * len(pages):
        st.warning(t["no_text_warning"])

    run_key = hashlib.sha256(
        (pdf_hash + repr((metrics, engine, endpoint, "v1"))).encode()
    ).hexdigest()

    if st.button(t["extract_button"], type="primary", disabled=not metrics):
        with st.spinner(t["extracting"]):
            findings = None
            if engine == "llm":
                try:
                    findings = extract_with_llm(pages, metrics, endpoint=endpoint)
                except Exception as exc:  # endpoint missing / permissions / network
                    st.error(f'{t["llm_error"]}\n\n`{type(exc).__name__}: {_md(str(exc))}`')
            if findings is None:
                findings = extract_heuristic(pages, metrics)
        with st.spinner(t["locating"]):
            findings = [locate_finding(pdf_bytes, f, len(pages)) for f in findings]
        st.session_state["results"] = findings
        st.session_state["results_pdf_hash"] = pdf_hash
        st.session_state["results_run_key"] = run_key

    findings = st.session_state.get("results")
    if not findings:
        return
    # Results belong to the PDF they were extracted from. A new upload makes
    # them meaningless (pages/rects reference the old file) — drop them
    # instead of rendering false evidence or crashing on out-of-range pages.
    if st.session_state.get("results_pdf_hash") != pdf_hash:
        st.session_state.pop("results", None)
        return
    if st.session_state.get("results_run_key") != run_key:
        st.caption(t["stale_settings"])

    st.subheader(t["results_header"])
    left, right = st.columns([5, 7], gap="large")

    with left:
        for f in findings:
            _finding_card(f, t)

        frame = _results_frame(findings, t)
        st.download_button(
            t["download_csv"],
            data=frame.to_csv(index=False).encode("utf-8-sig"),
            file_name="metrics.csv", mime="text/csv",
            key="dl_csv",
        )
        located = [f for f in findings if f.located]
        if located:
            st.download_button(
                t["download_pdf"],
                data=cached_annotated_pdf(pdf_bytes, _annotation_signature(located)),
                file_name=uploaded.name.replace(".pdf", "") + "_annotated.pdf",
                mime="application/pdf",
                key="dl_pdf",
            )

    with right:
        st.markdown(f"#### {t['evidence_header']}")
        showable = [f for f in findings if f.found]
        if not showable:
            st.info(t["not_found"])
            return
        chosen_name = st.selectbox(t["select_metric"], [f.metric for f in showable],
                                   key="evidence_for")
        chosen = next((f for f in showable if f.metric == chosen_name), showable[0])

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
            pdf_bytes, chosen.page,
            tuple(map(tuple, chosen.value_rects)),
            tuple(map(tuple, chosen.label_rects)),
            tuple(map(tuple, chosen.context_rects)),
        )
        st.image(png, use_container_width=True)
        if chosen.quote:
            st.caption(f'{t["quote_caption"]}: “{_md(chosen.quote)}”')
        if chosen.comment:
            st.caption(f'{t["comment_caption"]}: {_md(chosen.comment)}')


main()
