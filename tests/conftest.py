"""Shared fixtures for all tests."""
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Force-set test credentials BEFORE the app module is imported
# (admin.py reads these at module-import time as module-level vars)
os.environ["ADMIN_USERNAME"] = "testadmin"
os.environ["ADMIN_PASSWORD"] = "testpass"
os.environ["SECRET_KEY"] = "test-secret-key"

TEST_DB_URL = "sqlite:///./test_vpn.db"

from app.core.database import Base, get_db
from app.main import app
import app.api.admin as _admin_module

# Patch module-level vars in case the module was already imported
# with production values from the container's .env file
_admin_module.ADMIN_USERNAME = "testadmin"
_admin_module.ADMIN_PASSWORD = "testpass"

engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    """Create all tables once per session, drop after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("test_vpn.db"):
        os.remove("test_vpn.db")


@pytest.fixture()
def db():
    """Transactional DB session, rolled back after each test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db):
    """TestClient with overridden DB dependency."""
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    # follow_redirects=True is starlette's default; tests that need to inspect
    # redirect status codes pass follow_redirects=False per-request
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def auth_client(client):
    """TestClient already logged in as admin."""
    resp = client.post(
        "/login",
        data={"username": "testadmin", "password": "testpass"},
        follow_redirects=False,
    )
    assert resp.status_code == 302, f"Login failed: {resp.status_code} {resp.text[:200]}"
    return client
