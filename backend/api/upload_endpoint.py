import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

import json
from fastapi import APIRouter, UploadFile, File
from utils.pdf_parser import process_pdf
from utils.metadata_fetcher import enrich_metadata_with_fallback
from vectorstore.build_vector_db import build_vector_db


router = APIRouter()

@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    # 1. PDF 저장
    pdf_filename = file.filename
    base_filename = os.path.splitext(pdf_filename)[0]  # e.g., "transformer"
    
    upload_dir = "uploaded"
    os.makedirs(upload_dir, exist_ok=True)
    pdf_path = os.path.join(upload_dir, pdf_filename)

    with open(pdf_path, "wb") as f:
        f.write(await file.read())
    
    print(f"✅ PDF 저장 완료: {pdf_path}")

    # 2. PDF 파싱 → metadata json 경로 설정
    metadata_dir = "utils/metadata"
    os.makedirs(metadata_dir, exist_ok=True)

    base_metadata_path = os.path.join(metadata_dir, f"{base_filename}_metadata.json")
    integrated_metadata_path = os.path.join(metadata_dir, "integrated_metadata.json")

    # 3. 파싱 및 메타데이터 추출
    process_pdf(pdf_path, base_metadata_path)
    enrich_metadata_with_fallback(base_metadata_path, integrated_metadata_path, cache_dir=os.path.join(metadata_dir, '.cache'))

    # 4. 통합 메타데이터 로드 및 응답
    with open(integrated_metadata_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 5. vector DB 구축
    build_vector_db(integrated_metadata_path, os.path.join(metadata_dir, "chroma_db"))

    return {
        "title": data.get("title"),
        "abstract_original": data.get("abstract_original"),
        "abstract_llm": data.get("abstract_llm"),
        "references": data.get("references", []),
        "body_fixed": data.get("body_fixed", ""),
    }
