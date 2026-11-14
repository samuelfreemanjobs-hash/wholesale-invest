from typing import Any

from .models import (
    ConfidenceLevel,
    PropertyLead,
    RiskClass,
    ScoreBreakdown,
    UnderwritingResult,
    VerificationStatus,
)


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def score_financial_feasibility(weights: dict[str, float], uw: UnderwritingResult | None) -> float:
    cap = weights["financial_feasibility"]
    if uw is None:
        return 0.0
    if not uw.assignment_feasible:
        return cap * 0.15
    gap = uw.buyer_mao - uw.asking_price
    if gap <= 0:
        return cap * 0.2
    # Scale: $15k+ headroom → full points
    ratio = _clamp(gap / 15_000.0, 0.0, 1.0)
    fee_bonus = 0.2 if uw.assignment_fee_target >= 3_000 else 0.0
    return cap * _clamp(0.35 + 0.45 * ratio + fee_bonus, 0.0, 1.0)


def score_comp_confidence(weights: dict[str, float], lead: PropertyLead) -> float:
    cap = weights["comp_confidence"]
    if lead.comps is None or lead.comps.comp_count < 1:
        return 0.0
    base = {ConfidenceLevel.HIGH: 1.0, ConfidenceLevel.MEDIUM: 0.65, ConfidenceLevel.LOW: 0.35}[
        lead.comps.confidence
    ]
    count_factor = _clamp(lead.comps.comp_count / 3.0, 0.3, 1.0)
    return cap * base * count_factor


def score_data_reliability(weights: dict[str, float], lead: PropertyLead) -> float:
    cap = weights["data_reliability"]
    status_factor = {
        VerificationStatus.VERIFIED: 1.0,
        VerificationStatus.PARTIAL: 0.6,
        VerificationStatus.UNVERIFIED: 0.25,
        VerificationStatus.STALE: 0.15,
    }[lead.verification]
    citation_factor = 1.0 if lead.sources else 0.0
    return cap * status_factor * (0.5 + 0.5 * citation_factor)


def score_motivation(weights: dict[str, float], lead: PropertyLead) -> float:
    cap = weights["seller_motivation"]
    if not lead.motivation_evidence:
        return cap * 0.2
    points = min(len(lead.motivation_evidence), 5) / 5.0
    return cap * (0.35 + 0.65 * points)


def score_buyer_demand(weights: dict[str, float], lead: PropertyLead) -> float:
    cap = weights["buyer_demand"]
    if lead.buyer_match_ids:
        return cap * _clamp(0.4 + 0.2 * len(lead.buyer_match_ids), 0.0, 1.0)
    rank = lead.metadata.get("rental_market_rank")
    if rank is not None:
        try:
            rental_rank = int(rank)
        except (TypeError, ValueError):
            rental_rank = 20
        tier = _clamp(1.0 - (rental_rank - 1) / 19.0, 0.35, 1.0)
        return cap * tier
    return cap * 0.15


def score_execution(weights: dict[str, float], lead: PropertyLead) -> float:
    cap = weights["execution_feasibility"]
    if lead.risk_notes:
        penalty = min(0.8, 0.15 * len(lead.risk_notes))
        return cap * (1.0 - penalty)
    return cap * 0.85


def score_competition(weights: dict[str, float], meta: dict[str, Any]) -> float:
    cap = weights["competition_advantage"]
    indicator = meta.get("competition_advantage", "unknown")
    if indicator == "low":
        return cap
    if indicator == "medium":
        return cap * 0.5
    if indicator == "high":
        return cap * 0.15
    return cap * 0.4


def score_freshness(weights: dict[str, float], lead: PropertyLead) -> float:
    cap = weights["freshness_contactability"]
    days = lead.metadata.get("listing_age_days")
    if days is None:
        return cap * 0.4
    if days <= 14:
        return cap
    if days <= 45:
        return cap * 0.7
    return cap * 0.45


def compute_score(lead: PropertyLead, weights: dict[str, float]) -> ScoreBreakdown:
    breakdown = ScoreBreakdown()
    if lead.score.hard_stop:
        breakdown.hard_stop = True
        breakdown.risk_class = RiskClass.HARD_STOP
        return breakdown

    breakdown.financial_feasibility = score_financial_feasibility(weights, lead.underwriting)
    breakdown.seller_motivation = score_motivation(weights, lead)
    breakdown.comp_confidence = score_comp_confidence(weights, lead)
    breakdown.buyer_demand = score_buyer_demand(weights, lead)
    breakdown.execution_feasibility = score_execution(weights, lead)
    breakdown.competition_advantage = score_competition(weights, lead.metadata)
    breakdown.freshness_contactability = score_freshness(weights, lead)
    breakdown.data_reliability = score_data_reliability(weights, lead)
    breakdown.risk_class = lead.score.risk_class
    breakdown.hard_stop = lead.score.hard_stop
    return breakdown


def priority_label(total: float, bands: list[dict[str, Any]]) -> str:
    ordered = sorted(bands, key=lambda b: b["min_score"], reverse=True)
    for band in ordered:
        if total >= band["min_score"]:
            return band["label"]
    return "Research"