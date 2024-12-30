import logging
from typing import List
from langchain_community.retrievers import PineconeHybridSearchRetriever
from langchain_openai import OpenAIEmbeddings
from pinecone_text.sparse import BM25Encoder
from pinecone import Pinecone
from models.schema import QueryResult
from config.settings import settings


class HybridRetriever:
    """Hybrid Search Retriever"""

    def __init__(
        self,
        namespace: str = None,
        top_k: int = 20,
        alpha: float = 0.2,
        embedding_model: str = "text-embedding-ada-002",
    ):
        self.namespace = namespace
        self.embedding_model = embedding_model
        self.top_k = top_k
        self.alpha = alpha

        # Pinecone 인덱스 초기화
        pc = Pinecone(
            api_key=settings.PINECONE_API_KEY, environment=settings.PINECONE_ENVIRONMENT
        )
        self.index = pc.Index(settings.PINECONE_INDEX_NAME)

        if namespace:
            self.retriever = self._setup_retriever(namespace=namespace)
        else:
            raise ValueError("Namespace is required.")

        logging.info("HybridRetriever 초기화 완료")

    def _setup_retriever(self, namespace: str = None) -> PineconeHybridSearchRetriever:
        """하이브리드 검색 리트리버 설정"""
        return PineconeHybridSearchRetriever(
            embeddings=OpenAIEmbeddings(model=self.embedding_model),
            sparse_encoder=BM25Encoder().default(),
            index=self.index,
            top_k=self.top_k,
            alpha=self.alpha,
            namespace=namespace,
        )

    def retrieve(self, query: str, namespace: str = None) -> List[QueryResult]:
        """주어진 쿼리에 대한 하이브리드 검색 수행"""
        try:
            logging.info(f"검색 시작 - 쿼리: {query}, 네임스페이스: {namespace}")

            # 검색 수행
            results = self.retriever.invoke(query)
            logging.info(f"검색 완료 - 결과 수: {len(results)}")

            # 결과 변환
            query_results = []
            for doc in results:
                query_results.append(
                    QueryResult(
                        content=doc.page_content,
                        metadata=doc.metadata,
                    )
                )

            return query_results

        except Exception as e:
            logging.error(f"검색 실패: {e}", exc_info=True)
            raise RuntimeError(f"Retrieval failed: {str(e)}")
