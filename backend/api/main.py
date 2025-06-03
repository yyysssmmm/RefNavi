# backend/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.metadata_endpoint import router as metadata_router
from api.query_endpoint import router as query_router
from api.upload_endpoint import router as upload_router

app = FastAPI()

# ✅ CORS 설정 (여기에서만 설정)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ 모든 라우터 등록
app.include_router(metadata_router, prefix="")
app.include_router(query_router, prefix="")
app.include_router(upload_router, prefix="")