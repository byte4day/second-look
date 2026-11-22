import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ["DEMO_MODE"] = "true"
os.environ["JWT_SECRET"] = "test-secret-key-32chars-minimum!!"
os.environ["DATABASE_URL"] = "sqlite://"

from app.db import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def auth_headers(client, db_session):
    from app.services import auth_service

    auth_service.request_code(db_session, "user@example.com")
    from sqlalchemy import select

    from app.models.entities import AuthCode

    code = db_session.scalar(select(AuthCode.code).where(AuthCode.email == "user@example.com"))
    r = client.post("/api/auth/verify-code", json={"email": "user@example.com", "code": code})
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}