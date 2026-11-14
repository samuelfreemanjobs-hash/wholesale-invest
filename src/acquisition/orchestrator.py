from dataclasses import asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from .buyers import load_buyers, match_buyers
from .config import load_config
from .db.vault import DealVault
from .export import leads_to_rows, write_csv, write_json
from .gates import qualification_gates
from .models import (
    CompSummary,
    ConfidenceLevel,
    PipelineStatus,
    PropertyLead,
    RehabRange,
    ScoreBreakdown,
)
from .connectors import ManualCandidatesConnector
from .pipeline import dedupe_leads, promote_status, stamp_retrieval
from .scoring import compute_score, priority_label
from .underwriting import preliminary_assignment_fee, underwrite_lead


def _default_comp_placeholder(asking: float) -> CompSummary:
    # Without sold comps, ARV must stay provisional — scoring penalizes heavily.
    provisional_arv = asking * 2.0
    return CompSummary(
        arv_low=provisional_arv * 0.85,
        arv_base=provisional_arv,
        arv_high=provisional_arv * 1.1,
        confidence=ConfidenceLevel.LOW,
        comp_count=0,
        notes="NEEDS COMP ANALYST — placeholder ARV until sold comps attached",
    )


def _default_rehab() -> RehabRange:
    return RehabRange(low=20_000, base=30_000, high=45_000, contingency_pct=0.1)


def enrich_and_underwrite(lead: PropertyLead, cfg: dict[str, Any]) -> PropertyLead:
    uw_cfg = cfg["underwriting"]
    margin = float(uw_cfg["investor_margin_and_cost_rate_default"])
    fee_min = float(uw_cfg["target_assignment_fee_min"])
    fee_max = float(uw_cfg["target_assignment_fee_max"])

    if lead.comps is None and lead.asking_price:
        lead.comps = _default_comp_placeholder(lead.asking_price)
    if lead.rehab is None:
        lead.rehab = _default_rehab()

    asking = lead.asking_price or 0.0
    arv = lead.comps.arv_base if lead.comps else asking
    rehab = lead.rehab
    fee = preliminary_assignment_fee(arv, rehab.base_with_contingency(), margin, asking, fee_min, fee_max)
    lead.underwriting = underwrite_lead(asking, arv, rehab, margin, fee)

    buyers = load_buyers()
    lead.buyer_match_ids = match_buyers(lead, buyers)
    return stamp_retrieval(lead)


def _jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if hasattr(value, "__dataclass_fields__"):
        return {k: _jsonable(v) for k, v in asdict(value).items()}
    return value


def run_daily_acquisitions(
    config_path: Path | None = None,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    cfg = load_config(config_path)
    out = output_dir or Path("exports")
    vault = DealVault()

    prop_cfg = cfg["property"]
    market_cfg = cfg["market"]
    cities = market_cfg["primary"][: market_cfg["max_cities_per_run"]]

    connector = ManualCandidatesConnector()
    candidates: list[PropertyLead] = []
    connector_errors: list[str] = []

    for city in cities:
        result = connector.discover(
            city=city,
            min_price=float(prop_cfg["minimum_asking_price"]),
            max_price=float(prop_cfg["maximum_asking_price"]),
        )
        candidates.extend(result.leads)
        connector_errors.extend(result.errors)

    candidates = dedupe_leads(candidates)
    researched: list[PropertyLead] = []
    scores: dict[str, ScoreBreakdown] = {}
    priorities: dict[str, str] = {}
    gate_log: dict[str, Any] = {}

    weights = cfg["scoring"]["weights"]
    bands = cfg["scoring"]["priority_bands"]
    require_buyer = bool(cfg["underwriting"]["require_buyer_match"])

    for lead in candidates:
        lead = enrich_and_underwrite(lead, cfg)
        score = compute_score(lead, weights)
        lead.score = score
        gate = qualification_gates(lead, require_buyer_match=require_buyer)
        # Comp count 0 fails gate — stays research unless economics + comps fixed
        if gate.failures and "No supporting sold comps" in gate.failures:
            lead.pipeline_status = PipelineStatus.RESEARCH
        else:
            promote_status(lead, gate.qualified)
        scores[lead.property_id] = score
        pri = priority_label(score.total, bands)
        if lead.score.hard_stop:
            pri = "Hard Stop"
        priorities[lead.property_id] = pri
        gate_log[lead.property_id] = {"failures": gate.failures, "warnings": gate.warnings}
        vault.upsert_lead(lead, score, pri)
        researched.append(lead)

    researched.sort(key=lambda lead_item: scores[lead_item.property_id].total, reverse=True)
    qualified = [
        lead
        for lead in researched
        if lead.pipeline_status == PipelineStatus.QUALIFIED
    ][: int(cfg["sourcing"]["qualified_lead_target"])]

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "version": cfg["system"]["version"],
        "markets": cities,
        "candidate_count": len(candidates),
        "underwritten_count": len(researched),
        "qualified_count": len(qualified),
        "connector_errors": connector_errors,
        "compliance": {
            "human_approval_required": cfg["system"]["human_approval_required"],
            "auto_messages": cfg["operations"]["send_messages_automatically"],
        },
        "leads": [
            {
                "property_id": lead.property_id,
                "address": lead.address,
                "city": lead.city,
                "score": scores[lead.property_id].total,
                "priority": priorities[lead.property_id],
                "pipeline_status": lead.pipeline_status.value,
                "gates": gate_log[lead.property_id],
                "underwriting": _jsonable(lead.underwriting) if lead.underwriting else None,
            }
            for lead in researched
        ],
    }

    rows = leads_to_rows(researched, scores, priorities)
    write_csv(out / f"acquisition_brief_{datetime.now(timezone.utc).date()}.csv", rows)
    write_json(out / f"acquisition_brief_{datetime.now(timezone.utc).date()}.json", report)
    return report