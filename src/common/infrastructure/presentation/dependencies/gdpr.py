"""Dependency injection wiring for GDPR services."""

from typing import Annotated

from fastapi import Depends

from src.common.application.services.gdpr_delete_service import GDPRDeleteService
from src.common.application.services.gdpr_export_service import GDPRExportService

from .db import GetSession


def _get_gdpr_export_service(session: GetSession) -> GDPRExportService:  # type: ignore[reportInvalidTypeForm]
    return GDPRExportService(db=session)


def _get_gdpr_delete_service(session: GetSession) -> GDPRDeleteService:  # type: ignore[reportInvalidTypeForm]
    return GDPRDeleteService(db=session)


GetGDPRExportService = Annotated[
    GDPRExportService,
    Depends(_get_gdpr_export_service),
]

GetGDPRDeleteService = Annotated[
    GDPRDeleteService,
    Depends(_get_gdpr_delete_service),
]
