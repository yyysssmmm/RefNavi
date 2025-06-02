import os
import re
import json
import pdfplumber
from typing import Dict, List
from dotenv import load_dotenv
from openai import OpenAI
import nltk
from nltk import sent_tokenize

nltk.download('punkt')
nltk.download('punkt_tab')

# Load API Key
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY missing in .env")
client = OpenAI(api_key=OPENAI_API_KEY)

# 문장 기반 의미 단위 chunking
def semantic_chunking(text: str, max_chars: int = 6000) -> List[str]:
    sentences = sent_tokenize(text)
    chunks, current_chunk = [], ""

    for sent in sentences:
        if len(current_chunk) + len(sent) + 1 < max_chars:
            current_chunk += " " + sent
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sent
    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks

# 텍스트 블록 추출 함수
def extract_text_blocks(text: str) -> Dict[str, str]:
    # abstract와 references의 위치 찾기
    abstract_match = re.search(r'\babstract\b', text, re.IGNORECASE)
    ref_match = re.search(r'\n\s*(references|bibliography)\s*\n', text, re.IGNORECASE)

    # introduction 키워드 또는 목차 번호 패턴으로 abstract 끝 추정
    intro_patterns = [
        r'\n\s*(1|Ⅰ|I)\.?\s*(introduction)?\s*\n',
        r'\n\s*introduction\s*\n'
    ]
    end_abstract = None
    for pattern in intro_patterns:
        intro_match = re.search(pattern, text[abstract_match.end():], re.IGNORECASE) if abstract_match else None
        if intro_match:
            end_abstract = abstract_match.end() + intro_match.start()
            break
    if not end_abstract:
        end_abstract = abstract_match.end() if abstract_match else 0

    # reference 시작 지점
    start_refs = ref_match.start() if ref_match else len(text)

    # reference 이후 appendix 등으로 끊는 구간
    postfix_patterns = [
        r'\n\s*(appendix|supplementary|acknowledg(e)?ments|about the author|biography)\b'
    ]
    end_refs = len(text)
    for pattern in postfix_patterns:
        match = re.search(pattern, text[start_refs:], re.IGNORECASE)
        if match:
            end_refs = start_refs + match.start()
            break

    # block들 정의
    block1 = text[:end_abstract].strip()
    block2 = text[end_abstract:start_refs].strip()
    block3 = text[start_refs:end_refs].strip()
    block4 = text[end_refs:].strip() if end_refs < len(text) else ""

    return {
        "block1": block1,
        "block2": block2,
        "block3": block3,
        "block4": block4
    }

# LLM 호출 (1단계)
def call_llm_step1(block1: str, block3: str, model="gpt-4"):
    prompt = f"""
[논문 정보 일부]
- 논문 초반부 (제목/저자/abstract 포함): {block1}
- Reference 섹션 전체: {block3}

[당신의 임무]
1. 논문 제목(title)을 간결하게 정제하세요.
2. abstract 내용은 수정하지 말고, 띄어쓰기와 문장 부호, 대소문자, 오탈자만 교정하여 abstract_original로 출력하세요. 절대 요약하거나 의미를 바꾸지 마세요.
3. reference section에서 [1], [2], ... 형식의 reference 번호별로 각 논문의 제목만 추정해 출력하세요.

⚠️ 반드시 JSON 형식으로만 출력하세요. 설명, 주석, 여는 말 없이 JSON만 출력해야 합니다.

[출력 형식 예시]
{{
  "title": "...",
  "abstract_original": "...",
  "references": [
    {{
      "ref_number": "[1]",
      "ref_title": "..."
    }}
  ]
}}
"""
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    return json.loads(response.choices[0].message.content.strip())

# LLM 호출 (2단계 chunk별)
def call_llm_step2_chunk(chunk: str, model="gpt-4") -> Dict:
    prompt = f"""
[논문 본문 일부 chunk]
{chunk}

[당신의 임무]
1. citation_contexts는 [1], [2], ... 형식의 reference 번호가 포함된 문장만 추출하여, 해당 번호별로 리스트로 구성하세요. 여러 문장이 있다면 모두 포함해야 합니다.
2. body_fixed는 본문 내용을 그대로 유지하되, 띄어쓰기, 구두점, 대소문자, 오탈자만 교정하세요. 절대 의미를 바꾸지 마세요.

⚠️ 반드시 JSON 형식으로만 출력하세요. 설명, 주석, 여는 말 없이 JSON만 출력해야 합니다.

[출력 형식 예시]
{{
  "body_fixed": "...",
  "citation_contexts": {{
    "[1]": ["..."],
    "[2]": ["..."]
  }}
}}
"""
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    return json.loads(response.choices[0].message.content.strip())

# 메타데이터 병합 및 저장
def merge_and_save(step1_result, abstract_llm: str, body_fixed_chunks: List[str], citation_contexts: Dict[str, List[str]], pdf_path: str, out_path: str):
    for ref in step1_result.get("references", []):
        ref_number = ref.get("ref_number")
        ref["citation_contexts"] = citation_contexts.get(ref_number, [])

    final_metadata = {
        "title": step1_result.get("title", ""),
        "abstract_original": step1_result.get("abstract_original", ""),
        "abstract_llm": abstract_llm,
        "body_fixed": "\n\n".join(body_fixed_chunks),
        "references": step1_result.get("references", [])
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(final_metadata, f, indent=2, ensure_ascii=False)
    print(f"✅ 메타데이터 저장 완료: {out_path}")

# 전체 실행 함수
def process_pdf(pdf_path: str, out_path: str):
    print(f"\n📂 PDF 처리 시작: {pdf_path}")

    # ✅ 기존 출력 파일이 존재하면 패스
    if os.path.exists(out_path):
        print(f"⚠️ 이미 메타데이터 파일 존재: {out_path} → 처리 생략")
        return

    with pdfplumber.open(pdf_path) as pdf:
        full_text = "\n\n".join(page.extract_text() for page in pdf.pages if page.extract_text())

    blocks = extract_text_blocks(full_text)

    print("🚀 1단계 LLM 호출 중...")
    step1_result = call_llm_step1(blocks["block1"], blocks["block3"])

    print("🧠 요약용 abstract_llm 생성 중...")
    abstract_llm_prompt = f"""다음은 논문 본문입니다. 핵심 내용을 2~3문장으로 요약하세요:
{blocks['block2']}"""
    abstract_llm = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": abstract_llm_prompt}],
        temperature=0
    ).choices[0].message.content.strip()

    print("🚀 2단계 LLM 반복 호출 중...")
    chunks = semantic_chunking(blocks["block2"] + "\n" + blocks["block4"])

    body_fixed_chunks = []
    citation_contexts = {}
    for idx, chunk in enumerate(chunks):
        print(f"  🔍 Chunk {idx+1}/{len(chunks)} 처리 중...")
        result = call_llm_step2_chunk(chunk)
        body_fixed_chunks.append(result.get("body_fixed", ""))
        for ref, ctxs in result.get("citation_contexts", {}).items():
            citation_contexts.setdefault(ref, []).extend(ctxs)

    merge_and_save(step1_result, abstract_llm, body_fixed_chunks, citation_contexts, pdf_path, out_path)

if __name__ == "__main__":
    process_pdf("transformer.pdf", "transformer_metadata.json")
