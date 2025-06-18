import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from fastapi import HTTPException, APIRouter
from pydantic import BaseModel
from graphdb.hybrid_qa_strict import hybrid_qa
from vectorstore.qa_chain import run_qa_chain

base_dir = os.path.join(os.path.dirname(__file__), "..")
VECTOR_DB_DIR = os.path.join(base_dir, "utils/metadata/chroma_db")

router = APIRouter()

# ✅ 요청 형식
class QueryRequest(BaseModel):
    query: str
    top_k: int = 3
    return_sources: bool = False
    mode: str = "hybrid"

class Source(BaseModel):
    title: str | None = None
    year: int | None = None
    authors: list[str] | None = None
    summary: str | None = None

# ✅ 응답 형식
class QueryResponse(BaseModel):
    answer: str
    sources: list[Source]

# ✅ 메인 엔드포인트
@router.post("/query", response_model=QueryResponse)
def query_endpoint(request: QueryRequest):
    try:
        print(f"📥 받은 쿼리: {request.query}")
        print(f"🔁 반환할 소스 포함 여부: {request.return_sources}")
        print(f"🧩 QA 모드: {request.mode}")

        if request.mode == "vector-only":
            answer, source_docs = run_qa_chain(
                query=request.query,
                k=request.top_k,
                VECTOR_DB_DIR=VECTOR_DB_DIR,
                return_sources=True
            )
        else:  # hybrid (기본)
            answer, source_docs = hybrid_qa(
                question=request.query,
                k=request.top_k,
                vector_db_dir=VECTOR_DB_DIR,
                return_sources=request.return_sources
            )

        sources = []
        if request.return_sources:
            for doc in source_docs:
                try:
                    authors = doc.metadata.get("authors", "")
                    if isinstance(authors, str):
                        authors = [a.strip() for a in authors.split(",") if a.strip()]
                    elif not isinstance(authors, list):
                        authors = []

                    sources.append({
                        "title": doc.metadata.get("title", "제목 없음"),
                        "year": doc.metadata.get("year"),
                        "authors": authors,
                        "summary": doc.page_content[:300] + "..."
                    })
                except Exception as e:
                    print("⚠️ 소스 포맷 에러:", e)
                    sources.append({
                        "title": "Unknown",
                        "authors": [],
                        "summary": str(doc)[:300]
                    })

        return {"answer": answer, "sources": sources}

    except Exception as e:
        print(f"❌ 에러 발생: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


# ✅ 로컬 테스트용
if __name__ == "__main__":
    import uvicorn
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router)
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
