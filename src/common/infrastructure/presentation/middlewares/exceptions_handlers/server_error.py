from fastapi import Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from src.common.infrastructure.presentation.exceptions import exceptions_list
from src.common.utils import log


async def server_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    status_code = exceptions_list.get(type(exc), None)
    if not status_code:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    error = jsonable_encoder(exc)
    log.error(f"Server error:\n{error}\n")
    return JSONResponse(
        status_code=status_code,
        content={"detail": error},
    )
