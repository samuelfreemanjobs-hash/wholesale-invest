import json
import re
from datetime import datetime, timezone
from pathlib import Path

from ..models import PipelineStatus, PropertyLead, SourceCitation, VerificationStatus
from ..pipeline import property_id_from_address
from .base import ConnectorResult, ListingConnector


def _parse_zip(address: str) -> str:
    match = re.search(r"\b(\d{5})\b", address)
    return match.group(1) if match else ""


def _parse_street(address: str) -> str:
    return address.split(",")[0].strip()


class JsonCandidatesConnector(ListingConnector):
    name = "json"

    def __init__(self, path: Path) -> None:
        self.path = path

    def discover(self, city: str, min_price: float, max_price: float) -> ConnectorResult:
        if not self.path.exists():
            return ConnectorResult(
                channel=self.name,
                leads=[],
                errors=[f"Candidates file not found: {self.path}"],
            )
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        items = raw.get("leads", raw) if isinstance(raw, dict) else raw
        if not isinstance(items, list):
            return ConnectorResult(channel=self.name, leads=[], errors=["Invalid candidates JSON"])

        now = datetime.now(timezone.utc)
        channel = raw.get("source", "zillow_search") if isinstance(raw, dict) else "json_import"
        leads: list[PropertyLead] = []
        errors: list[str] = []

        for item in items:
            item_city = str(item.get("city", "Ann Arbor"))
            if item_city.lower() != city.lower():
                continue
            price = float(item.get("asking_price", 0) or 0)
            if price and not (min_price <= price <= max_price):
                continue
            beds = item.get("beds")
            baths = item.get("baths")
            address = str(item.get("address", ""))
            street = item.get("street") or _parse_street(address)
            zip_code = str(item.get("zip_code") or _parse_zip(address))
            url = str(item.get("url", ""))
            lead = PropertyLead(
                property_id=property_id_from_address(street, item_city, zip_code),
                address=street,
                city=item_city,
                zip_code=zip_code,
                asking_price=price or None,
                beds=int(beds) if beds is not None else None,
                baths=float(baths) if baths is not None else None,
                sources=[
                    SourceCitation(
                        channel=channel,
                        url=url,
                        retrieved_at=now,
                        snippet=item.get("status_text", ""),
                    )
                ],
                verification=VerificationStatus.PARTIAL,
                pipeline_status=PipelineStatus.CANDIDATE,
                motivation_evidence=["mls_agent_listing"],
                metadata={
                    "contact_path": "listing_agent",
                    "property_type": str(item.get("home_type", "single_family")).lower(),
                    "zpid": item.get("zpid"),
                    "living_area_sqft": item.get("living_area_sqft"),
                    "competition_advantage": "low",
                },
            )
            leads.append(lead)

        if not leads:
            errors.append(f"No candidates matched {city} and ${min_price:.0f}-${max_price:.0f}")
        return ConnectorResult(channel=self.name, leads=leads, errors=errors)