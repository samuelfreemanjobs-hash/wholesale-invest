from pathlib import Path
from typing import Any

import yaml

from .models import PropertyLead

DEFAULT_BUYERS_PATH = Path(__file__).resolve().parents[2] / "config" / "buyers.yml"


def load_buyers(path: Path | None = None) -> list[dict[str, Any]]:
    buyers_path = path or DEFAULT_BUYERS_PATH
    if not buyers_path.exists():
        return []
    with buyers_path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return list(data.get("buyers", []))


def match_buyers(lead: PropertyLead, buyers: list[dict[str, Any]]) -> list[str]:
    """Match on documented criteria only — never infer activity from old sales."""
    matches: list[str] = []
    price = lead.asking_price or 0.0
    for buyer in buyers:
        if not buyer.get("documented_criteria"):
            continue
        if buyer.get("active_ready") is not True:
            continue
        zips = buyer.get("target_zips") or []
        cities = [c.lower() for c in buyer.get("target_cities") or []]
        price_min = float(buyer.get("price_min", 0))
        price_max = float(buyer.get("price_max", 9_999_999))
        if lead.city.lower() not in cities and (not zips or lead.zip_code not in zips):
            continue
        if price and not (price_min <= price <= price_max):
            continue
        prop_types = buyer.get("property_types") or []
        lead_type = lead.metadata.get("property_type", "single_family")
        if prop_types and lead_type not in prop_types:
            continue
        matches.append(str(buyer["buyer_id"]))
    return matches