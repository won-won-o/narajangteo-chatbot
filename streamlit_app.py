import logging
import streamlit as st
from core.router import QueryRouter
from processors.sql_processor import SQLProcessor
from processors.namespace_finder import NamespaceFinder
from processors.vector_processor import VectorProcessor
from processors.sql_formatter import SQLResultFormatter
import os


class RAGApp:
    def __init__(self):
        self.router = QueryRouter()
        self.sql_processor = SQLProcessor()
        self.vector_processor = VectorProcessor()
        self.sql_formatter = SQLResultFormatter()
        self.namespace_finder = NamespaceFinder()

    def process_query(self, query: str):
        # 쿼리 라우팅
        db_type = self.router.route(query)

        print(f"{db_type} 조회...")

        # 프로세서 선택 및 실행
        if db_type == "rdb":
            result = self.sql_processor.process(query)
            print(f"rdb결과.. {result}")
            return (
                self.sql_formatter.format_result(
                    result.results[0].metadata["sql_query"],
                    result.raw_response,
                    bool(result.results[0].score),
                ),
                db_type,
            )
        else:
            logging.info("Processing Vector query...")
            # Vector 검색을 위한 namespace 찾기
            if not st.session_state.selected_bid_no:
                st.session_state.namespace_finder.find_namespace(query)
                print(f"Found namespace: {st.session_state.selected_bid_no}")
                if not st.session_state.selected_bid_no:
                    return None, db_type
            else:
                namespace = st.session_state.selected_bid_no

            print("Using namespace:", namespace)
            self.vector_processor.namespace = namespace
            result = self.vector_processor.process(query)

            formatted_response = self.vector_processor.response(query, result)

            return formatted_response, db_type


def create_streamlit_app():
    st.title("Advanced RAG Query System")

    # 환경 변수 설정
    if "OPENAI_API_KEY" not in os.environ:
        openai_api_key = st.sidebar.text_input("OpenAI API Key", type="password")
        if openai_api_key:
            os.environ["OPENAI_API_KEY"] = openai_api_key
        else:
            st.error("OpenAI API 키를 입력해주세요!")
            return

    # 세션 상태 초기화
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "selected_bid_no" not in st.session_state:
        st.session_state.selected_bid_no = None
    if "candidates" not in st.session_state:
        st.session_state.candidates = []
    if "rag_app" not in st.session_state:
        st.session_state.rag_app = RAGApp()
    if "namespace_finder" not in st.session_state:
        st.session_state.namespace_finder = NamespaceFinder()
    if "current_response" not in st.session_state:
        st.session_state.current_response = None

    # 사이드바 설정
    with st.sidebar:
        st.markdown("### System Info")
        st.markdown("- Query Router: LLM based")
        st.markdown("- RDB: PostgreSQL with Langchain")
        st.markdown("- Vector DB: Pinecone with Langchain")

        # 선택된 공고 정보 표시
        if st.session_state.selected_bid_no:
            st.markdown("### 선택된 공고")
            last_selected = st.session_state.get("last_selected")
            if last_selected:
                st.markdown(f"**공고명**: {last_selected['bid_notice_nm']}")
                st.markdown(f"**공고번호**: {last_selected['bid_notice_no']}")
                if st.button("공고 선택 초기화"):
                    st.session_state.selected_bid_no = None
                    st.session_state.candidates = []
                    st.session_state.current_response = None
                    st.session_state.last_selected = None
                    st.rerun()

    # 모든 메시지 표시
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

            # 사용자 메시지 다음에 선택지 표시
            if (
                message == st.session_state.messages[-1]
                and message["role"] == "user"
                and not st.session_state.selected_bid_no
            ):

                # 공고 검색 및 선택지 표시
                st.session_state.namespace_finder.find_namespace(message["content"])
                if st.session_state.selected_bid_no:
                    st.session_state.messages.append(
                        {
                            "role": "system",
                            "content": f"공고번호: {st.session_state.selected_bid_no}",
                        }
                    )
                    st.rerun()

    # 쿼리 입력
    input_placeholder = (
        "질문을 입력하세요"
        if st.session_state.selected_bid_no
        else "검색할 공고의 키워드를 입력하세요"
    )

    if prompt := st.chat_input(input_placeholder):
        # 사용자 입력 표시
        st.session_state.messages.append({"role": "user", "content": prompt})

        # 먼저 쿼리 타입 확인 (이 부분을 밖으로 뺌)
        response_stream, db_type = st.session_state.rag_app.process_query(prompt)

        # RDB 쿼리이거나 공고가 선택된 경우에만 답변 생성
        if db_type == "rdb" or st.session_state.selected_bid_no:
            try:
                with st.chat_message("assistant"):
                    if db_type == "rdb":
                        message_placeholder = st.empty()
                        full_response = []
                        for chunk in response_stream:
                            content = (
                                chunk.content
                                if hasattr(chunk, "content")
                                else str(chunk)
                            )
                            full_response.append(content)
                            message_placeholder.markdown("".join(full_response) + "▌")
                        final_response = "".join(full_response)
                        message_placeholder.markdown(final_response)
                    else:  # vector DB case
                        message_placeholder = st.empty()
                        full_response = []
                        for chunk in response_stream:
                            content = (
                                chunk.content
                                if hasattr(chunk, "content")
                                else str(chunk)
                            )
                            full_response.append(content)
                            message_placeholder.markdown("".join(full_response) + "▌")
                        final_response = "".join(full_response)
                        message_placeholder.markdown(final_response)

                    st.session_state.messages.append(
                        {"role": "assistant", "content": final_response}
                    )
            except Exception as e:
                error_message = f"쿼리 처리 중 오류가 발생했습니다: {str(e)}"
                st.error(error_message)
                st.session_state.messages.append(
                    {"role": "assistant", "content": error_message}
                )
        else:
            st.warning("Vector 검색을 위해서는 먼저 공고를 선택해주세요!")
        st.rerun()


if __name__ == "__main__":
    from logging_langsmith import langsmith

    langsmith("나라장터 챗봇")
    create_streamlit_app()
