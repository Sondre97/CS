"""BDO Norge web tokens ("Fargeblokk" direction) injected into Streamlit.

Palette per official brand sheet: primary red #E81A3B, text #333333, slate
#5B6E7F, burgundy #98002E, orange #D67900, green #009966, blue #008FD2,
links #0062B8, light surface #F2F2F2. Radius 16, soft shadows. Web typography
is Proxima Nova with Segoe UI/system fallback (no external font loading).
"""

import streamlit as st

TOKENS = {
    "red": "#E81A3B",
    "text": "#333333",
    "slate": "#5B6E7F",
    "burgundy": "#98002E",
    "orange": "#D67900",
    "green": "#009966",
    "blue": "#008FD2",
    "link": "#0062B8",
    "surface": "#F2F2F2",
}

_CSS = f"""
<style>
html, body, [data-testid="stAppViewContainer"] * {{
    font-family: "Proxima Nova", "Segoe UI", system-ui, Arial, sans-serif;
}}
/* Streamlit draws icons as ligatures in a Material Symbols font — the rule
   above would otherwise render them as the literal words "upload",
   "arrow_right", "close" wherever an icon should be. */
[data-testid="stIconMaterial"],
span[class*="material-symbols"],
.material-symbols-rounded,
.material-symbols-outlined {{
    font-family: "Material Symbols Rounded", "Material Symbols Outlined",
                 "Material Icons" !important;
}}
[data-testid="stAppViewContainer"] {{ color: {TOKENS["text"]}; }}

.bdo-header {{
    background: linear-gradient(120deg, {TOKENS["red"]} 0%, {TOKENS["burgundy"]} 100%);
    color: #ffffff;
    border-radius: 16px;
    padding: 1.6rem 2rem 1.4rem 2rem;
    margin-bottom: 1.2rem;
    box-shadow: 0 8px 24px rgba(51, 51, 51, 0.14);
}}
.bdo-header h1 {{
    color: #ffffff; font-size: 1.7rem; font-weight: 700;
    margin: 0 0 0.25rem 0; padding: 0;
}}
.bdo-header p {{ color: #ffe3e8; margin: 0; font-size: 0.95rem; }}

.bdo-card {{
    background: #ffffff;
    border: 1px solid #ececec;
    border-radius: 16px;
    padding: 0.9rem 1.1rem;
    margin-bottom: 0.7rem;
    box-shadow: 0 4px 14px rgba(51, 51, 51, 0.07);
}}
.bdo-card .metric-name {{
    color: {TOKENS["slate"]}; font-size: 0.8rem; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 0.15rem;
}}
.bdo-card .metric-value {{
    color: {TOKENS["text"]}; font-size: 1.45rem; font-weight: 700;
}}
.bdo-card .metric-meta {{ color: {TOKENS["slate"]}; font-size: 0.82rem; }}

.bdo-badge {{
    display: inline-block; border-radius: 999px; padding: 0.12rem 0.6rem;
    font-size: 0.72rem; font-weight: 600; color: #ffffff;
    vertical-align: middle; margin-left: 0.4rem;
}}
.bdo-badge.green {{ background: {TOKENS["green"]}; }}
.bdo-badge.slate {{ background: {TOKENS["slate"]}; }}
.bdo-badge.orange {{ background: {TOKENS["orange"]}; }}
.bdo-badge.red {{ background: {TOKENS["red"]}; }}

.bdo-legend {{ color: {TOKENS["slate"]}; font-size: 0.82rem; margin: 0.3rem 0 0.6rem 0; }}
.bdo-legend .swatch {{
    display: inline-block; width: 0.8rem; height: 0.8rem; border-radius: 4px;
    vertical-align: -0.1rem; margin: 0 0.3rem 0 0.8rem;
}}
a {{ color: {TOKENS["link"]}; }}
</style>
"""


def inject_theme() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


def header(title: str, subtitle: str) -> None:
    st.markdown(
        f'<div class="bdo-header"><h1>{title}</h1><p>{subtitle}</p></div>',
        unsafe_allow_html=True,
    )
