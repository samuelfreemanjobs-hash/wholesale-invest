"""Manual / imported candidate feed for Milestone 1 when live connectors are not wired."""

from datetime import datetime, timezone

from ..models import PipelineStatus, PropertyLead, SourceCitation, VerificationStatus
from ..pipeline import property_id_from_address
from .base import ConnectorResult, ListingConnector


class ManualCandidatesConnector(ListingConnector):
    name = "manual"

    def discover(self, city: str, min_price: float, max_price: float) -> ConnectorResult:
        # Phase 1 live research examples (TRAINING / re-underwrite only — verify before outreach).
        samples = [
            {
                "address": "352 Worden St",
                "city": "Warren",
                "zip": "48089",
                "price": 55000,
                "url": "https://www.fsbo.com/",
                "notes": "Gutted / estate context per prior live pull — re-verify listing",
            },
            {
                "address": "22613 Sharrow",
                "city": "Warren",
                "zip": "48089",
                "price": 72000,
                "url": "https://www.fsbo.com/",
                "notes": "FSBO — re-verify price and contact",
            },
            {
                "address": "314 Washtenaw Ave",
                "city": "Ypsilanti",
                "zip": "48197",
                "price": 89000,
                "url": "https://www.fsbo.com/",
                "notes": "As-is FSBO — re-verify listing and comps",
            },
        ]
        leads: list[PropertyLead] = []
        now = datetime.now(timezone.utc)
        for item in samples:
            if item["city"].lower() != city.lower():
                continue
            if not (min_price <= item["price"] <= max_price):
                continue
            lead = PropertyLead(
                property_id=property_id_from_address(item["address"], item["city"], item["zip"]),
                address=item["address"],
                city=item["city"],
                zip_code=item["zip"],
                asking_price=float(item["price"]),
                sources=[
                    SourceCitation(
                        channel="fsbo",
                        url=item["url"],
                        retrieved_at=now,
                        snippet=item["notes"],
                    )
                ],
                verification=VerificationStatus.PARTIAL,
                pipeline_status=PipelineStatus.CANDIDATE,
                motivation_evidence=["fsbo_listing", "needs_work_language_unverified"],
                metadata={
                    "contact_path": "listing_url",
                    "listing_age_days": 21,
                    "property_type": "single_family",
                    "competition_advantage": "medium",
                },
            )
            leads.append(lead)
        return ConnectorResult(channel=self.name, leads=leads, errors=[])