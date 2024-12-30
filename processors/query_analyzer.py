from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser
from langchain.prompts import ChatPromptTemplate
from typing import List, Literal
from pydantic import BaseModel, Field


class SearchIntentModel(BaseModel):
    """검색 의도를 나타내는 Pydantic 모델"""

    keywords: List[str] = Field(
        description="검색에 사용될 핵심 키워드 리스트", min_items=1
    )
    search_type: Literal["general", "qualification", "price", "schedule"] = Field(
        description="검색 유형 (일반, 자격요건, 가격, 일정)"
    )
    filters: dict = Field(description="검색에 적용할 필터 조건", default_factory=dict)
    confidence: float = Field(
        description="분석 결과의 신뢰도 점수 (0.0 ~ 1.0)", ge=0.0, le=1.0
    )


class QueryAnalyzer:
    def __init__(self):
        # JSON 응답 형식을 강제하는 모델 설정
        self.llm = ChatOpenAI(
            temperature=0,
            model="gpt-4o-mini",
            model_kwargs={"response_format": {"type": "json_object"}},
        )

        # JSON 파서 설정
        self.parser = JsonOutputParser(pydantic_object=SearchIntentModel)

        # 프롬프트 템플릿 설정
        self.analysis_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """입찰공고 검색 시스템의 쿼리 분석을 수행하는 전문가입니다.
            사용자의 질문을 분석하여 다음 정보를 추출합니다:

            1. keywords: 검색에 사용될 핵심 키워드 (반드시 1개 이상)
            2. search_type: 검색 유형 (general/qualification/price/schedule 중 하나)
            3. filters: 검색 필터 (옵션)
            4. confidence: 분석 신뢰도 (0.0 ~ 1.0)

            JSON 형식으로 응답해야 합니다.
            """,
                ),
                ("user", "{query}"),
                ("assistant", "검색 의도를 분석하여 JSON 형식으로 응답하겠습니다."),
                ("system", "{format_instructions}"),
            ]
        )

    def analyze(self, query: str) -> SearchIntentModel:
        """사용자 쿼리를 분석하여 구조화된 검색 의도를 반환합니다."""
        try:
            # 프롬프트 준비
            prompt = self.analysis_prompt.format_messages(
                query=query, format_instructions=self.parser.get_format_instructions()
            )

            # LLM 호출 및 결과 파싱
            response = self.llm.invoke(prompt)
            parsed_response = self.parser.parse(response.content)

            return parsed_response

        except Exception as e:
            raise ValueError(f"쿼리 분석 중 오류 발생: {str(e)}")

    def _validate_search_type(self, search_type: str) -> str:
        """검색 유형의 유효성을 검증합니다."""
        valid_types = {"general", "qualification", "price", "schedule"}
        if search_type not in valid_types:
            return "general"
        return search_type
