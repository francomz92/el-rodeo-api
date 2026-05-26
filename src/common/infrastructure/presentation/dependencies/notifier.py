from typing import Annotated

from fastapi import Depends

from src.common.infrastructure.adapters.workers.email_workers import EmailNotifier

GetNotifierClient = Annotated[EmailNotifier, Depends()]
