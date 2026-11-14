import unittest

from acquisition.models import RehabRange
from acquisition.underwriting import underwrite_lead


class UnderwritingTests(unittest.TestCase):
    def test_mao_example_from_spec(self) -> None:
        rehab = RehabRange(low=25_000, base=30_000, high=40_000, contingency_pct=0.0)
        uw = underwrite_lead(
            asking_price=80_000,
            arv_base=160_000,
            rehab=rehab,
            margin_rate=0.30,
            assignment_fee=7_000,
        )
        self.assertAlmostEqual(uw.buyer_mao, 75_000, places=0)
        self.assertFalse(uw.assignment_feasible)


if __name__ == "__main__":
    unittest.main()