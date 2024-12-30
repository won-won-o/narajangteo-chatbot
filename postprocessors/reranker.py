import logging
import cohere

from langchain_core.documents import Document
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import CrossEncoderReranker
from langchain_cohere import CohereRerank
from models.schema import ProcessedResult, QueryResult
from config.settings import settings


class HuggingFaceReranker:

    def __init__(
        self,
        retriever,
        model_name: str = "BAAI/bge-reranker-v2-m3",
        top_n: int = 5,
    ):
        self.model = HuggingFaceCrossEncoder(model_name=model_name)
        self.compressor = CrossEncoderReranker(model=self.model, top_n=top_n)
        self.compression_retriever = ContextualCompressionRetriever(
            base_compressor=self.compressor, base_retriever=retriever
        )

    def process(self, query) -> list[Document]:
        return self.compression_retriever.invoke(query)


class CohereDocumentReranker:
    def __init__(self, model: str = "rerank-multilingual-v3.0", top_k: int = 5):
        self.model = model
        self.top_k = top_k
        self.api_key = settings.COHERE_API_KEY
        if not self.api_key:
            raise ValueError("COHERE_API_KEY를 찾을 수 없습니다.")
        self.reranker = self._setup_reranker()

    def _setup_reranker(self):
        """Cohere Reranker 설정"""
        logging.info(f"Cohere Reranker 모델 '{self.model}' 초기화 중...")

        # cohere.Client를 API 키로 초기화
        client = cohere.Client(api_key=self.api_key)

        # client를 CohereRerank에 전달
        return CohereRerank(model=self.model, top_n=self.top_k, client=client)

    def rerank(self, processed_result: ProcessedResult, query: str) -> ProcessedResult:
        """검색 결과 재순위화"""
        try:
            if not processed_result.results:
                logging.warning("재순위화할 결과가 없습니다.")
                return processed_result

            logging.info(
                f"재순위화 시작 - 입력 문서 수: {len(processed_result.results)}"
            )

            # QueryResult를 Document로 변환
            documents = [
                Document(page_content=result.content, metadata=result.metadata)
                for result in processed_result.results
            ]
            logging.info("문서 변환 완료")

            # 재순위화 수행
            reranked_docs = self.reranker.compress_documents(documents, query)
            logging.info(f"재순위화 완료 - 출력 문서 수: {len(reranked_docs)}")

            # Document를 QueryResult로 변환
            reranked_results = [
                QueryResult(
                    content=doc.page_content,
                    metadata=doc.metadata,
                    score=getattr(doc, "score", 1.0),
                )
                for doc in reranked_docs
            ]

            return ProcessedResult(
                results=reranked_results,
                source_type=processed_result.source_type,
                raw_response=reranked_docs,
            )

        except Exception as e:
            logging.error(f"재순위화 실패: {e}")
            raise
