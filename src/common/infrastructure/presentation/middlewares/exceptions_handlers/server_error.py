from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from src.common.utils import log


async def server_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    err = jsonable_encoder(exc)
    log.error(f"Server error:\n{err}\n")
    return JSONResponse(
        status_code=500,
        content={"detail": err},
    )
