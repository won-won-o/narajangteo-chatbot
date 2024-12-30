import logging
import streamlit as st
from langchain_core.prompts import load_prompt
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from postprocessors.reranker import CohereDocumentReranker
from processors.base import BaseProcessor
from processors.retriever import HybridRetriever
from models.schema import ProcessedResult, QueryResult
from config.settings import settings


class VectorProcessor(BaseProcessor):
    def __init__(self, text_key="context"):
        # gRPC 클라이언트로 Pinecone 초기화
        self._namespace = None
        self.embeddings = OpenAIEmbeddings()
        self.pc = PineconeVectorStore(
            index_name=settings.PINECONE_INDEX_NAME,
            embedding=self.embeddings,
            text_key=text_key,
        )
        self.response_prompt = load_prompt(
            "prompts/vector_process.yaml", encoding="utf-8"
        )
        self.llm = ChatOpenAI(temperature=0, model_name="gpt-4o")

    @property
    def namespace(self):
        return self._namespace

    @namespace.setter
    def namespace(self, value):
        self._namespace = value

    def process(self, query: str, top_k: int = 5) -> ProcessedResult:
        # 쿼리 임베딩 생성
        try:
            # 1. retriever 단계
            st.info("Starting Hybrid Retrieval...")
            retriever = HybridRetriever(self.namespace)
            results = retriever.retrieve(query)

            logging.info(f"검색 완료 - 결과 수: {len(results)}")

            # 결과 변환
            results = [
                QueryResult(
                    content=result.content,
                    metadata=result.metadata,
                )
                for result in results
            ]

            # 2. rerank 단계
            st.info("Starting Reranking...")
            reranker = CohereDocumentReranker(top_k=top_k)
            results = reranker.rerank(
                ProcessedResult(
                    results=results, source_type="vector", raw_response=results
                ),
                query,
            )

            st.info("Hybrid Retrieval Completed!")

            return results

        except Exception as e:
            print(f"Error processing vector query: {e}")
            return ProcessedResult(
                results=[], source_type="vector", raw_response=str(e)
            )

    def response(self, query: str, result: ProcessedResult):

        # 3. response 만들기
        print(f"{len(result.results)} results found")
        # extract_results = [r for r in result.results if r.metadata["type"] == "table"][
        #     :2
        # ]
        # extract_results.extend(
        #     [r for r in result.results if r.metadata["type"] != "table"][:5]
        # )

        # 테이블 데이터와 일반 텍스트 분리
        table_results = [
            r for r in result.results if r.metadata.get("type") == "table"
        ][:2]
        text_results = [r for r in result.results if r.metadata.get("type") != "table"][
            :5
        ]

        # 컨텍스트 생성 (출처 정보 포함)
        contexts = []

        def get_source_info(metadata):
            file_name = metadata.get("file_name", "문서")
            # .pdf 확장자 제거
            if file_name.lower().endswith(".pdf"):
                file_name = file_name[:-4]

            page = metadata.get("page", "N/A")
            if isinstance(page, (int, float)):
                page = int(page)

            return f"[답변 출처: {file_name} p.{page}]"

        # 테이블 데이터 처리
        for r in table_results:
            source = get_source_info(r.metadata)
            contexts.append(f"{r.content} {source}")

        # 일반 텍스트 처리
        for r in text_results:
            source = get_source_info(r.metadata)
            contexts.append(f"{r.content} {source}")

        # context = "\n".join([query_result.content for query_result in extract_results])
        context = "\n".join(contexts)
        chain = self.response_prompt | self.llm

        response = chain.stream({"context": context, "query": query})

        return response
