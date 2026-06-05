"""Database connection setup for the application."""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_SESSION_URL = os.environ["DATABASE_SESSION_URL"]
if DATABASE_SESSION_URL is None:
    raise RuntimeError("DATABASE_SESSION_URL environment variable is not set")

engine = create_engine(DATABASE_SESSION_URL)
SessionLocal = sessionmaker(bind=engine)


def get_session():
    """Yield a database session for request-scoped work.

    Yields:
        Session: SQLAlchemy session bound to the application engine.
    """

    with SessionLocal() as session:
        yield session
