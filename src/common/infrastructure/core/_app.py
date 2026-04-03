from src.common.infrastructure.presentation.middlewares.exceptions_handlers import configure_exception_handlers
from src.common.infrastructure.presentation.middlewares import configure_middlewares


def configure_app(app):
    configure_middlewares(app)
    configure_exception_handlers(app)
