from postprocessors.base import BasePostProcessor
from models.schema import ProcessedResult, QueryResult


class DiversityReorder(BasePostProcessor):
    def __init__(self, diversity_threshold: float = 0.3):
        self.diversity_threshold = diversity_threshold

    async def process(self, result: ProcessedResult) -> ProcessedResult:
        if len(result.results) <= 1:
            return result

        selected_indices = self._mmr_selection(result.results)
        result.results = [result.results[i] for i in selected_indices]
        return result

    def _mmr_selection(self, results: list[QueryResult]) -> list[int]:
        selected = []
        remaining = list(range(len(results)))

        while remaining:
            if not selected:
                best_idx = max(remaining, key=lambda i: results[i].score)
            else:
                scores = []
                for i in remaining:
                    relevance = results[i].score
                    diversity = max(
                        self._similarity(results[i], results[j]) for j in selected
                    )
                    mmr = relevance - self.diversity_threshold * diversity
                    scores.append((i, mmr))
                best_idx = max(scores, key=lambda x: x[1])[0]

            selected.append(best_idx)
            remaining.remove(best_idx)

        return selected

    def _similarity(self, doc1: QueryResult, doc2: QueryResult) -> float:
        return len(set(doc1.content.split()) & set(doc2.content.split())) / len(
            set(doc1.content.split()) | set(doc2.content.split())
        )
