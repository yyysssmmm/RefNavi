import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from vectorstore.qa_chain import run_qa_chain

app = FastAPI()

# ✅ CORS 설정 (프론트엔드 로컬 개발용 포함)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ 요청 형식 정의
class QueryRequest(BaseModel):
    query: str
    top_k: int = 3

# ✅ 응답 형식 정의
class QueryResponse(BaseModel):
    answer: str
    sources: list

# ✅ 메인 엔드포인트
@app.post("/query", response_model=QueryResponse)

def query_endpoint(request: QueryRequest):
    try:
        print(f"📥 받은 쿼리: {request.query}")
        
        answer, source_docs = run_qa_chain(request.query, k=request.top_k, VECTOR_DB_DIR="../vectorstore/chroma_db", return_sources=True)

        sources = [
            {
                "title": doc.metadata.get("title"),
                "year": doc.metadata.get("year"),
                "authors": doc.metadata.get("authors"),
                "summary": doc.page_content[:300] + "..."
            }
            for doc in source_docs
        ]

        return QueryResponse(answer=answer, sources=sources)

    except Exception as e:
        print(f"❌ 에러 발생: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

# ✅ 로컬 테스트용
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.query_endpoint:app", host="0.0.0.0", port=8000, reload=True)