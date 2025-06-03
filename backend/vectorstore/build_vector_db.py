import os
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from .loader import load_metadata_as_documents

# ✅ 설정값
JSON_PATH = "../utils/integrated_metadata.json"  # 입력 메타데이터 위치
VECTOR_DB_DIR = "chroma_db"                      # 벡터 DB 저장 경로

import shutil

if os.path.exists(VECTOR_DB_DIR):
    shutil.rmtree(VECTOR_DB_DIR)  # 기존 DB 삭제


def build_vector_db(json_path: str = JSON_PATH, persist_dir: str = VECTOR_DB_DIR) -> Chroma:
    """
    - JSONL에서 문서 로드 → 임베딩 → Chroma 벡터 DB 생성 및 저장
    - 생성된 Chroma 인스턴스를 반환
    """
    # 1. 문서 로딩
    print("📄 문서 로딩 중...")
    documents = load_metadata_as_documents(json_path)
    print(f"✅ 총 {len(documents)}개 문서 로드 완료")

    # 2. 임베딩 모델 로딩
    print("🧠 HuggingFace 임베딩 모델 로딩 중...")
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    # 3. 벡터 DB 생성
    print("📦 Chroma 벡터 DB 생성 중...")
    vector_db = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory=persist_dir
    )
    # vector_db.persist()
    print(f"✅ 벡터 DB 저장 완료 → '{persist_dir}/'")
    return vector_db

# ✅ 단독 실행 시 테스트
if __name__ == "__main__":
    print("🚀 벡터 DB 생성 시작...")
    db = build_vector_db()

    # 🔍 저장된 DB에서 간단히 검색 테스트
    print("\n🔎 유사도 검색 테스트 (Query = 'Neural machine translation') ...")
    retriever = db.as_retriever()
    results = db.similarity_search_with_score("Neural machine translation", k=5)

    # ✅ 유사도 점수 기준 내림차순 정렬
    results_sorted = sorted(results, key=lambda x: x[1], reverse=True)

    print(f"✅ 관련 문서 {len(results_sorted)}개 검색됨:")
    for i, (doc, score) in enumerate(results_sorted, 1):
        print(f"\n--- 결과 {i} ---")
        print(f"🔹 유사도 점수: {score:.4f}")
        print(f"🔹 제목: {doc.metadata.get('title')}")
        print(f"🔹 요약: {doc.page_content[:300]}...")

