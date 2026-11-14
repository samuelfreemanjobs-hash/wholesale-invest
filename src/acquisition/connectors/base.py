from abc import ABC, abstractmethod
from dataclasses import dataclass

from ..models import PropertyLead


@dataclass
class ConnectorResult:
    channel: str
    leads: list[PropertyLead]
    errors: list[str]


class ListingConnector(ABC):
    name: str

    @abstractmethod
    def discover(self, city: str, min_price: float, max_price: float) -> ConnectorResult:
        raise NotImplementedError