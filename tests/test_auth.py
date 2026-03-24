"""Tests for authentication routes: login / logout."""
import pytest


class TestLoginPage:
    def test_login_page_returns_html(self, client):
        resp = client.get("/login")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]

    def test_login_page_contains_form(self, client):
        resp = client.get("/login")
        assert b"<form" in resp.content

    def test_authenticated_user_redirected_from_login(self, auth_client):
        resp = auth_client.get("/login", follow_redirects=False)
        assert resp.status_code == 302
        assert resp.headers["location"] == "/admin"


class TestLogin:
    def test_correct_credentials_redirect_to_admin(self, client):
        resp = client.post(
            "/login",
            data={"username": "testadmin", "password": "testpass"},
            follow_redirects=False,
        )
        assert resp.status_code == 302
        assert "/admin" in resp.headers["location"]

    def test_wrong_password_returns_401(self, client):
        resp = client.post(
            "/login",
            data={"username": "testadmin", "password": "wrongpass"},
            follow_redirects=False,
        )
        assert resp.status_code == 401

    def test_wrong_username_returns_401(self, client):
        resp = client.post(
            "/login",
            data={"username": "baduser", "password": "testpass"},
            follow_redirects=False,
        )
        assert resp.status_code == 401

    def test_wrong_credentials_show_error_message(self, client):
        resp = client.post(
            "/login",
            data={"username": "bad", "password": "bad"},
        )
        assert b"\xd0\x9d\xd0\xb5\xd0\xb2\xd0\xb5\xd1\x80\xd0\xbd" in resp.content  # "Неверн"


class TestLogout:
    def test_logout_redirects_to_login(self, auth_client):
        resp = auth_client.get("/logout", follow_redirects=False)
        assert resp.status_code == 302
        assert "/login" in resp.headers["location"]

    def test_after_logout_admin_is_protected(self, auth_client):
        auth_client.get("/logout")
        resp = auth_client.get("/admin/", follow_redirects=False)
        assert resp.status_code == 302
        assert "/login" in resp.headers["location"]
