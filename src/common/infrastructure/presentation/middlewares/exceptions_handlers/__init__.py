from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from src.common.application.exceptions import ApplicationError

from .server_error import server_exception_handler
from .request_validation_error import _request_validation_exception_handler
from .business_errors import business_exception_handler


def configure_exception_handlers(app: FastAPI):
    app.add_exception_handler(Exception, server_exception_handler)  # type: ignore
    app.add_exception_handler(RequestValidationError, _request_validation_exception_handler)  # type: ignore
    app.add_exception_handler(ApplicationError, business_exception_handler)  # type: ignore
