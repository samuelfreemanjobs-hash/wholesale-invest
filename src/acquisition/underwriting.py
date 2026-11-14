from .models import RehabRange, UnderwritingResult


def preliminary_assignment_fee(
    arv_base: float,
    rehab_base: float,
    margin_rate: float,
    asking_price: float,
    fee_min: float,
    fee_max: float,
) -> float:
    """Pick a target fee in range when economics support at least fee_min."""
    mao_without_fee = arv_base * (1.0 - margin_rate) - rehab_base
    room = mao_without_fee - asking_price
    if room < fee_min:
        return fee_min
    return min(fee_max, max(fee_min, room * 0.35))


def underwrite_lead(
    asking_price: float,
    arv_base: float,
    rehab: RehabRange,
    margin_rate: float,
    assignment_fee: float,
) -> UnderwritingResult:
    rehab_used = rehab.base_with_contingency()
    return UnderwritingResult.compute(
        asking_price=asking_price,
        arv_base=arv_base,
        rehab_base=rehab_used,
        margin_rate=margin_rate,
        assignment_fee=assignment_fee,
    )