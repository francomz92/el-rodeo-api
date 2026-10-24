from __future__ import annotations

from typing import ClassVar, Protocol

from src.reports.application.dto.report_spec import ReportSpec


class IReportExporter(Protocol):
    """Exports a declarative report spec into a downloadable byte format.

    Implementations carry their transport metadata (``media_type`` and
    ``file_extension``) as class attributes so routers can build responses
    without knowing concrete formats.
    """

    media_type: ClassVar[str]
    file_extension: ClassVar[str]

    def export(self, spec: ReportSpec) -> bytes:
        """Render a declarative report specification as document bytes."""
        ...
