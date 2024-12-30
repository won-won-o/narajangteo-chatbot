# processors/sql_formatter.py
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from typing import Any
import json


class SQLResultFormatter:
    def __init__(self):
        self.llm = ChatOpenAI(temperature=0, model_name="gpt-4o-mini", streaming=True)

        self.format_prompt = ChatPromptTemplate.from_template(
            """SQL 쿼리 결과를 읽기 쉬운 마크다운 테이블 형식으로 변환해주세요.

            다음은 결과를 이해하는데 도움이 되는 정보입니다:
            1. SQL 쿼리: {query}
            2. 쿼리 결과: {result}
            3. 결과 존재 여부: {has_result}

            위 정보를 바탕으로 다음과 같이 응답해주세요:

            결과가 없는 경우:
            - "검색 결과가 없습니다. 다른 검색어나 조건으로 다시 시도해보세요." 메시지 출력

            위 정보를 바탕으로 다음과 같이 응답해주세요:
            1. 결과에 대한 간단한 설명을 한 문장으로 작성, 컬럼명은 한글로 변환
            2. 결과를 마크다운 테이블로 변환, 코드 블록으로 쓰지 말 것
            3. 필요한 경우 금액은 천 단위 콤마를 추가
            4. 날짜 형식은 YYYY-MM-DD로 통일
            5. 컬럼명은 이해하기 쉽게 한글로 변환
            """
        )

    def format_result(self, sql_query: str, query_result: Any, has_result):
        # SQL 결과를 문자열로 변환
        if isinstance(query_result, str):
            result_str = query_result
        else:
            result_str = json.dumps(query_result, ensure_ascii=False, indent=2)

        # LLM chain 생성 및 실행
        chain = self.format_prompt | self.llm

        # 스트리밍 응답을 반환
        return chain.stream(
            {"query": sql_query, "result": result_str, "has_result": has_result}
        )
