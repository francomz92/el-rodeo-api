"""Declarative report layout specification.

Reports describe *what* to render as plain data; exporters decide *how*
to paint bytes (PDF, XLSX, ...). Values arrive pre-formatted as strings so
every exporter produces identical text across formats.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TableSection:
    """A titled data table with a fixed header row and formatted rows."""

    title: str
    headers: list[str]
    rows: list[list[str]]
    empty_message: str = "No hay datos para el período seleccionado."


@dataclass(frozen=True)
class TotalsSection:
    """A titled two-column totals table (label, value)."""

    title: str
    rows: list[list[str]]


@dataclass(frozen=True)
class ReportSpec:
    """Full document layout: title, optional period line, ordered sections."""

    title: str
    period_text: str | None
    sections: list[TableSection | TotalsSection]
