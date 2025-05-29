import json
from typing import List
from langchain_core.documents import Document

def load_metadata_as_documents(jsonl_path: str) -> List[Document]:
    """
    OpenAlex 메타데이터 JSONL 파일을 LangChain Document 리스트로 변환.
    - page_content: abstract
    - metadata: title, year, authors, doi, citation_count
    """
    documents = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                data = json.loads(line.strip())
                content = data.get("abstract", "").strip()
                if not content:
                    continue  # abstract가 없으면 스킵

                metadata = {
                    "title": data.get("title", ""),
                    "year": data.get("year", ""),
                    "authors": ", ".join(data.get("authors", [])),
                    "doi": data.get("doi", ""),
                    "citation_count": data.get("citation_count", 0)
                }

                doc = Document(page_content=content, metadata=metadata)
                documents.append(doc)

            except json.JSONDecodeError as e:
                print(f"❌ JSON 디코딩 에러: {e}")
                continue

    return documents


# ✅ 단독 실행 시 테스트
if __name__ == "__main__":
    test_path = "../utils/openalex_metadata.jsonl"  # ← 경로 확인 필요
    docs = load_metadata_as_documents(test_path)

    print(f"\n📄 문서 개수: {len(docs)}개")
    if docs:
        print("\n📌 첫 번째 문서 내용 예시:")
        print(f"제목: {docs[0].metadata.get('title')}")
        print(f"연도: {docs[0].metadata.get('year')}")
        print(f"저자: {docs[0].metadata.get('authors')}")
        print(f"DOI: {docs[0].metadata.get('doi')}")
        print(f"인용 수: {docs[0].metadata.get('citation_count')}")
        print("\n본문 요약:")
        print(docs[0].page_content[:300] + "...")
