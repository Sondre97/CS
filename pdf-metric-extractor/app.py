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
from occurrences import _norm_value
from pdf_utils import (
    build_annotated_pdf,
    extract_pages,
    extract_rows,
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


@st.cache_data(show_spinner=False, max_entries=64)
def cached_pages(pdf_bytes: bytes) -> list[str]:
    return extract_pages(pdf_bytes)


@st.cache_data(show_spinner=False, max_entries=64)
def cached_rows(pdf_bytes: bytes) -> list[str]:
    return extract_rows(pdf_bytes)


@st.cache_data(show_spinner=False, max_entries=64)
def cached_render(pdf_bytes: bytes, page_index: int, value_rects: tuple,
                  label_rects: tuple, context_rects: tuple) -> bytes:
    return render_page_with_highlights(
        pdf_bytes, page_index,
        [tuple(r) for r in value_rects],
        [tuple(r) for r in label_rects],
        [tuple(r) for r in context_rects],
    )


@st.cache_data(show_spinner=False, max_entries=64)
def cached_locate(pdf_bytes: bytes, metric: str, label: str, value: str,
                  page: int, quote: str, total_pages: int) -> Finding:
    """Pin one alternative occurrence to coordinates, for the evidence view."""
    return locate_finding(
        pdf_bytes,
        Finding(metric=metric, found=True, value=value, page=page,
                label=label, quote=quote),
        total_pages,
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


def _column_config(t: dict) -> dict:
    """Keep the identifying columns and the value itself readable when the
    table is narrow; long report filenames otherwise push Value out of view."""
    return {
        t["col_company"]: st.column_config.TextColumn(width="small"),
        t["col_report"]: st.column_config.TextColumn(width="medium"),
        t["col_year"]: st.column_config.TextColumn(width="small"),
        t["col_metric"]: st.column_config.TextColumn(width="medium"),
        t["col_value"]: st.column_config.TextColumn(width="small"),
    }


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


def _extract_one(fl: dict, metrics: list[str], engine: str,
                 endpoint: str) -> tuple[list[Finding], str]:
    """Extract one document. Returns (findings, failure) — `failure` is the
    endpoint error to report, empty when the chosen engine worked."""
    pages, rows = fl["pages"], fl["rows"]
    failure = ""
    if engine == "llm":
        try:
            return extract_with_llm(pages, metrics, endpoint=endpoint,
                                    row_texts=rows), ""
        except Exception as exc:  # endpoint missing / permissions / network
            failure = f"{type(exc).__name__}: {exc}"
    return extract_heuristic(pages, metrics, row_texts=rows), failure


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
    # Switching language translates the metric list only while it is still the
    # untouched default — anything typed is the user's and stays put.
    other = "no" if lang == "en" else "en"
    if st.session_state.get("metrics") == DEFAULT_METRICS[other]:
        st.session_state["metrics"] = DEFAULT_METRICS[lang]
    metrics_raw = st.text_area(
        t["metrics_label"], value=DEFAULT_METRICS[lang],
        height=140, help=t["metrics_help"], key="metrics",
    )
    metrics = [m.strip() for m in metrics_raw.splitlines() if m.strip()]
    if not metrics:
        st.warning(t["no_metrics_warning"])

    if not uploads:
        st.info(t["upload_first"])
        return

    # Per-file: bytes, readability, metadata (company/year, user-editable).
    # Widget keys are per upload SLOT, not per content hash: the same PDF can
    # legitimately be uploaded twice, and two identical hashes would collide
    # into one key and abort the script.
    files = []
    for slot, up in enumerate(uploads):
        pdf_bytes = up.getvalue()
        pdf_hash = hashlib.sha256(pdf_bytes).hexdigest()
        try:
            pages = cached_pages(pdf_bytes)
            rows = cached_rows(pdf_bytes)
        except Exception:
            st.error(f'{t["skipped_file"]} **{_md(up.name)}** — {t["pdf_error"]}')
            continue
        files.append({
            "name": up.name, "bytes": pdf_bytes, "hash": pdf_hash,
            "pages": pages, "rows": rows, "slot": slot,
            "uid": f"{pdf_hash[:12]}#{slot}",
        })
    if not files:
        return

    # Company/year survive a file being removed and re-added: Streamlit drops
    # widget state for widgets that stop being rendered, so the last value is
    # remembered per document.
    remembered = st.session_state.setdefault("meta_by_hash", {})

    with st.expander(t["meta_header"], expanded=False):
        st.caption(t["meta_help"])
        for fl in files:
            c1, c2, c3 = st.columns([4, 3, 2])
            c1.markdown(f"**{_md(fl['name'])}** · {len(fl['pages'])} {t['pages']}")
            prior = remembered.get(fl["hash"], {})
            fl["company"] = c2.text_input(
                t["company_label"],
                value=prior.get("company") or _guess_company(fl["name"]),
                key=f"company_{fl['uid']}",
            )
            fl["year"] = c3.text_input(
                t["year_label"],
                value=prior.get("year") or _guess_year(
                    fl["name"], fl["pages"][0] if fl["pages"] else ""),
                key=f"year_{fl['uid']}",
            )
            remembered[fl["hash"]] = {"company": fl["company"], "year": fl["year"]}

    thin = [fl for fl in files
            if sum(len(p.strip()) for p in fl["pages"]) < 25 * max(1, len(fl["pages"]))]
    if thin:
        st.warning(t["no_text_warning"] + " (" +
                   ", ".join(_md(fl["name"]) for fl in thin) + ")")

    # Results are kept per document, tagged with the settings that produced
    # them. Editing a metric therefore never blanks the table — the previous
    # results stay on screen, marked stale, until the next extraction. Adding
    # a report only processes the new file, so the table accumulates.
    store = st.session_state.setdefault("per_file_results", {})

    def result_key(fl):
        return hashlib.sha256(
            (fl["hash"] + repr((metrics, engine, endpoint, "v3"))).encode()
        ).hexdigest()

    if st.button(t["extract_button"], type="primary", disabled=not metrics):
        reported_failure = False
        for fl in files:
            key = result_key(fl)
            if store.get(fl["hash"], {}).get("key") == key:
                continue
            with st.spinner(f'{t["extracting"]} — {fl["name"]}'):
                findings, failure = _extract_one(fl, metrics, engine, endpoint)
            if failure and not reported_failure:
                # One endpoint is either reachable or not; saying so once per
                # upload would bury the table under identical errors.
                st.error(t["llm_error"])
                st.code(failure, language=None)
                reported_failure = True
            with st.spinner(t["locating"]):
                findings = [locate_finding(fl["bytes"], f, len(fl["pages"]))
                            for f in findings]
            store[fl["hash"]] = {"key": key, "findings": findings}
        # Bound session memory without ever dropping a document still uploaded.
        live = {fl["hash"] for fl in files}
        for key in [k for k in store if k not in live][:max(0, len(store) - 64)]:
            store.pop(key, None)

    rows = []
    pending = []
    for fl in files:
        entry = store.get(fl["hash"])
        if entry is None or entry["key"] != result_key(fl):
            pending.append(fl["name"])
        if entry is None:
            continue
        for f in entry["findings"]:
            rows.append({
                "company": fl["company"], "report": fl["name"],
                "year": fl["year"], "finding": f, "file": fl,
            })
    if not rows:
        return
    if pending:
        # Name them: "press the button" is unhelpful when the user cannot see
        # which of five reports is missing from the table.
        st.caption(t["stale_settings"].format(
            reports=", ".join(_md(n) for n in dict.fromkeys(pending))))

    st.subheader(t["results_header"])

    frame = _results_frame(rows, t)
    st.dataframe(frame, width="stretch", hide_index=True,
                 column_config=_column_config(t))
    st.download_button(
        t["download_csv"],
        data=frame.to_csv(index=False).encode("utf-8-sig"),
        file_name="metrics.csv", mime="text/csv",
        key="dl_csv",
    )

    st.divider()

    with st.container():
        st.markdown(f"#### {t['evidence_header']}")
        showable = [r for r in rows if r["finding"].found]
        if not showable:
            st.info(t["not_found"])
            return
        # Selection is by position, not by label: two uploads can share a
        # filename and metric, and matching on the label would always resolve
        # to the first of them.
        def row_label(i: int) -> str:
            r = showable[i]
            return t["evidence_pick_fmt"].format(
                report=r["report"], metric=r["finding"].metric)

        selected_row = st.selectbox(
            t["select_metric"], range(len(showable)),
            format_func=row_label, key="evidence_for",
        )
        selected_row = min(selected_row or 0, len(showable) - 1)
        chosen_row = showable[selected_row]
        chosen = chosen_row["finding"]
        chosen_file = chosen_row["file"]

        _finding_card(chosen, t, chosen_row["report"])

        # A metric is usually stated in several places — the group total, each
        # segment's share, a five-year history. Show them all so a segment
        # figure can never masquerade as the answer unnoticed.
        occurrences = [(chosen.page, chosen.value, chosen.quote)] + list(chosen.alternatives)
        radio_key = f"occ::{chosen_file['uid']}::{chosen.metric}"
        selected = 0
        if len(occurrences) > 1:
            distinct = len({_norm_value(v) for _, v, _ in occurrences})
            if distinct > 1:
                st.warning(t["ambiguity_warning"].format(n=distinct))

            def occ_label(i):
                page, value, line = occurrences[i]
                head = t["occurrence_fmt"].format(page=(page or 0) + 1, value=value)
                if i == 0:
                    head += f" · {t['occurrence_extracted']}"
                return f"{head} — {line[:70]}"

            with st.expander(t["occurrences_label"].format(n=len(occurrences)),
                             expanded=False):
                selected = st.radio(
                    t["occurrences_label"].format(n=len(occurrences)),
                    range(len(occurrences)), format_func=occ_label,
                    key=radio_key, label_visibility="collapsed",
                )

        view = chosen
        if selected != 0:
            page, value, line = occurrences[selected]
            view = cached_locate(
                chosen_file["bytes"], chosen.metric, chosen.label or chosen.metric,
                value, page, line, len(chosen_file["pages"]),
            )
            st.info(t["viewing_other"])
            if st.button(t["adopt_button"], key=f"adopt::{radio_key}"):
                chosen.value, chosen.page, chosen.quote = view.value, view.page, view.quote
                chosen.located = view.located
                chosen.value_rects = view.value_rects
                chosen.label_rects = view.label_rects
                chosen.context_rects = view.context_rects
                chosen.comment = t["adopted_note"]
                chosen.alternatives = [
                    o for o in occurrences
                    if not (o[0] == view.page and _norm_value(o[1]) == _norm_value(view.value))
                ]
                st.session_state.pop(radio_key, None)
                st.rerun()

        if not view.located:
            st.warning(t["found_not_located"])
            if view.quote:
                st.caption(f'{t["quote_caption"]}: “{_md(view.quote)}”')
            return

        st.markdown(
            f"""<div class="bdo-legend">{t['page_label']} {view.page + 1} —
<span class="swatch" style="background:#E81A3B55;border:2px solid #E81A3B"></span>{t['legend_value']}
<span class="swatch" style="background:#5B6E7F55"></span>{t['legend_label']}
<span class="swatch" style="background:#D6790040"></span>{t['legend_context']}</div>""",
            unsafe_allow_html=True,
        )
        png = cached_render(
            chosen_file["bytes"], view.page,
            tuple(map(tuple, view.value_rects)),
            tuple(map(tuple, view.label_rects)),
            tuple(map(tuple, view.context_rects)),
        )
        st.image(png, width="stretch")
        if view.quote:
            st.caption(f'{t["quote_caption"]}: “{_md(view.quote)}”')
        if view.comment:
            st.caption(f'{t["comment_caption"]}: {_md(view.comment)}')

        located_here = [
            r["finding"] for r in rows
            if r["file"]["uid"] == chosen_file["uid"] and r["finding"].located
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
