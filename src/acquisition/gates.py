from dataclasses import dataclass

from .models import PropertyLead, RiskClass, VerificationStatus


@dataclass
class GateResult:
    qualified: bool
    failures: list[str]
    warnings: list[str]


def qualification_gates(lead: PropertyLead, require_buyer_match: bool) -> GateResult:
    failures: list[str] = []
    warnings: list[str] = []

    if not lead.address or not lead.city:
        failures.append("Property or listing source not identifiable")
    if not lead.sources:
        failures.append("No source citation")
    if lead.verification == VerificationStatus.UNVERIFIED and not lead.metadata.get(
        "allow_unverified_listing"
    ):
        warnings.append("Listing lead not ownership-verified")
    if lead.comps is None or lead.comps.comp_count < 1:
        failures.append("No supporting sold comps")
    if lead.rehab is None:
        failures.append("Repair assumptions not documented")
    if lead.underwriting is None:
        failures.append("Underwriting incomplete")
    elif not lead.underwriting.assignment_feasible:
        failures.append("Economics fail: MAO below asking or zero assignment capacity")
    if require_buyer_match and not lead.buyer_match_ids:
        warnings.append("No documented buyer match (required by config)")
    if lead.score.hard_stop or lead.score.risk_class == RiskClass.HARD_STOP:
        failures.append("Hard-stop risk unresolved")
    if not lead.metadata.get("contact_path"):
        failures.append("No legitimate contact path recorded")

    qualified = len(failures) == 0
    return GateResult(qualified=qualified, failures=failures, warnings=warnings)


def apply_hard_stops(lead: PropertyLead, hard_stop_reasons: list[str]) -> PropertyLead:
    if hard_stop_reasons:
        lead.score.hard_stop = True
        lead.score.risk_class = RiskClass.HARD_STOP
        lead.risk_notes.extend(hard_stop_reasons)
    return lead