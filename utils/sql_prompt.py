from datetime import date


def get_schema_info():
    schema = """
    -- 실패한 입찰 정보
    Table: bid_result_fails
        - bid_notice_no (text): 입찰 공고번호
        - openg_rslt_div_nm (text): 개찰 결과 구분명
        - nobid_rsn (text): 유찰 사유

    -- 성공한 입찰 정보
    Table: bid_result_successes
        - bid_notice_no (text): 입찰 공고번호
        - prcbdr_bizno (text): 입찰자 사업자번호
        - prcbdr_nm (text): 입찰자명
        - prcbdr_ceo_nm (text): 입찰자 대표자명
        - bidprc_amt (numeric): 입찰가격금액
        - bidprc_rt (double precision): 입찰가격비율
        - openg_rank (integer): 개찰순위
        - drwt_no1 (text): 추첨번호1
        - drwt_no2 (text): 추첨번호2
        - rmrk (text): 비고
        - bidprc_dt (timestamp): 입찰가격일자
        - openg_rslt_div_nm (text): 개찰 결과 구분명

    -- 나라장터 입찰 정보
    Table: naramarket_bids
        - bid_notice_no (text): 입찰 공고번호
        - bid_notice_nm (text): 입찰 공고명
        - ntce_kind_nm (text): 공고 종류명
        - bid_notice_date (date): 공고 일자
        - ntce_instt_nm (text): 공고기관명
        - dminstt_nm (text): 수요기관명
        - bid_method_nm (text): 입찰 방식명
        - cntrct_cncls_method_nm (text): 계약체결방식명
        - ntce_instt_ofcl_nm (text): 담당자명
        - ntce_instt_ofcl_tel_no (text): 담당자 전화번호
        - ntce_instt_ofcl_email_adrs (text): 담당자 이메일
        - bid_qlfct_rgst_dt (timestamp): 입찰참가자격등록마감일시
        - bid_begin_dt (timestamp): 입찰개시일시
        - bid_close_dt (timestamp): 입찰마감일시
        - openg_dt (timestamp): 개찰일시
        - asign_bdgt_amt (numeric): 배정예산금액
        - presmpt_price (numeric): 추정가격
        - vat (numeric): 부가가치세
        - srvce_div_nm (text): 용역구분명
        - pub_prcrmnt_lrg_clsfc_nm (text): 공공조달대분류명
        - pub_prcrmnt_mid_clsfc_nm (text): 공공조달중분류명
        - pub_prcrmnt_clsfc_nm (text): 공공조달분류명
        - bid_notice_url (text): 입찰공고URL
        - bid_prgs_stat_nm (text): 입찰진행상태명(null, 유찰, 자체 입찰 공고, 개찰 전, 개찰완료, 개찰 미진행, 직찰)
    """
    return schema


def generate_prompt(user_query):
    schema = get_schema_info()
    examples = """
    Example 1: 월별 유찰 건수 분석
    질문: 2023년에 유찰된 입찰 건수를 월별로 보여주세요
    <thought_process>
    1. 필요한 테이블 식별:
        - bid_result_fails: 유찰 정보 확인
        - naramarket_bids: 날짜 정보 확인
    2. 조인 조건:
        - 두 테이블을 bid_notice_no로 연결
    3. 데이터 처리:
        - 2023년 데이터만 필터링
        - 월별로 그룹화하여 카운트
        - 월 순서대로 정렬
    </thought_process>
    <sql>
    SELECT
        EXTRACT(MONTH FROM nb.bid_notice_date) as month,
        COUNT(*) as fail_count
    FROM bid_result_fails brf
    JOIN naramarket_bids nb ON brf.bid_notice_no = nb.bid_notice_no
    WHERE EXTRACT(YEAR FROM nb.bid_notice_date) = 2023
    GROUP BY EXTRACT(MONTH FROM nb.bid_notice_date)
    ORDER BY month;
    </sql>

    Example 2: 입찰 성공 업체 분석
    질문: 입찰 성공 건수가 가장 많은 상위 5개 업체의 평균 입찰가격과 총 낙찰 건수를 보여주세요
    <thought_process>
    1. 필요한 데이터 확인:
        - bid_result_successes 테이블에서 업체 정보와 입찰가격 추출
        - 낙찰은 openg_rank = 1인 경우를 의미
    2. 계산 항목:
        - 업체별 낙찰 건수(openg_rank = 1인 경우의 카운트)
        - 업체별 평균 입찰가격
    3. 데이터 정렬:
        - 낙찰 건수 기준 내림차순
        - 상위 5개 업체만 선택
    </thought_process>
    <sql>
    SELECT
        prcbdr_nm as company_name,
        COUNT(*) as success_count,
        AVG(bidprc_amt) as avg_bid_amount
    FROM bid_result_successes
    WHERE openg_rank = 1
    GROUP BY prcbdr_nm
    ORDER BY success_count DESC
    LIMIT 5;
    </sql>

    Example 3: 고액 예산 기관 분석
    질문: 공고기관별 평균 예산금액이 10억 이상인 기관의 총 공고 건수와 평균 예산을 보여주세요
    <thought_process>
    1. 데이터 소스:
        - naramarket_bids 테이블에서 기관정보와 예산정보 사용
    2. 집계 방법:
        - 기관별로 그룹화
        - 평균 예산 계산
        - 공고 건수 카운트
    3. 필터링:
        - 평균 예산 10억 이상 필터 (HAVING 절 사용)
    4. 정렬:
        - 평균 예산 기준 내림차순
    </thought_process>
    <sql>
    SELECT
        ntce_instt_nm as institution_name,
        COUNT(*) as total_notices,
        AVG(asign_bdgt_amt) as avg_budget
    FROM naramarket_bids
    GROUP BY ntce_instt_nm
    HAVING AVG(asign_bdgt_amt) >= 1000000000
    ORDER BY avg_budget DESC;
    </sql>
    """

    return f"""당신은 PostgreSQL 전문가 AI 어시스턴트입니다.
주어진 데이터베이스 스키마를 기반으로 자연어 질의를 SQL로 변환합니다.
{{table_info}}

오늘 날짜: {date.today()}

데이터베이스 스키마:
{schema}

최대 반환 결과 수: {{top_k}}

다음은 질의 예시와 각각의 사고 과정, SQL 쿼리입니다:
{examples}

다음 질의를 SQL로 변환해주세요:
{{input}}

먼저 <thought_process> 태그 안에 SQL 작성을 위한 사고 과정을 다음과 같은 단계로 설명해주세요:
1. 필요한 테이블과 컬럼 식별
2. 테이블 간 조인 관계 파악
3. 필요한 필터링 조건 설정
4. 필요한 집계/계산 결정
5. 정렬 및 제한 조건 확인

그 다음 <sql> 태그 안에 최종 SQL 쿼리를 작성해주세요.

주의사항:
1. PostgreSQL 문법을 사용합니다
2. 날짜/시간 함수는 EXTRACT()를 사용합니다
3. 테이블 조인 시 명시적 JOIN 구문을 사용합니다
4. 컬럼명은 스키마에 정의된 것만 사용합니다
5. 가능한 명확한 별칭(alias)을 사용합니다
6. 결과의 가독성을 위해 적절한 컬럼명을 지정합니다"""


def generate_prompt_with_number(user_query):
    schema = get_schema_info()
    examples = """
    Example 1: 입찰 참여자 상세 정보
    질문: 모든 입찰 참여자의 순위와 상세 정보를 보여주세요
    <thought_process>
    1. 필요한 테이블 식별:
        - bid_result_successes: 입찰 결과 정보 (순위, 업체정보, 가격정보)
    2. 필터링 조건:
        - bid_notice_no로 특정 공고 선택
    3. 데이터 처리:
        - 업체 관련 정보(업체명, 대표자명)
        - 입찰 관련 정보(순위, 가격, 투찰률)
        - 순위순으로 정렬
    </thought_process>
    <sql>
    SELECT
        openg_rank as rank,
        prcbdr_nm as company_name,
        prcbdr_ceo_nm as ceo_name,
        bidprc_amt as bid_amount,
        bidprc_rt as bid_ratio,
        openg_rslt_div_nm as result_status
    FROM bid_result_successes
    WHERE bid_notice_no = '{{bid_notice_no}}'
    ORDER BY openg_rank;
    </sql>

    Example 2: 공고 개요와 낙찰 정보
    질문: 공고 기본정보와 낙찰 결과를 보여주세요
    <thought_process>
    1. 필요한 테이블과 컬럼:
        - naramarket_bids: 공고 기본정보(공고명, 기관, 예산)
        - bid_result_successes: 낙찰자 정보(rank 1)
    2. 조인 조건:
        - bid_notice_no로 두 테이블 연결
    3. 데이터 추출:
        - 공고 기본정보
        - 낙찰자 정보(rank = 1인 경우)
    </thought_process>
    <sql>
    SELECT
        nb.bid_notice_nm as notice_name,
        nb.ntce_instt_nm as institution_name,
        nb.dminstt_nm as demand_institution,
        nb.asign_bdgt_amt as budget_amount,
        brs.prcbdr_nm as winner_name,
        brs.bidprc_amt as winning_amount,
        brs.bidprc_rt as winning_ratio
    FROM naramarket_bids nb
    LEFT JOIN bid_result_successes brs
        ON nb.bid_notice_no = brs.bid_notice_no
        AND brs.openg_rank = 1
    WHERE nb.bid_notice_no = '{{bid_notice_no}}';
    </sql>

    Example 3: 입찰 진행 현황
    질문: 진행상태와 세부 일정을 보여주세요
    <thought_process>
    1. 데이터 소스:
        - naramarket_bids 테이블의 진행 관련 정보
    2. 필요한 정보:
        - 진행상태(bid_prgs_stat_nm)
        - 입찰/계약 방식
        - 주요 일정들
    3. 필터링:
        - 특정 bid_notice_no만 선택
    </thought_process>
    <sql>
    SELECT
        bid_prgs_stat_nm as status,
        bid_method_nm as bid_method,
        cntrct_cncls_method_nm as contract_method,
        bid_notice_date as notice_date,
        bid_begin_dt as bid_begin,
        bid_close_dt as bid_close,
        openg_dt as open_date,
        ntce_instt_ofcl_nm as manager_name,
        ntce_instt_ofcl_tel_no as manager_contact
    FROM naramarket_bids
    WHERE bid_notice_no = '{{bid_notice_no}}';
    </sql>
    """

    return f"""당신은 PostgreSQL 전문가 AI 어시스턴트입니다.
선택된 입찰공고({{bid_notice_no}})에 대한 상세 분석을 위해 자연어 질의를 SQL로 변환합니다.
{{table_info}}

오늘 날짜: {date.today()}

데이터베이스 스키마:
{schema}

최대 반환 결과 수: {{top_k}}

다음은 질의 예시와 각각의 사고 과정, SQL 쿼리입니다:
{examples}

다음 질의를 SQL로 변환해주세요:
{{input}}

먼저 <thought_process> 태그 안에 SQL 작성을 위한 사고 과정을 다음과 같은 단계로 설명해주세요:
1. 필요한 테이블과 컬럼 식별
2. 테이블 간 조인 관계 파악
3. 필요한 필터링 조건 설정
4. 필요한 집계/계산 결정
5. 정렬 및 제한 조건 확인

그 다음 <sql> 태그 안에 최종 SQL 쿼리를 작성해주세요.

주의사항:
1. PostgreSQL 문법을 사용합니다
2. 날짜/시간 함수는 EXTRACT()를 사용합니다
3. 테이블 조인 시 명시적 JOIN 구문을 사용합니다
4. 컬럼명은 스키마에 정의된 것만 사용합니다
5. 가능한 명확한 별칭(alias)을 사용합니다
6. 결과의 가독성을 위해 적절한 컬럼명을 지정합니다
7. 항상 선택된 공고번호에 대한 분석만 수행합니다"""
