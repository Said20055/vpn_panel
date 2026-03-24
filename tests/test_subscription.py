"""Tests for GET /sub endpoint (Happ client subscription)."""
import base64
import pytest


class TestSubscriptionEndpoint:
    def test_returns_200(self, client):
        resp = client.get("/sub")
        assert resp.status_code == 200

    def test_content_type_is_text_plain(self, client):
        resp = client.get("/sub")
        assert "text/plain" in resp.headers["content-type"]

    def test_has_profile_title_header(self, client, auth_client):
        auth_client.post(
            "/admin/update-settings",
            data={"sub_name": "TestVPN", "sub_description": "https://t.me/x"},
        )
        resp = client.get("/sub")
        assert "profile-title" in resp.headers

    def test_has_support_url_header(self, client, auth_client):
        auth_client.post(
            "/admin/update-settings",
            data={"sub_name": "TestVPN", "sub_description": "https://t.me/x"},
        )
        resp = client.get("/sub")
        assert "support-url" in resp.headers

    def test_has_profile_update_interval_header(self, client):
        resp = client.get("/sub")
        assert resp.headers.get("profile-update-interval") == "12"

    def test_empty_subscription_returns_valid_base64(self, client):
        resp = client.get("/sub")
        # Should decode without error (empty or valid base64)
        body = resp.text.strip()
        if body:
            decoded = base64.b64decode(body + "==").decode("utf-8", errors="ignore")
            assert isinstance(decoded, str)

    def test_active_config_appears_in_subscription(self, auth_client, client):
        raw = "vless://abc123-def456@example.com:443#Test Server"
        auth_client.post(
            "/admin/add",
            data={"name": "Test Server", "raw_link": raw},
        )
        resp = client.get("/sub")
        body_decoded = base64.b64decode(resp.text.strip() + "==").decode("utf-8", errors="ignore")
        assert raw in body_decoded

    def test_inactive_config_excluded_from_subscription(self, auth_client, client, db):
        from app.repository.vpn_repository import config_repo
        raw = "vless://inactive@example.com:443#Inactive"
        cfg = config_repo.create(db, name="Inactive", raw_link=raw)
        config_repo.toggle_active(db, cfg.id)  # make inactive

        resp = client.get("/sub")
        body = resp.text.strip()
        if body:
            decoded = base64.b64decode(body + "==").decode("utf-8", errors="ignore")
            assert raw not in decoded

    def test_subscription_settings_title_in_header(self, db, client):
        # Update settings directly via the repository to avoid cross-request
        # session state complexity; the GET /sub shares the same db session
        from app.repository.vpn_repository import config_repo
        config_repo.update_settings(db, name="MyUniqueVPN", desc="")
        resp = client.get("/sub")
        # sub_name is ASCII-only so quote() returns it unchanged
        assert resp.headers.get("profile-title") == "MyUniqueVPN"
