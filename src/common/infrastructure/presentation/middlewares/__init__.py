from fastapi import FastAPI

from .cors import configure_cors
from .trusted_host import configure_trusted_host
from .compresion import configure_compression_body


def configure_middlewares(app: FastAPI):
    configure_cors(app)
    configure_trusted_host(app)
    configure_compression_body(app)
