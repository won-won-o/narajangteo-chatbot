from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from typing import List
from pydantic import BaseModel


class SearchKeywords(BaseModel):
    """공고 검색을 위한 키워드 모델"""

    search_keywords: List[str]


class KeywordExtractor:
    def __init__(self):
        self.llm = ChatOpenAI(
            temperature=0,
            model="gpt-4o-mini",
            model_kwargs={"response_format": {"type": "json_object"}},
        )

        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
            사용자의 질문에서 입찰공고를 검색하기 위한 핵심 키워드만을 추출하는 작업을 수행합니다.

            다음 규칙을 따라주세요:
            1. 반드시 공고명에 포함될 가능성이 높은 단어만 선택
            2. 다음 단어들은 절대 키워드로 선택하지 않음:
               - 자격요건, 가격, 금액, 날짜, 기간 등 검색 조건
               - 찾아줘, 검색해줘 등의 행동 요청
               - 공고, 입찰, 제안 등 모든 공고에 공통적인 단어
               - ~해서, ~에서 등의 조사
            3. 키워드는 2-4개로 유지
            4. json 형식으로 "search_keywords"에 리스트 형태로 담아 추출
            """,
                ),
                ("user", "{query}"),
            ]
        )

    def extract(self, query: str) -> List[str]:
        """사용자 쿼리에서 검색 키워드를 추출합니다."""
        try:
            # LLM 호출
            messages = self.prompt.format_messages(query=query)
            response = self.llm.invoke(messages)

            # 결과 파싱
            result = SearchKeywords.model_validate_json(response.content)
            return result.search_keywords

        except Exception as e:
            print(f"키워드 추출 중 오류 발생: {str(e)}")
            # 오류 발생 시 입력 텍스트에서 기본적인 키워드 추출
            default_keywords = [w for w in query.split() if len(w) > 1][:3]
            return default_keywords
