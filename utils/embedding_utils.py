from langchain_openai import OpenAIEmbeddings
import psycopg2
from psycopg2.extras import RealDictCursor
from config.settings import settings
from processors.keyword_extractor import KeywordExtractor


class EmbeddingManager:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings()
        self.keyword_extractor = KeywordExtractor()
        self.conn = psycopg2.connect(settings.POSTGRES_URI)

    def create_document_text(self, row: dict) -> str:
        """검색에 사용될 텍스트 생성"""
        return f"{row['bid_notice_nm']} {row['ntce_kind_nm']} {row['dminstt_nm']} {row['pub_prcrmnt_clsfc_nm']}"

    async def update_embeddings(self, batch_size: int = 100):
        """임베딩이 없는 레코드들의 임베딩을 생성하여 저장"""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            # 임베딩이 없는 레코드 조회
            cur.execute(
                """
                SELECT
                    id,
                    bid_notice_no,
                    bid_notice_nm,
                    ntce_kind_nm,
                    dminstt_nm,
                    pub_prcrmnt_clsfc_nm
                FROM naramarket_bids
                WHERE content_embedding IS NULL
                LIMIT %s
            """,
                (batch_size,),
            )

            rows = cur.fetchall()

            for row in rows:
                # 텍스트 생성 및 임베딩
                text = self.create_document_text(row)
                embedding = await self.embeddings.aembed_query(text)

                # DB 업데이트
                cur.execute(
                    """
                    UPDATE naramarket_bids
                    SET content_embedding = %s
                    WHERE id = %s
                """,
                    (embedding, row["id"]),
                )

            self.conn.commit()

    def hybrid_search(self, query: str, limit: int = 5):
        """키워드 기반 하이브리드 검색 수행"""
        try:
            # 1. 키워드 추출
            keywords = self.keyword_extractor.extract(query)

            # 2. 추출된 키워드로 임베딩 생성
            query_embedding = self.embeddings.embed_query(" ".join(keywords))

            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                # 3. 하이브리드 검색 쿼리 실행
                cur.execute(
                    """
                    WITH vector_matches AS (
                        SELECT
                            nb.*,
                            (content_embedding <#> %s::vector) * -1 + 1 as vector_similarity
                        FROM naramarket_bids nb
                        WHERE
                            bid_notice_nm ILIKE ANY(%s)
                            OR ntce_kind_nm ILIKE ANY(%s)
                            OR dminstt_nm ILIKE ANY(%s)
                            OR pub_prcrmnt_clsfc_nm ILIKE ANY(%s)
                    )
                    SELECT
                        id,
                        bid_notice_no,
                        bid_notice_nm,
                        ntce_kind_nm,
                        dminstt_nm,
                        pub_prcrmnt_clsfc_nm,
                        vector_similarity as score
                    FROM vector_matches
                    WHERE vector_similarity > 0.6
                    ORDER BY vector_similarity DESC
                    LIMIT %s
                    """,
                    (
                        query_embedding,
                        [f"%{keyword}%" for keyword in keywords],
                        [f"%{keyword}%" for keyword in keywords],
                        [f"%{keyword}%" for keyword in keywords],
                        [f"%{keyword}%" for keyword in keywords],
                        limit,
                    ),
                )

                results = cur.fetchall()
                return {
                    "results": list(results),
                    "keywords": keywords,
                    "total_count": len(results),
                }

        except Exception as e:
            print(f"검색 중 오류 발생: {str(e)}")
            return {
                "results": [],
                "keywords": keywords if "keywords" in locals() else [],
                "error": str(e),
            }

    def close(self):
        self.conn.close()
