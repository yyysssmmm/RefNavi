from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys, os

# ✅ 경로 강제 추가 (실행 환경 깨짐 방지용)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.chains.rag_chain import qa_chain  # ← 이전에 만든 LangChain QA 객체

app = FastAPI()

# ✅ CORS (React 연결용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 운영 환경에선 도메인 지정 필요
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/ping")
def ping():
    return {"message": "pong"}

# ✅ 입력 데이터 모델
class QueryRequest(BaseModel):
    question: str

# ✅ 출력 데이터 모델
class QueryResponse(BaseModel):
    answer: str
    sources: list[str]

# ✅ 질의응답 API
@app.post("/query", response_model=QueryResponse)
async def query_api(request: QueryRequest):
    result = qa_chain.invoke(request.question)
    return {
        "answer": result["result"],
        "sources": [
            doc.metadata.get("title", "Unknown") for doc in result["source_documents"]
        ]
    }

from fastapi import File, UploadFile
from backend.utils.pdf_parser import extract_references_from_pdf  # 기존 코드 활용

@app.post("/upload")
async def upload_pdf(pdf: UploadFile = File(...)):
    contents = await pdf.read()

    # 임시 저장
    temp_path = f"temp_{pdf.filename}"
    with open(temp_path, "wb") as f:
        f.write(contents)

    refs = extract_references_from_pdf(temp_path)

    os.remove(temp_path)  # 업로드 파일 삭제
    return {"references": refs}
