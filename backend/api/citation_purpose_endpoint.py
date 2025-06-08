from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

router = APIRouter()

class CitationPurposeRequest(BaseModel):
    citation_number: int
    local_context: list[str]
    all_contexts: list[str]
    abstract: str
    full_text: str

@router.post("/get_citation_purpose")
def get_citation_purpose(request: CitationPurposeRequest):
    # TODO: Replace with actual LLM logic
    dummy_purpose = "This citation is used to support the main argument."
    return JSONResponse(content={"purpose": dummy_purpose}) 