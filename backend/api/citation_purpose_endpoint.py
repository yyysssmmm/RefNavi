import os
import json
import logging
from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import httpx
from dotenv import load_dotenv

# 로깅 설정
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# .env 파일 로드
load_dotenv()

router = APIRouter()

class CitationPurposeRequest(BaseModel):
    citation_number: int
    local_context: list[str]
    all_contexts: list[str]
    abstract: str
    full_text: str

async def analyze_with_perplexity(
    citation_number: int,
    local_context: List[str],
    all_contexts: List[str],
    abstract: str,
    full_text: str
) -> str:
    try:
        # Perplexity API 키 확인
        api_key = os.getenv("PERPLEXITY_API_KEY")
        if not api_key:
            raise ValueError("PERPLEXITY_API_KEY is not set in environment variables")

        # 프롬프트 구성
        prompt = f"""You are an expert in academic paper analysis. Analyze the purpose of citation [{citation_number}] in the paper.

Citation Information:
- Citation Number: [{citation_number}]
- Local Context (where the citation appears): {json.dumps(local_context, ensure_ascii=False)}
- All Citation Contexts: {json.dumps(all_contexts, ensure_ascii=False)}
- Cited Paper's Abstract: {abstract}

Please analyze:
1. Why was this paper cited in this specific context?
2. What aspect of the cited paper is being referenced?
3. How does this citation support the author's argument?

Provide a clear and concise analysis in Korean, focusing on the academic significance of this citation."""

        # Perplexity API 호출
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.perplexity.ai/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "sonar-pro",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 1000
                },
                timeout=30.0
            )

            if response.status_code != 200:
                logger.error(f"Perplexity API error: {response.status_code} - {response.text}")
                raise HTTPException(status_code=500, detail=f"Perplexity API error: {response.text}")

            result = response.json()
            return result["choices"][0]["message"]["content"]

    except Exception as e:
        logger.error(f"Error in analyze_with_perplexity: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/get_citation_purpose")
async def get_citation_purpose(request: CitationPurposeRequest):
    try:
        logger.debug(f"Request data: {request.dict()}")
        
        purpose = await analyze_with_perplexity(
            citation_number=request.citation_number,
            local_context=request.local_context,
            all_contexts=request.all_contexts,
            abstract=request.abstract,
            full_text=request.full_text
        )
        
        return JSONResponse(content={"purpose": purpose})
        
    except Exception as e:
        logger.error(f"Error in get_citation_purpose: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to get citation purpose",
                "message": str(e),
                "type": type(e).__name__
            }
        ) 