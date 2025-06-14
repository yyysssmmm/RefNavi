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
    exact_citation_sentence: str
    all_contexts: list[str]
    abstract: str
    full_text: str
    ref_title: str

async def analyze_with_perplexity(
    citation_number: int,
    local_context: List[str],
    exact_citation_sentence: str,
    all_contexts: List[str],
    abstract: str,
    full_text: str,
    ref_title: str
) -> str:
    try:
        # Perplexity API 키 확인
        api_key = os.getenv("PERPLEXITY_API_KEY")
        if not api_key:
            raise ValueError("PERPLEXITY_API_KEY is not set in environment variables")

        # 프롬프트 구성
        prompt = f"""당신은 학술 논문 분석 전문가입니다. 다음 정보를 바탕으로 인용의 목적을 간단명료하게 분석해주세요.

인용 정보:
- 인용된 논문 제목: {ref_title}
- 정확한 인용 문장: {exact_citation_sentence}
- 인용 문장의 문맥 (앞뒤 문장): {json.dumps(local_context, ensure_ascii=False)}
- 인용된 논문의 쓰인 다른 문장들: {json.dumps(all_contexts, ensure_ascii=False)}
- 인용된 논문의 초록: {abstract}

다음 두 가지에 초점을 맞춰 1~2가지 이유로 분석해 주세요:
1. 인용 문장에서 어떤 목적(예: 근거 제시, 방법 인용, 배경 설명 등)으로 이 논문이 쓰였는가?
2. 인용 논문의 어떤 구체적 내용이 그 목적에 활용되었는가?

분석은 다음 형식으로 작성해주세요:
[인용 목적] 해당 문장에서 이 인용이 사용된 이유를 1~2문장으로 설명해주세요.
[참조 내용] 인용된 논문의 어떤 개념, 방법, 결과 또는 주장이 문장에 연결되는지를 3~4문장으로 설명해주세요.

분석은 학술적 중요성에 초점을 맞추되, 반드시 간결하게 작성해주세요."""

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
            exact_citation_sentence=request.exact_citation_sentence,
            all_contexts=request.all_contexts,
            abstract=request.abstract,
            full_text=request.full_text,
            ref_title=request.ref_title
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