import hashlib
import re
from datetime import datetime, timezone

from .models import PipelineStatus, PropertyLead, VerificationStatus


def normalize_address(address: str) -> str:
    lowered = address.lower().strip()
    lowered = re.sub(r"\s+", " ", lowered)
    return lowered


def property_id_from_address(address: str, city: str, zip_code: str = "") -> str:
    key = f"{normalize_address(address)}|{city.lower()}|{zip_code}"
    return hashlib.sha256(key.encode()).hexdigest()[:16]


def dedupe_leads(leads: list[PropertyLead]) -> list[PropertyLead]:
    seen: dict[str, PropertyLead] = {}
    for lead in leads:
        pid = lead.property_id or property_id_from_address(lead.address, lead.city, lead.zip_code)
        lead.property_id = pid
        if pid not in seen:
            seen[pid] = lead
            continue
        existing = seen[pid]
        existing.sources.extend(lead.sources)
        if (lead.asking_price or 0) > 0 and not existing.asking_price:
            existing.asking_price = lead.asking_price
    return list(seen.values())


def promote_status(lead: PropertyLead, qualified: bool) -> PropertyLead:
    if lead.score.hard_stop:
        lead.pipeline_status = PipelineStatus.REJECTED
    elif qualified:
        lead.pipeline_status = PipelineStatus.QUALIFIED
    elif lead.comps and lead.underwriting:
        lead.pipeline_status = PipelineStatus.RESEARCH
    else:
        lead.pipeline_status = PipelineStatus.CANDIDATE
    return lead


def stamp_retrieval(lead: PropertyLead) -> PropertyLead:
    if not lead.sources:
        lead.verification = VerificationStatus.UNVERIFIED
    elif lead.verification == VerificationStatus.UNVERIFIED:
        lead.verification = VerificationStatus.PARTIAL
    lead.metadata.setdefault("last_pipeline_at", datetime.now(timezone.utc).isoformat())
    return lead