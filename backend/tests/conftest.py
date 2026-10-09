import os
from collections.abc import Iterator

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import Connection, Engine, create_engine, text
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.passwords import PasswordService
from app.main import create_app

TABLE_NAMES = text(
    "SELECT string_agg(quote_ident(tablename), ', ') FROM pg_tables"
    " WHERE schemaname = 'public' AND tablename <> 'alembic_version'"
)


class TestDatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    TEST_DATABASE_URL: str


@pytest.fixture(scope="session")
def database_url() -> str:
    return TestDatabaseSettings().TEST_DATABASE_URL


@pytest.fixture(scope="session")
def engine(database_url: str) -> Iterator[Engine]:
    engine = create_engine(database_url)
    with engine.begin() as connection:
        connection.execute(text("DROP SCHEMA public CASCADE"))
        connection.execute(text("CREATE SCHEMA public"))
    previous = os.environ.get("MIGRATION_DATABASE_URL")
    os.environ["MIGRATION_DATABASE_URL"] = database_url
    try:
        command.upgrade(Config("alembic.ini"), "head")
    finally:
        if previous is None:
            del os.environ["MIGRATION_DATABASE_URL"]
        else:
            os.environ["MIGRATION_DATABASE_URL"] = previous
    yield engine
    engine.dispose()


@pytest.fixture(autouse=True)
def clean_database(engine: Engine) -> None:
    with engine.begin() as connection:
        tables = connection.scalar(TABLE_NAMES)
        connection.execute(text(f"TRUNCATE {tables} CASCADE"))


@pytest.fixture
def connection(engine: Engine) -> Iterator[Connection]:
    with engine.connect() as connection:
        yield connection


@pytest.fixture
def session(engine: Engine) -> Iterator[Session]:
    with Session(engine) as session:
        yield session


@pytest.fixture(scope="session")
def passwords() -> PasswordService:
    return PasswordService(4)


@pytest.fixture
def settings(database_url: str) -> Settings:
    return Settings(APP_ENV="test", DATABASE_URL=database_url)


@pytest.fixture
def app(settings: Settings, engine: Engine):
    return create_app(settings)


@pytest.fixture
def client(app) -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client
