# backend/api/metadata_endpoint.py

from fastapi import APIRouter
from fastapi.responses import JSONResponse
import os
import json
import logging

# 로깅 설정
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("")
def get_metadata():
    try:
        # 절대 경로 설정
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
        metadata_path = os.path.join(base_dir, "utils", "metadata", "integrated_metadata.json")
        
        logger.debug(f"Looking for metadata file at: {metadata_path}")
        
        if not os.path.exists(metadata_path):
            logger.error(f"Metadata file not found at: {metadata_path}")
            return JSONResponse(
                status_code=404,
                content={"error": f"Metadata file not found at: {metadata_path}"}
            )

        with open(metadata_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            logger.debug(f"Successfully loaded metadata with {len(data.get('references', []))} references")
            return JSONResponse(content=data)
            
    except Exception as e:
        logger.error(f"Error loading metadata: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Internal server error: {str(e)}"}
        )