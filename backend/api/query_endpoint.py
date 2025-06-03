import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from fastapi import HTTPException
from fastapi import APIRouter
from pydantic import BaseModel
from vectorstore.qa_chain import run_qa_chain

router = APIRouter()

# ✅ 요청 형식 정의
class QueryRequest(BaseModel):
    query: str
    top_k: int = 3

class Source(BaseModel):
    title: str | None = None
    year: int | None = None
    authors: list[str] | None = None
    summary: str | None = None

# ✅ 응답 형식 정의
class QueryResponse(BaseModel):
    answer: str
    sources: list[Source]

# ✅ 메인 엔드포인트
@router.post("/query", response_model=QueryResponse)

def query_endpoint(request: QueryRequest):
    try:
        print(f"📥 받은 쿼리: {request.query}")
        
        answer, source_docs = run_qa_chain(request.query, k=request.top_k, VECTOR_DB_DIR="../vectorstore/chroma_db", return_sources=True)

        sources = []
        for doc in source_docs:
            try:
                sources.append({
                    "title": doc.metadata.get("title", "제목 없음"),
                    "year": doc.metadata.get("year"),
                    "authors": doc.metadata.get("authors", []),
                    "summary": doc.page_content[:300] + "..."
                })
            except Exception as e:
                print("⚠️ 소스 포맷 에러:", e)
                sources.append({
                    "title": "Unknown",
                    "summary": str(doc)[:300]
                })

        return {"answer": answer, "sources": sources}

    except Exception as e:
        print(f"❌ 에러 발생: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

# ✅ 로컬 테스트용
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.query_endpoint:app", host="0.0.0.0", port=8000, reload=True)