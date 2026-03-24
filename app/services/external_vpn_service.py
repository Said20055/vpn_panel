# app/services/external_vpn_service.py
import base64
import uuid
from urllib.parse import unquote

import httpx
from sqlalchemy.orm import Session

from app.domain.models import Config, ExternalSubscription
from app.repository.external_vpn_repository import ext_sub_repo
from app.repository.vpn_repository import config_repo

VALID_PREFIXES = ("vless://", "vmess://", "trojan://", "ss://", "hysteria2://", "hy2://", "tuic://")

_HWID = str(uuid.uuid5(uuid.NAMESPACE_DNS, "vpn-bot-fetcher"))

_FETCH_HEADERS = {
    "User-Agent": "HappProxy/2.1.6 (Linux; Bot)",
    "x-hwid": _HWID,
    "x-device-os": "Linux",
    "x-ver-os": "6.1",
    "x-device-model": "Server",
    "Accept": "*/*",
}


def _extract_links(text: str) -> list[dict]:
    links = []
    for line in text.splitlines():
        line = line.strip()
        if any(line.startswith(p) for p in VALID_PREFIXES):
            if "#" in line:
                raw_link, fragment = line.rsplit("#", 1)
                name = unquote(fragment).strip() or raw_link[:40]
            else:
                raw_link = line
                name = line[:40]
            links.append({"name": name, "raw_link": line})
    return links


def parse_subscription(content: str) -> list[dict]:
    """Plain-text or base64 subscription → list of {name, raw_link}."""
    links = _extract_links(content)
    if links:
        return links
    try:
        decoded = base64.b64decode(content + "==").decode("utf-8", errors="ignore")
        return _extract_links(decoded)
    except Exception:
        return []


class ExternalVpnService:
    def fetch_and_parse(self, url: str) -> list[dict]:
        """Fetch subscription URL and return list of {name, raw_link}."""
        with httpx.Client(timeout=15, follow_redirects=True, verify=False) as client:
            response = client.get(url, headers=_FETCH_HEADERS)
            response.raise_for_status()
        return parse_subscription(response.text)

    def save_configs(self, db: Session, url: str, name: str, selected: list[dict]) -> tuple[ExternalSubscription, int]:
        """Create ExternalSubscription and save selected configs into the unified Config table."""
        sub = ext_sub_repo.create(db, name=name, url=url)
        count = config_repo.create_many(db, items=selected, subscription_id=sub.id)
        return sub, count

    def get_all_subscriptions(self, db: Session) -> list[ExternalSubscription]:
        return ext_sub_repo.get_all(db)

    def get_configs_by_subscription(self, db: Session, sub_id: int) -> list[Config]:
        return config_repo.get_by_subscription(db, sub_id)

    def delete_subscription(self, db: Session, sub_id: int):
        ext_sub_repo.delete(db, sub_id)


ext_vpn_service = ExternalVpnService()
