#!/usr/bin/env python3
"""Merge per-city lead JSONL blobs into acquisition candidates file."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

AVG_RENT: dict[str, int] = {
    "Detroit": 1353,
    "Ann Arbor": 2096,
    "Dearborn": 1718,
    "Royal Oak": 1700,
    "Troy": 1615,
    "Livonia": 1464,
    "Farmington Hills": 1489,
    "Southfield": 1445,
    "Sterling Heights": 1307,
    "Oak Park": 1252,
    "Ypsilanti": 1500,
    "Westland": 1190,
    "Taylor": 1189,
    "Warren": 1138,
    "Dearborn Heights": 1166,
    "Inkster": 1133,
    "Southgate": 1229,
    "Madison Heights": 1265,
    "Ferndale": 1400,
    "Pontiac": 1100,
}

CITY_ORDER = sorted(AVG_RENT.keys(), key=lambda c: -AVG_RENT[c])


def _parse_city(address: str, fallback: str) -> str:
    parts = [p.strip() for p in address.split(",")]
    if len(parts) >= 2:
        return parts[1]
    return fallback


def _normalize_home_type(value: str) -> str:
    v = value.lower().replace("-", "_")
    if v in {"single_family", "multi_family", "townhouse", "condo", "manufactured"}:
        return v
    return "single_family"


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    src = root / "data" / "live" / "_se_rental_city_blobs.jsonl"
    if not src.exists():
        raise SystemExit(f"Missing {src}")

    leads: list[dict] = []
    seen_zpid: set[str] = set()
    for line in src.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        blob = json.loads(line)
        city = blob["city"]
        rent = AVG_RENT.get(city, 0)
        rank = CITY_ORDER.index(city) + 1 if city in CITY_ORDER else 99
        for item in blob.get("leads", []):
            zpid = str(item.get("zpid", ""))
            if zpid and zpid in seen_zpid:
                continue
            if zpid:
                seen_zpid.add(zpid)
            address = str(item["address"])
            item_city = _parse_city(address, city)
            row = {
                "address": address,
                "city": item_city,
                "asking_price": item["asking_price"],
                "beds": item.get("beds"),
                "baths": item.get("baths"),
                "home_type": _normalize_home_type(str(item.get("home_type", "single_family"))),
                "living_area_sqft": item.get("living_area_sqft"),
                "url": item.get("url"),
                "zpid": zpid,
                "status_text": item.get("status_text"),
                "rental_market_rank": rank,
                "avg_market_rent": rent,
            }
            leads.append(row)

    out = {
        "source": "zillow_search",
        "market_run": "se_rental_top20",
        "retrieved_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "market_reference": "RentCafe city average rent comparison (Metro Detroit markets, 2026)",
        "cities": [
            {"city": c, "avg_rent_monthly_usd": AVG_RENT[c], "rental_rank": i + 1}
            for i, c in enumerate(CITY_ORDER)
        ],
        "leads": leads,
    }
    dest = root / "data" / "live" / "se_rental_top20_candidates.json"
    dest.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"Wrote {len(leads)} leads to {dest}")


if __name__ == "__main__":
    main()