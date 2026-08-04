"""App-level tests: the multi-report state machine, driven through Streamlit's
own AppTest harness so widget identity and rerun semantics are exercised for
real rather than simulated.

Each test stubs only ``st.file_uploader`` — everything else is the app.
"""

import io
import sys
from pathlib import Path
from unittest.mock import patch

import pymupdf as fitz
import pytest
from streamlit.testing.v1 import AppTest

APP_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(APP_DIR))


class FakeUpload(io.BytesIO):
    """Stand-in for Streamlit's UploadedFile (only .name and .getvalue used)."""

    def __init__(self, data: bytes, name: str):
        super().__init__(data)
        self.name = name


def report_pdf(value: str, label: str = "Verdijustert egenkapital") -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 90), "Nøkkeltall konsern", fontsize=12)
    page.insert_text((72, 130), f"{label}                    {value}", fontsize=10)
    return doc.tobytes()


def run_app(uploads, metric="Verdijustert egenkapital", extract=True) -> AppTest:
    at = AppTest.from_file(str(APP_DIR / "app.py"), default_timeout=90)
    with patch("streamlit.file_uploader", return_value=uploads):
        at.run()
        assert not at.exception, at.exception
        at.text_area(key="metrics").set_value(metric).run()
        if extract:
            at.button[0].click().run()
    return at


def values_in_table(at: AppTest) -> list[str]:
    frame = at.dataframe[0].value
    return list(frame["Value"])


def test_same_pdf_uploaded_twice_does_not_crash():
    """Identical bytes in two upload slots must not collide on widget keys."""
    pdf = report_pdf("50,4")
    at = run_app([FakeUpload(pdf, "Ferd-2024.pdf"), FakeUpload(pdf, "Ferd-2024.pdf")])
    assert not at.exception, at.exception
    assert values_in_table(at) == ["50,4", "50,4"]


def test_two_reports_sharing_a_filename_stay_distinct():
    """Rows must follow the upload, not the (identical) filename."""
    at = run_app([FakeUpload(report_pdf("50,4"), "report.pdf"),
                  FakeUpload(report_pdf("45,8"), "report.pdf")])
    assert not at.exception, at.exception
    assert values_in_table(at) == ["50,4", "45,8"]


def test_table_accumulates_when_a_report_is_added():
    """Adding a report keeps the earlier results and extracts only the new one."""
    first = FakeUpload(report_pdf("50,4"), "Ferd-2024.pdf")
    at = AppTest.from_file(str(APP_DIR / "app.py"), default_timeout=90)
    with patch("streamlit.file_uploader", return_value=[first]):
        at.run()
        at.text_area(key="metrics").set_value("Verdijustert egenkapital").run()
        at.button[0].click().run()
        assert values_in_table(at) == ["50,4"]

    second = FakeUpload(report_pdf("45,8"), "Ferd-2023.pdf")
    with patch("streamlit.file_uploader", return_value=[first, second]):
        at.run()
        at.button[0].click().run()
    assert not at.exception, at.exception
    assert values_in_table(at) == ["50,4", "45,8"]


def test_unreadable_pdf_is_skipped_not_fatal():
    at = run_app([FakeUpload(b"not a pdf at all", "broken.pdf"),
                  FakeUpload(report_pdf("50,4"), "Ferd-2024.pdf")])
    assert not at.exception, at.exception
    assert values_in_table(at) == ["50,4"]
    assert any("broken" in e.value for e in at.error)


def test_language_switch_keeps_typed_metrics_and_results():
    uploads = [FakeUpload(report_pdf("50,4"), "Ferd-2024.pdf")]
    with patch("streamlit.file_uploader", return_value=uploads):
        at = AppTest.from_file(str(APP_DIR / "app.py"), default_timeout=90)
        at.run()
        at.text_area(key="metrics").set_value("Verdijustert egenkapital").run()
        at.button[0].click().run()
        assert values_in_table(at) == ["50,4"]

        at.radio(key="lang").set_value("no").run()
        assert not at.exception, at.exception
        # typed metrics survive, results survive, headers are now Norwegian
        assert at.text_area(key="metrics").value == "Verdijustert egenkapital"
        frame = at.dataframe[0].value
        assert list(frame["Verdi"]) == ["50,4"]
        assert "Selskap" in frame.columns


@pytest.mark.parametrize("n", [1, 3])
def test_evidence_panel_renders_an_image_per_report(n):
    uploads = [FakeUpload(report_pdf(f"5{i},4"), f"Ferd-202{i}.pdf") for i in range(n)]
    at = run_app(uploads)
    assert not at.exception, at.exception
    assert len(at.dataframe[0].value) == n
    # the evidence panel always renders exactly one highlighted page
    assert len(at.image) == 1


def test_editing_metrics_does_not_blank_the_results():
    """Typing in the metric box must not wipe the table: results stay on
    screen, flagged stale, until the next extraction."""
    uploads = [FakeUpload(report_pdf("50,4"), "Ferd-2024.pdf")]
    with patch("streamlit.file_uploader", return_value=uploads):
        at = AppTest.from_file(str(APP_DIR / "app.py"), default_timeout=90)
        at.run()
        at.text_area(key="metrics").set_value("Verdijustert egenkapital").run()
        at.button[0].click().run()
        assert values_in_table(at) == ["50,4"]

        at.text_area(key="metrics").set_value("Verdijustert egenkapital\nEBITDA").run()
        assert not at.exception, at.exception
        assert at.dataframe, "results vanished when the metric list was edited"
        assert values_in_table(at) == ["50,4"]
        # captions are markdown-escaped ("Ferd\\-2024\\.pdf"), so compare
        # against the text as it renders
        rendered = [c.value.replace("\\", "") for c in at.caption]
        assert any("Ferd-2024.pdf" in c for c in rendered), \
            f"stale caption should name the pending report, got {rendered}"


def test_language_switch_translates_untouched_default_metrics():
    uploads = [FakeUpload(report_pdf("50,4"), "Ferd-2024.pdf")]
    with patch("streamlit.file_uploader", return_value=uploads):
        at = AppTest.from_file(str(APP_DIR / "app.py"), default_timeout=90)
        at.run()
        assert "Revenue" in at.text_area(key="metrics").value
        at.radio(key="lang").set_value("no").run()
        assert not at.exception, at.exception
        assert "Driftsinntekter" in at.text_area(key="metrics").value


def test_endpoint_failure_reported_once_for_many_files():
    """A dead endpoint is one problem, not one problem per uploaded report."""
    uploads = [FakeUpload(report_pdf(f"5{i},4"), f"r{i}.pdf") for i in range(3)]
    with patch("streamlit.file_uploader", return_value=uploads):
        at = AppTest.from_file(str(APP_DIR / "app.py"), default_timeout=120)
        at.run()
        at.text_area(key="metrics").set_value("Verdijustert egenkapital").run()
        at.radio(key="engine").set_value("llm").run()
        at.button[0].click().run()
    assert not at.exception, at.exception
    assert len(at.error) == 1, f"{len(at.error)} error blocks for one bad endpoint"
    # it still falls back, so the user gets values rather than nothing
    assert values_in_table(at) == ["50,4", "51,4", "52,4"]
