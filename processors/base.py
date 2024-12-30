from abc import ABC, abstractmethod
from models.schema import ProcessedResult


class BaseProcessor(ABC):
    @abstractmethod
    def process(self, query: str) -> ProcessedResult:
        pass
