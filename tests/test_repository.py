"""Tests for repository layer (ConfigRepository, ExternalSubscriptionRepository)."""
import pytest
from app.repository.vpn_repository import config_repo
from app.repository.external_vpn_repository import ext_sub_repo


class TestConfigRepository:
    def test_create_manual_config(self, db):
        cfg = config_repo.create(db, name="Server A", raw_link="vless://a#Server A")
        assert cfg.id is not None
        assert cfg.name == "Server A"
        assert cfg.subscription_id is None
        assert cfg.is_active is True

    def test_get_by_id_returns_config(self, db):
        cfg = config_repo.create(db, name="Server B", raw_link="vless://b#B")
        found = config_repo.get_by_id(db, cfg.id)
        assert found is not None
        assert found.name == "Server B"

    def test_get_by_id_returns_none_for_missing(self, db):
        assert config_repo.get_by_id(db, 99999) is None

    def test_get_manual_excludes_external(self, db):
        sub = ext_sub_repo.create(db, name="Sub", url="https://example.com")
        config_repo.create(db, name="Manual", raw_link="vless://m", subscription_id=None)
        config_repo.create(db, name="External", raw_link="vless://e", subscription_id=sub.id)

        manual = config_repo.get_manual(db)
        names = [c.name for c in manual]
        assert "Manual" in names
        assert "External" not in names

    def test_get_active_returns_only_active(self, db):
        cfg_on = config_repo.create(db, name="On", raw_link="vless://on")
        cfg_off = config_repo.create(db, name="Off", raw_link="vless://off")
        config_repo.toggle_active(db, cfg_off.id)  # make inactive

        active = config_repo.get_active(db)
        ids = [c.id for c in active]
        assert cfg_on.id in ids
        assert cfg_off.id not in ids

    def test_toggle_active_flips_status(self, db):
        cfg = config_repo.create(db, name="Toggle", raw_link="vless://toggle")
        assert cfg.is_active is True
        result = config_repo.toggle_active(db, cfg.id)
        assert result is False
        result2 = config_repo.toggle_active(db, cfg.id)
        assert result2 is True

    def test_toggle_nonexistent_returns_false(self, db):
        assert config_repo.toggle_active(db, 99999) is False

    def test_update_config(self, db):
        cfg = config_repo.create(db, name="Old", raw_link="vless://old")
        updated = config_repo.update(db, cfg.id, name="New", raw_link="vless://new", is_active=False)
        assert updated.name == "New"
        assert updated.raw_link == "vless://new"
        assert updated.is_active is False

    def test_rename_config(self, db):
        cfg = config_repo.create(db, name="Before", raw_link="vless://r")
        config_repo.rename(db, cfg.id, "After")
        found = config_repo.get_by_id(db, cfg.id)
        assert found.name == "After"

    def test_delete_config(self, db):
        cfg = config_repo.create(db, name="Delete Me", raw_link="vless://del")
        config_repo.delete(db, cfg.id)
        assert config_repo.get_by_id(db, cfg.id) is None

    def test_create_many(self, db):
        sub = ext_sub_repo.create(db, name="Bulk Sub", url="https://bulk.example.com")
        items = [
            {"name": f"Server {i}", "raw_link": f"vless://s{i}"}
            for i in range(3)
        ]
        count = config_repo.create_many(db, items=items, subscription_id=sub.id)
        assert count == 3
        configs = config_repo.get_by_subscription(db, sub.id)
        assert len(configs) == 3

    def test_get_settings_creates_default(self, db):
        settings = config_repo.get_settings(db)
        assert settings is not None
        assert settings.id == 1

    def test_update_settings(self, db):
        config_repo.update_settings(db, name="My VPN", desc="https://t.me/test")
        settings = config_repo.get_settings(db)
        assert settings.sub_name == "My VPN"
        assert settings.sub_description == "https://t.me/test"


class TestExternalSubscriptionRepository:
    def test_create_subscription(self, db):
        sub = ext_sub_repo.create(db, name="Sub A", url="https://sub-a.example.com")
        assert sub.id is not None
        assert sub.name == "Sub A"
        assert sub.url == "https://sub-a.example.com"

    def test_get_all_subscriptions(self, db):
        ext_sub_repo.create(db, name="Sub X", url="https://x.example.com")
        ext_sub_repo.create(db, name="Sub Y", url="https://y.example.com")
        subs = ext_sub_repo.get_all(db)
        names = [s.name for s in subs]
        assert "Sub X" in names
        assert "Sub Y" in names

    def test_get_by_id(self, db):
        sub = ext_sub_repo.create(db, name="Sub Z", url="https://z.example.com")
        found = ext_sub_repo.get_by_id(db, sub.id)
        assert found is not None
        assert found.name == "Sub Z"

    def test_get_by_id_returns_none(self, db):
        assert ext_sub_repo.get_by_id(db, 99999) is None

    def test_delete_subscription_cascades_configs(self, db):
        sub = ext_sub_repo.create(db, name="Cascade", url="https://cascade.example.com")
        config_repo.create_many(
            db,
            items=[{"name": "C1", "raw_link": "vless://c1"}],
            subscription_id=sub.id,
        )
        configs_before = config_repo.get_by_subscription(db, sub.id)
        assert len(configs_before) == 1

        ext_sub_repo.delete(db, sub.id)
        configs_after = config_repo.get_by_subscription(db, sub.id)
        assert len(configs_after) == 0


class TestExternalVpnServiceParsing:
    """Tests for parse_subscription and _extract_links."""

    def test_parse_plain_text_links(self):
        from app.services.external_vpn_service import parse_subscription
        content = "vless://abc@example.com:443#Server 1\ntrojan://xyz@host:443#Server 2"
        result = parse_subscription(content)
        assert len(result) == 2
        assert result[0]["name"] == "Server 1"
        assert result[1]["name"] == "Server 2"

    def test_parse_base64_encoded_subscription(self):
        import base64
        from app.services.external_vpn_service import parse_subscription
        plain = "vless://encoded@example.com:443#Encoded Server"
        encoded = base64.b64encode(plain.encode()).decode()
        result = parse_subscription(encoded)
        assert len(result) == 1
        assert result[0]["name"] == "Encoded Server"

    def test_parse_ignores_invalid_lines(self):
        from app.services.external_vpn_service import parse_subscription
        content = "not-a-protocol://something\nvless://valid@host:443#Valid"
        result = parse_subscription(content)
        assert len(result) == 1
        assert result[0]["name"] == "Valid"

    def test_parse_empty_string(self):
        from app.services.external_vpn_service import parse_subscription
        assert parse_subscription("") == []

    def test_link_without_fragment_uses_truncated_url(self):
        from app.services.external_vpn_service import parse_subscription
        link = "vless://nofragment@example.com:443/path"
        result = parse_subscription(link)
        assert len(result) == 1
        assert result[0]["raw_link"] == link
        assert result[0]["name"] == link[:40]

    def test_urlencoded_fragment_decoded(self):
        from app.services.external_vpn_service import parse_subscription
        content = "vless://x@h:443#%D0%A1%D0%B5%D1%80%D0%B2%D0%B5%D1%80"  # "Сервер"
        result = parse_subscription(content)
        assert result[0]["name"] == "Сервер"
