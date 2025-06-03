# backend/api/metadata_endpoint.py

from fastapi import APIRouter
from fastapi.responses import JSONResponse
import os
import json

router = APIRouter()

@router.get("/get_metadata")
def get_metadata():
    metadata_path = "./utils/get_metadata/integrated_metadata.json"
    if not os.path.exists(metadata_path):
        return JSONResponse(status_code=404, content={"error": "Metadata file not found"})

    with open(metadata_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return JSONResponse(content=data)