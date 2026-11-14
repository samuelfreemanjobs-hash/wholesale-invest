from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class VerificationStatus(str, Enum):
    VERIFIED = "verified"
    PARTIAL = "partial"
    UNVERIFIED = "unverified"
    STALE = "stale"


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RiskClass(str, Enum):
    CLEAR = "clear"
    ELEVATED = "elevated"
    HARD_STOP = "hard_stop"


class PipelineStatus(str, Enum):
    CANDIDATE = "candidate"
    RESEARCH = "research"
    QUALIFIED = "qualified"
    REJECTED = "rejected"
    OUTREACH_DRAFT = "outreach_draft"


@dataclass
class SourceCitation:
    channel: str
    url: str
    retrieved_at: datetime
    snippet: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "channel": self.channel,
            "url": self.url,
            "retrieved_at": self.retrieved_at.isoformat(),
            "snippet": self.snippet,
        }


@dataclass
class RehabRange:
    low: float
    base: float
    high: float
    contingency_pct: float = 0.1

    def base_with_contingency(self) -> float:
        return self.base * (1.0 + self.contingency_pct)


@dataclass
class CompSummary:
    arv_low: float
    arv_base: float
    arv_high: float
    confidence: ConfidenceLevel
    comp_count: int
    notes: str = ""


@dataclass
class UnderwritingResult:
    asking_price: float
    arv_base: float
    rehab_base: float
    investor_margin_rate: float
    assignment_fee_target: float
    buyer_mao: float
    seller_offer_low: float
    seller_offer_high: float
    assignment_feasible: bool
    formula_notes: str = ""

    @staticmethod
    def compute(
        asking_price: float,
        arv_base: float,
        rehab_base: float,
        margin_rate: float,
        assignment_fee: float,
    ) -> "UnderwritingResult":
        # MAO = ARV * (1 - C) - Rehab - AssignmentFee (preliminary)
        buyer_mao = arv_base * (1.0 - margin_rate) - rehab_base - assignment_fee
        spread = buyer_mao - asking_price
        feasible = spread >= 0 and assignment_fee > 0
        offer_high = min(asking_price, max(0.0, buyer_mao))
        offer_low = max(0.0, offer_high * 0.92)
        return UnderwritingResult(
            asking_price=asking_price,
            arv_base=arv_base,
            rehab_base=rehab_base,
            investor_margin_rate=margin_rate,
            assignment_fee_target=assignment_fee,
            buyer_mao=buyer_mao,
            seller_offer_low=offer_low,
            seller_offer_high=offer_high,
            assignment_feasible=feasible,
            formula_notes="MAO = ARV×(1−C) − Rehab − AssignmentFee",
        )


@dataclass
class ScoreBreakdown:
    financial_feasibility: float = 0.0
    seller_motivation: float = 0.0
    comp_confidence: float = 0.0
    buyer_demand: float = 0.0
    execution_feasibility: float = 0.0
    competition_advantage: float = 0.0
    freshness_contactability: float = 0.0
    data_reliability: float = 0.0
    risk_class: RiskClass = RiskClass.CLEAR
    hard_stop: bool = False

    @property
    def total(self) -> float:
        if self.hard_stop:
            return 0.0
        return (
            self.financial_feasibility
            + self.seller_motivation
            + self.comp_confidence
            + self.buyer_demand
            + self.execution_feasibility
            + self.competition_advantage
            + self.freshness_contactability
            + self.data_reliability
        )


@dataclass
class PropertyLead:
    property_id: str
    address: str
    city: str
    state: str = "MI"
    zip_code: str = ""
    asking_price: float | None = None
    beds: int | None = None
    baths: float | None = None
    sources: list[SourceCitation] = field(default_factory=list)
    verification: VerificationStatus = VerificationStatus.UNVERIFIED
    pipeline_status: PipelineStatus = PipelineStatus.CANDIDATE
    score: ScoreBreakdown = field(default_factory=ScoreBreakdown)
    underwriting: UnderwritingResult | None = None
    comps: CompSummary | None = None
    rehab: RehabRange | None = None
    risk_notes: list[str] = field(default_factory=list)
    motivation_evidence: list[str] = field(default_factory=list)
    buyer_match_ids: list[str] = field(default_factory=list)
    outreach_draft: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def retrieved_at(self) -> datetime:
        if self.sources:
            return max(s.retrieved_at for s in self.sources)
        return datetime.now(timezone.utc)