import os
import re
import json
import pdfplumber
from typing import Dict
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY missing in .env")

client = OpenAI(api_key=OPENAI_API_KEY)

def extract_text_from_pdf(pdf_path: str) -> str:
    full_text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"
    return full_text

def extract_reference_section(text: str) -> str:
    lower = text.lower()
    idx = lower.find("references")
    return text[idx:] if idx != -1 else ""

def extract_citation_contexts(text: str) -> Dict[str, list]:
    """
    본문에서 [1], [2], ... 등의 인용 번호가 언급된 문장들을 추출.
    """
    citation_contexts = dict()
    sentences = re.split(r'(?<=[.?!])\s+', text)
    for sent in sentences:
        matches = re.findall(r'\[(\d{1,3})\]', sent)
        for num in matches:
            ref_num = f"[{num}]"
            citation_contexts.setdefault(ref_num, []).append(sent.strip())
    return citation_contexts

def extract_title_and_summary(text_sample: str, model="gpt-4") -> Dict:
    prompt = f"""
다음은 논문 일부입니다. 아래 두 가지 정보를 JSON 형식으로 생성해줘.

{{
  "title": "논문 제목",
  "summary": "논문 요약 (2~3문장)"
}}

본문:
-----------------
{text_sample}
"""

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    try:
        return json.loads(response.choices[0].message.content.strip())
    except Exception as e:
        print("❌ LLM 응답 파싱 실패:", e)
        return {"title": "", "summary": ""}

def extract_ref_titles_from_section(ref_text: str, model="gpt-4") -> Dict[str, str]:
    prompt = f"""
다음은 논문의 References 섹션입니다. 각 참고문헌의 인용번호와 제목만 추론해서 JSON으로 정리해줘.

출력 형식:
{{
  "[1]": "참고문헌 제목",
  "[2]": "참고문헌 제목",
  ...
}}

참고문헌 섹션:
-----------------
{ref_text}
"""

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    try:
        return json.loads(response.choices[0].message.content.strip())
    except Exception as e:
        print("❌ 참고문헌 제목 추론 실패:", e)
        return {}

def build_metadata(text: str, title_summary: Dict, ref_titles: Dict[str, str], citation_contexts: Dict[str, list]) -> Dict:
    references = []
    for ref_number, ref_title in ref_titles.items():
        references.append({
            "ref_number": ref_number,
            "ref_title": ref_title,
            "citation_contexts": citation_contexts.get(ref_number, [])
        })

    return {
        "title": title_summary.get("title", ""),
        "summary": title_summary.get("summary", ""),
        "references": references
    }

def save_metadata(metadata: Dict, pdf_path: str):
    out_path = pdf_path.replace(".pdf", "_metadata.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    print(f"✅ 메타데이터 저장 완료: {out_path}")

def process_pdf(pdf_path: str):
    full_text = extract_text_from_pdf(pdf_path)
    ref_section = extract_reference_section(full_text)
    text_sample = full_text[:2000]

    print("🚀 LLM으로 제목 + 요약 추출 중...")
    title_summary = extract_title_and_summary(text_sample)

    print("📚 참고문헌 섹션에서 제목 추출 중...")
    ref_titles = extract_ref_titles_from_section(ref_section)

    print("🔍 본문에서 citation context 추출 중...")
    citation_contexts = extract_citation_contexts(full_text)

    metadata = build_metadata(full_text, title_summary, ref_titles, citation_contexts)
    save_metadata(metadata, pdf_path)

# 예시 실행
if __name__ == "__main__":
    process_pdf("transformer.pdf")
