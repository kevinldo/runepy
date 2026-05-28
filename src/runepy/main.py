"""Application entrypoint.

This module creates the FastAPI app, registers API routes, and holds app-level
configuration such as metadata or startup/shutdown hooks. Run the service by
pointing Uvicorn at `runepy.main:app`.
"""

from fastapi import FastAPI

from runepy.api.routes import router

app = FastAPI()

app.include_router(router)
