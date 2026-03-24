"""Tests for admin panel routes (requires auth)."""
import pytest


class TestAdminPanelAccess:
    def test_unauthenticated_redirects_to_login(self, client):
        # Use /admin/ (with trailing slash) to avoid the 307 slash-redirect
        resp = client.get("/admin/", follow_redirects=False)
        assert resp.status_code == 302
        assert "/login" in resp.headers["location"]

    def test_authenticated_returns_200(self, auth_client):
        resp = auth_client.get("/admin/")
        assert resp.status_code == 200
        assert b"text/html" in resp.headers["content-type"].encode()


class TestAddConfig:
    def test_add_config_redirects(self, auth_client):
        resp = auth_client.post(
            "/admin/add",
            data={"name": "Test Server", "raw_link": "vless://test#Test"},
            follow_redirects=False,
        )
        assert resp.status_code == 303
        assert resp.headers["location"] == "/admin"

    def test_add_config_appears_in_panel(self, auth_client):
        auth_client.post(
            "/admin/add",
            data={"name": "My Server", "raw_link": "vless://abc123#My Server"},
        )
        resp = auth_client.get("/admin/")
        assert b"My Server" in resp.content

    def test_add_config_unauthenticated_redirects(self, client):
        resp = client.post(
            "/admin/add",
            data={"name": "X", "raw_link": "vless://x"},
            follow_redirects=False,
        )
        assert resp.status_code == 302


class TestEditConfig:
    def test_edit_config_updates_name(self, auth_client):
        auth_client.post(
            "/admin/add",
            data={"name": "Old Name", "raw_link": "vless://edit-test#Old Name"},
        )
        # Get id from admin page
        resp = auth_client.get("/admin/")
        assert b"Old Name" in resp.content

    def test_edit_nonexistent_config_redirects(self, auth_client):
        resp = auth_client.post(
            "/admin/edit/99999",
            data={"name": "X", "raw_link": "vless://x"},
            follow_redirects=False,
        )
        assert resp.status_code == 303


class TestToggleConfig:
    def test_toggle_unauthenticated_redirects(self, client):
        resp = client.post("/admin/toggle/1", follow_redirects=False)
        assert resp.status_code == 302

    def test_toggle_nonexistent_config_redirects(self, auth_client):
        resp = auth_client.post("/admin/toggle/99999", follow_redirects=False)
        assert resp.status_code == 303


class TestDeleteConfig:
    def test_delete_config_removes_it(self, auth_client):
        auth_client.post(
            "/admin/add",
            data={"name": "To Delete", "raw_link": "vless://delete-me#To Delete"},
        )
        resp = auth_client.get("/admin/")
        assert b"To Delete" in resp.content

    def test_delete_unauthenticated_redirects(self, client):
        resp = client.post("/admin/delete/1", follow_redirects=False)
        assert resp.status_code == 302


class TestUpdateSettings:
    def test_update_settings_redirects(self, auth_client):
        resp = auth_client.post(
            "/admin/update-settings",
            data={"sub_name": "My VPN", "sub_description": "https://t.me/test"},
            follow_redirects=False,
        )
        assert resp.status_code == 303

    def test_updated_settings_visible_in_panel(self, auth_client):
        auth_client.post(
            "/admin/update-settings",
            data={"sub_name": "SuperVPN", "sub_description": "https://t.me/supervpn"},
        )
        resp = auth_client.get("/admin/")
        assert b"SuperVPN" in resp.content

    def test_update_settings_unauthenticated_redirects(self, client):
        resp = client.post(
            "/admin/update-settings",
            data={"sub_name": "X", "sub_description": "X"},
            follow_redirects=False,
        )
        assert resp.status_code == 302


class TestExternalSubs:
    def test_fetch_missing_url_returns_422(self, auth_client):
        resp = auth_client.post("/admin/external-subs/fetch", data={})
        assert resp.status_code == 422

    def test_delete_nonexistent_sub_redirects(self, auth_client):
        resp = auth_client.post(
            "/admin/external-subs/99999/delete", follow_redirects=False
        )
        assert resp.status_code == 303

    def test_fetch_unauthenticated_redirects(self, client):
        resp = client.post(
            "/admin/external-subs/fetch",
            data={"url": "https://example.com"},
            follow_redirects=False,
        )
        assert resp.status_code == 302

    def test_rename_nonexistent_config_redirects(self, auth_client):
        resp = auth_client.post(
            "/admin/external-configs/99999/rename",
            data={"name": "New Name"},
            follow_redirects=False,
        )
        assert resp.status_code == 303
