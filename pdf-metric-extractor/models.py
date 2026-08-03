"""Shared data structures for the PDF metric extractor."""

from dataclasses import dataclass, field


@dataclass
class Finding:
    """One extracted metric and, once located, where it sits in the PDF.

    Rectangles are stored as plain ``(x0, y0, x1, y1)`` tuples in PDF point
    coordinates so the object survives Streamlit session-state pickling.
    ``page`` is a 0-based physical page index.
    """

    metric: str
    found: bool = False
    value: str = ""
    unit: str = ""
    period: str = ""
    page: int | None = None
    quote: str = ""
    label: str = ""
    confidence: str = ""
    comment: str = ""

    located: bool = False
    value_rects: list[tuple[float, float, float, float]] = field(default_factory=list)
    label_rects: list[tuple[float, float, float, float]] = field(default_factory=list)
    context_rects: list[tuple[float, float, float, float]] = field(default_factory=list)
