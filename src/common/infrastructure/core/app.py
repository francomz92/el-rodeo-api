from src.common.infrastructure.presentation.middlewares import configure_middlewares
from src.common.infrastructure.presentation.middlewares.exceptions_handlers import configure_exception_handlers
from src.common.infrastructure.presentation.routers import configure_routers


def configure_app(app):
    configure_middlewares(app)
    configure_exception_handlers(app)
    configure_routers(app)
