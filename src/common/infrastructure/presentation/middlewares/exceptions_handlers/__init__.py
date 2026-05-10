from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from src.common.application.exceptions import ApplicationError
from src.common.domain.exceptions import DomainError

from .server_error import server_exception_handler
from .request_validation_error import _request_validation_exception_handler
from .application_errors import application_exception_handler
from .domain_errors import domain_exception_handler


def configure_exception_handlers(app: FastAPI):
    app.add_exception_handler(Exception, server_exception_handler)  # type: ignore
    app.add_exception_handler(RequestValidationError, _request_validation_exception_handler)  # type: ignore
    app.add_exception_handler(ApplicationError, application_exception_handler)  # type: ignore
    app.add_exception_handler(DomainError, domain_exception_handler)  # type: ignore
