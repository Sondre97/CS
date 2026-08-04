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

`samples/make_demo_reports.py` writes 14 synthetic annual-report stand-ins for
three Norwegian investment companies — Ferd (2021–2025), Aker ASA (2021–2025)
and Sundt (2019–2022). They are **not** those companies' reports; every page
says so. What is real is the figures: each company's publicly reported
"verdijustert egenkapital", so uploading all 14 with
`Verdijustert egenkapital` as the metric produces true time series with
per-report evidence. For real work, run the app on the actual PDFs.

```bash
pip install reportlab                # only needed to build the demo files
python samples/make_demo_reports.py  # writes samples/out/*.pdf
```

The three report the same metric in deliberately different ways, which is
what the extraction has to survive:

| Company | How the figure is printed | The trap on the page |
|---|---|---|
| Ferd | `55,3 milliarder kroner` | prior-year column, segment rows |
| Aker ASA | `67 259 millioner kroner` | a per-share figure (`905 kroner`) right beside it, and a space that is a thousands separator rather than a column gap |
| Sundt | `steg … til 16,3 milliarder` | the opening figure of a "from X to Y" clause |

## Trusting the number

The failure that matters in a report like this is not "no value found" — it is
a *confidently wrong* value. "Verdijustert egenkapital" appears in the group
highlights, again for every business segment with a smaller figure, and once
more across a five-year note. Pick the wrong line and you get a segment's
share presented as the group total, with convincing highlighted evidence
underneath it.

So the app never shows a value alone:

* every place the metric is stated is listed, with page and context, and you
  can switch the evidence view to any of them — or adopt one as the answer;
* when the document states the metric with more than one value, it says so
  before you trust the number;
* ranking uses cross-document consensus, so the figure repeated in the
  highlights *and* the key-figures table beats a segment row that appears
  once.

## How it works

1. **Text extraction** — PyMuPDF reads every page twice: as text, and rebuilt
   row-by-row from word geometry. A key-figures row is often three separate
   text blocks ("Verdijustert egenkapital", "50,4", "45,8"), so without the
   second pass the standard table is invisible to a line-based search.
2. **Extraction** — the page-tagged text and your metric list go to a
   Databricks **Model Serving** endpoint (any chat-capable Foundation Model
   API endpoint, e.g. `databricks-claude-sonnet-4-5`). The model must return
   each value *verbatim* — exact digits and separators — plus the page, the
   document's own label for the metric, and a supporting quote.
3. **Localisation** — the verbatim value is pinned to coordinates by matching
   it against the page's word stream with separators normalised, so `1 234,5`
   is found however it is spaced or split across words. Digit boundaries are
   judged geometrically: `12` never pins inside `2012`, while `50,4    45,8`
   stays two columns rather than fusing into one number. (PyMuPDF's
   `search_for` is used for labels and quotes, but not for values — it
   happily matches a number inside a longer one.) When a value occurs several
   times on a page, the occurrence nearest the metric's label wins; a page
   carrying both value and label beats a page with the value alone; and if
   the model cited the wrong page, neighbours and then the whole document are
   searched.
4. **Evidence** — the page is rendered as an image with translucent overlays
   (red = value, slate = label, orange = quote context), and an annotated PDF
   copy is offered for download.

There is also an **offline heuristic engine** (best-ranked line naming the
metric, see `occurrences.py`) so the app works before any serving endpoint is
bound — useful for smoke-testing the deployment. Its results are flagged
`heuristic` and are markedly weaker than the LLM path; the occurrence list
above is how you check them.

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

`tests/test_pipeline.py` builds synthetic reports and exercises the pipeline
offline: extraction, localisation (NBSP-formatted numbers, label
disambiguation, wrong-page recovery, digit boundaries, rotated pages,
neighbouring table columns), the group-total-vs-segment ranking, highlight
rendering and PDF annotation.

`tests/test_app_state.py` drives the app itself through Streamlit's AppTest
harness: several reports at once, duplicate uploads, two reports sharing a
filename, an unreadable PDF among good ones, the table accumulating as
reports are added, and the language switch.

## Limitations

- **Scanned PDFs**: no OCR yet — the app warns when a document has little or
  no machine-readable text.
- One value per metric goes in the table, with the rest offered as
  alternatives you can inspect or adopt. If you want several of them as their
  own rows, ask for the metric per period, e.g. `Revenue Q2 2025` and
  `Revenue Q2 2024`.
- The consensus ranking assumes the headline figure is the one the report
  repeats. A report that states a segment figure more often than the group
  total would rank it first — the occurrence list is there for exactly that
  case.
- Very large documents are processed in ~60k-character chunks; results are
  merged with best-confidence-wins.
