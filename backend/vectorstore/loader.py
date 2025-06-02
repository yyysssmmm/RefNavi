import json
from typing import List
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

def load_metadata_as_documents(json_path: str) -> List[Document]:
    """
    통합 메타데이터(JSON) → LangChain Document 리스트로 변환
    - 본문은 chunking 후 각 chunk마다 Document로 저장
    - reference는 하나씩 Document로 저장
    """
    documents = []

    with open(json_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    # ✅ 본문 chunking
    paper_title = metadata.get("title", "").strip()
    abstract_original = metadata.get("abstract_original", "").strip()
    abstract_llm = metadata.get("abstract_llm", "").strip()
    body_text = metadata.get("body_fixed", "").strip()

    # chunking
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    body_chunks = text_splitter.create_documents([body_text])

    for idx, chunk in enumerate(body_chunks):
        chunk.metadata = {
            "source": "original_paper_body",
            "title": paper_title,
            "chunk_id": idx
        }
        documents.append(chunk)

    # ✅ abstract 통합 Document 하나 추가
    full_original_text = f"""[Original Paper]
Title: {paper_title}

Abstract (Original):
{abstract_original}

Abstract (LLM Summary):
{abstract_llm}
"""
    documents.append(Document(
        page_content=full_original_text.strip(),
        metadata={"source": "original paper", "title": paper_title}
    ))

    # ✅ reference 논문 처리
    references = metadata.get("references", [])
    for ref in references:
        title = ref.get("ref_title") or ""
        abstract = ref.get("abstract") or ""
        ref_num = ref.get("ref_number") or ""
        citation_contexts = [ctx for ctx in ref.get("citation_contexts", []) if ctx.strip()]
        citation_text = "\n".join(f"- {ctx}" for ctx in citation_contexts) or "N/A"

        page_content = f"""[Reference Paper]
Title: {title}
Abstract: {abstract}
Citation Contexts:
{citation_text}
"""

        doc_metadata = {
            "ref_num": ref_num,
            "title": title,
            "year": str(ref.get("year") or "unknown"),
            "authors": ", ".join(ref.get("authors", [])) if isinstance(ref.get("authors", []), list) else "-",
            "doi": ref.get("doi") or "",
            "citation_count": int(ref.get("citation_count") or 0),
            "source": "reference paper"
        }

        documents.append(Document(page_content=page_content.strip(), metadata=doc_metadata))

    return documents


# ✅ 단독 실행 테스트
if __name__ == "__main__":
    test_path = "../utils/integrated_metadata.json"
    docs = load_metadata_as_documents(test_path)

    print(f"\n📄 총 문서 개수: {len(docs)}개 (업로드 논문의 본문 chunk + 업로드 논문의 제목 및 abstract + references)")
    print("\n📌 첫 번째 문서 메타데이터:")
    print(f"source: {docs[0].metadata.get('source')}")
    print(f"title: {docs[0].metadata.get('title')}")
    print("\n📄 본문 내용 (앞 500자):")
    print(docs[0].page_content[:500] + "...\n")
