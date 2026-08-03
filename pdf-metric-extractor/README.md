# PDF Metric Extractor — Databricks App

Upload one or more PDFs (typically quarterly/annual financial reports), list
the metrics you want, and the app collects every value into one table —
**company, report, year, metric, value** — where each row comes **with
proof**: the exact spot in the source PDF where the value was read,
highlighted on a rendering of the page. Company and year are guessed per file
(editable). You can also download each PDF with the highlights baked in as
real annotations, and the whole table as CSV.

Adding more reports later and re-running only processes the new files — the
table accumulates across runs.

## Try it

`samples/make_ferd_demo.py` generates five demo annual-report extracts
(Ferd, the Norwegian family office, 2021–2025) carrying Ferd's real published
"verdijustert egenkapital" figures. Upload all five, enter
`Verdijustert egenkapital` as the metric, and you get the full time series
with per-year evidence:

```bash
python samples/make_ferd_demo.py   # writes samples/out/*.pdf
```

## How it works

1. **Text extraction** — PyMuPDF reads every page (text + word-level
   coordinates).
2. **Extraction** — the page-tagged text and your metric list go to a
   Databricks **Model Serving** endpoint (any chat-capable Foundation Model
   API endpoint, e.g. `databricks-claude-sonnet-4-5`). The model must return
   each value *verbatim* — exact digits and separators — plus the page, the
   document's own label for the metric, and a supporting quote.
3. **Localisation** — the verbatim value is pinned to coordinates:
   `search_for` first, then a separator-normalised match against the page's
   word stream (handles `1 234,5` written with non-breaking/thin spaces, or
   split across words). When a value occurs several times on a page, the
   occurrence nearest the metric's label wins (same table row preferred). If
   the model cited the wrong page, neighbouring pages and then the whole
   document are searched.
4. **Evidence** — the page is rendered as an image with translucent overlays
   (red = value, slate = label, orange = quote context), and an annotated PDF
   copy is offered for download.

There is also an **offline heuristic engine** (fuzzy label match + first
number on the line) so the app works before any serving endpoint is bound —
useful for smoke-testing the deployment. Its results are flagged
`heuristic` and are markedly weaker than the LLM path.

## Deploy to Databricks Apps

```bash
# from this folder
databricks sync . /Workspace/Users/<you>/pdf-metric-extractor
databricks apps create pdf-metric-extractor   # first time only
databricks apps deploy pdf-metric-extractor \
  --source-code-path /Workspace/Users/<you>/pdf-metric-extractor
```

Or via the UI: **Compute → Apps → Create app → Custom**, then point the app
at this folder.

### Model Serving access

The app runs as a service principal, which needs **CAN QUERY** on the
serving endpoint you use. Recommended setup:

1. In the app's config, add a **Serving endpoint** resource with resource key
   `serving-endpoint` (pick e.g. `databricks-claude-sonnet-4-5`). Binding the
   resource grants the permission automatically.
2. Uncomment the `SERVING_ENDPOINT` block in `app.yaml` so the app picks the
   bound endpoint up from the environment.

Without a bound resource the app still starts: the endpoint name is editable
in the sidebar (permission must then be granted manually), and the offline
heuristic engine works with no endpoint at all.

## Run locally

```bash
pip install -r requirements.txt
# For the LLM engine: authenticate and expose the profile to the app.
# (`databricks auth login` stores a *named* profile — a bare WorkspaceClient()
# only picks it up via DATABRICKS_CONFIG_PROFILE or if the profile is DEFAULT.)
databricks auth login --host https://<your-workspace> --profile DEFAULT
streamlit run app.py
# ...or keep a named profile:
DATABRICKS_CONFIG_PROFILE=<profile-name> streamlit run app.py
```

## Tests

```bash
pip install pytest
pytest tests/ -v
```

The tests build a synthetic quarterly report and exercise the full pipeline
offline: extraction, localisation (including NBSP-formatted numbers, label
disambiguation and wrong-page recovery), highlight rendering and PDF
annotation.

## Limitations

- **Scanned PDFs**: no OCR yet — the app warns when a document has little or
  no machine-readable text.
- One value per metric is reported (the model is instructed to prefer the
  primary financial statements). If you need every occurrence, ask for the
  metric per period, e.g. `Revenue Q2 2025` and `Revenue Q2 2024`.
- Very large documents are processed in ~60k-character chunks; results are
  merged with best-confidence-wins.
