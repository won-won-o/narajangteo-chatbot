from abc import ABC, abstractmethod
from models.schema import ProcessedResult


class BasePostProcessor(ABC):
    @abstractmethod
    async def process(self, result: ProcessedResult) -> ProcessedResult:
        pass
