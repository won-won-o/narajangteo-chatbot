import streamlit as st
from utils.embedding_utils import EmbeddingManager


class NamespaceFinder:
    def __init__(self):
        self.embedding_manager = EmbeddingManager()
        if "selected_bid_no" not in st.session_state:
            st.session_state.selected_bid_no = None
        if "candidates" not in st.session_state:
            st.session_state.candidates = []
        if "search_complete" not in st.session_state:
            st.session_state.search_complete = False

    def find_namespace(self, query: str) -> str:
        # 이미 선택된 공고가 있다면 반환
        if st.session_state.selected_bid_no and st.session_state.search_complete:
            return st.session_state.selected_bid_no

        # 하이브리드 검색으로 후보 찾기
        search_result = self.embedding_manager.hybrid_search(query, limit=5)

        if not search_result["results"]:
            return None

        # 검색 결과를 세션 상태에 저장
        st.session_state.candidates = search_result["results"]

        # 검색에 사용된 키워드 표시
        st.write(f"검색 키워드: {', '.join(search_result['keywords'])}")

        # 사용자에게 확인 (Streamlit UI에 radio 버튼으로 표시)
        st.write("### 찾고 계신 공고가 다음 중 하나인가요?")

        # Radio 버튼용 옵션 생성
        options = []
        for candidate in st.session_state.candidates:
            bid_url = f"https://www.g2b.go.kr:8101/ep/invitation/publish/bidInfoDtl.do?bidno={candidate['bid_notice_no']}"
            option_text = (
                f"{candidate['bid_notice_nm']}\n"
                f"공고번호: [{candidate['bid_notice_no']}]({bid_url})\n"
                f"분류: {candidate['ntce_kind_nm']} | {candidate['pub_prcrmnt_clsfc_nm']}\n"
                f"기관: {candidate['dminstt_nm']}\n"
                f"유사도 점수: {candidate.get('total_score', candidate.get('score', 0)):.3f}"
            )
            options.append(option_text)

        options.append("찾는 공고가 없습니다")

        selected_option = st.radio(
            "공고를 선택해주세요:", options, key=f"radio_{len(options)}"
        )

        # 선택 버튼 추가
        if st.button("선택 완료", key="select_complete"):
            # "찾는 공고가 없습니다" 선택 시
            if selected_option == options[-1]:
                st.warning("다른 키워드로 다시 검색해주세요.")
                st.session_state.search_complete = False
                return None

            # 선택된 공고 찾기
            selected_idx = options.index(selected_option)
            selected_candidate = st.session_state.candidates[selected_idx]

            # 세션 상태 업데이트
            st.session_state.selected_bid_no = selected_candidate["bid_notice_no"]
            st.session_state.last_selected = selected_candidate
            st.session_state.search_complete = True

            st.success(f"선택된 공고번호: {selected_candidate['bid_notice_no']}")
            return selected_candidate["bid_notice_no"]

        return None
