"""Database connection setup for the application.

This module is responsible for creating and configuring the SQLAlchemy engine
and database sessions used by the rest of the app. Other modules should import
session helpers from here instead of creating their own database connections.
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_SESSION_URL = os.environ["DATABASE_SESSION_URL"]
if DATABASE_SESSION_URL is None:
    raise RuntimeError("DATABASE_SESSION_URL environment variable is not set")

engine = create_engine(DATABASE_SESSION_URL)
SessionLocal = sessionmaker(bind=engine)


def get_session():
    with SessionLocal() as session:
        yield session
