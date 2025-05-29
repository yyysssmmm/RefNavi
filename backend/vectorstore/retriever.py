import os
from typing import List, Tuple
from langchain_core.documents import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# ✅ 설정
VECTOR_DB_DIR = "chroma_db"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

def get_top_k_documents(
    query: str,
    k: int = 5,
    threshold: float = 0.4,
    persist_dir: str = VECTOR_DB_DIR,
    model_name: str = EMBEDDING_MODEL
) -> List[Tuple[Document, float]]:
    """
    쿼리를 입력받아 벡터 DB에서 관련 문서 상위 k개를 점수와 함께 반환.
    threshold 이하 점수는 제거.
    """
    if not os.path.exists(persist_dir):
        raise FileNotFoundError(f"❌ '{persist_dir}' 경로에 DB가 존재하지 않음. 먼저 build_vector_db 실행 필요.")

    # 🔁 임베딩 및 DB 로드
    print("🧠 임베딩 모델 로딩 중...")
    embeddings = HuggingFaceEmbeddings(model_name=model_name)
    print("📦 Chroma DB 로딩 중...")
    db = Chroma(persist_directory=persist_dir, embedding_function=embeddings)

    # 🔍 검색 수행 (score 포함)
    print(f"🔍 유사 문서 검색 중 (query = '{query}')")
    results_with_scores = db.similarity_search_with_score(query, k=k)

    # ✅ 점수 기준 정렬 (높은 점수 우선)
    results_sorted = sorted(results_with_scores, key=lambda x: x[1], reverse=True)

    # 🎯 threshold 필터링
    filtered = [(doc, score) for doc, score in results_sorted if score >= threshold]
    print(f"✅ {len(filtered)}개 문서 반환 (score ≥ {threshold})")
    return filtered

# ✅ 단독 실행 시 테스트
if __name__ == "__main__":
    test_query = "neural machine translation"
    top_k = 5
    threshold = 0.4

    results = get_top_k_documents(test_query, k=top_k, threshold=threshold)

    for i, (doc, score) in enumerate(results, 1):
        print(f"\n--- 결과 {i} (score: {score:.4f}) ---")
        print(f"제목: {doc.metadata.get('title')}")
        print(f"연도: {doc.metadata.get('year')}")
        print(f"저자: {doc.metadata.get('authors')}")
        print(f"요약: {doc.page_content[:300]}...")
