from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware


def configure_compression_body(app: FastAPI):
    app.add_middleware(GZipMiddleware, minimum_size=500)
