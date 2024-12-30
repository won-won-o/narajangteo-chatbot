from langchain.chains import create_sql_query_chain
from langchain_community.utilities import SQLDatabase
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import PromptTemplate

import streamlit as st

from processors.base import BaseProcessor
from models.schema import ProcessedResult, QueryResult
from config.settings import settings
from utils.sql_prompt import generate_prompt, generate_prompt_with_number


def extract_sql_query(response: str) -> str:
    """LLM 응답에서 SQL 쿼리만 추출"""
    try:
        # <sql> 태그 사이의 내용만 추출
        sql_part = response.split("<sql>")[1].split("</sql>")[0].strip()
        return sql_part
    except IndexError:
        raise ValueError("SQL 쿼리를 찾을 수 없습니다.")


class SQLProcessor(BaseProcessor):
    def __init__(self):
        self.db = SQLDatabase.from_uri(settings.POSTGRES_URI)
        custom_prompt = PromptTemplate(
            template=generate_prompt("{input}"),
            input_variables=["input", "table_info", "top_k"],
            partial_variables={"dialect": "postgresql"},
        )
        custom_prompt_with_number = PromptTemplate(
            template=generate_prompt_with_number("{input}"),
            input_variables=["input", "table_info", "top_k", "bid_notice_no"],
            partial_variables={"dialect": "postgresql"},
        )

        self.sql_chain = create_sql_query_chain(
            llm=ChatAnthropic(model="claude-3-5-sonnet-20241022", temperature=0),
            db=self.db,
            prompt=custom_prompt,
            k=10,
        )

        self.sql_chain_with_number = create_sql_query_chain(
            llm=ChatAnthropic(model="claude-3-5-sonnet-20241022", temperature=0),
            db=self.db,
            prompt=custom_prompt_with_number,
            k=10,
        )

    def process(self, query: str) -> ProcessedResult:
        if st.session_state.selected_bid_no:
            print("Using namespace:", st.session_state.selected_bid_no)
            llm_response = self.sql_chain_with_number.invoke(
                {
                    "question": query,
                    "table_names_to_use": [],
                    "table_info": "",
                    "bid_notice_no": st.session_state.selected_bid_no,
                }
            )
        else:
            llm_response = self.sql_chain.invoke(
                {"question": query, "table_names_to_use": [], "table_info": ""}
            )
        print(f"{llm_response=}")
        sql_query = extract_sql_query(llm_response)
        print(f"{sql_query=}")
        result = self.db.run(sql_query)

        if result:
            query_results = [
                QueryResult(
                    content=str(row), metadata={"sql_query": sql_query}, score=1.0
                )
                for row in result
            ]
        else:
            query_results = [
                QueryResult(
                    content="검색 결과가 없습니다. 다른 검색어로 다시 시도해보세요.",
                    metadata={"sql_query": sql_query, "status": "no_results"},
                    score=0.0,
                )
            ]

        return ProcessedResult(
            results=query_results, source_type="sql", raw_response=result
        )
