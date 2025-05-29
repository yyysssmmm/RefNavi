import os
import pdfplumber
import json
from typing import List, Dict
from dotenv import load_dotenv
from openai import OpenAI

# 🔐 Load OpenAI API key from .env
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("❌ OPENAI_API_KEY가 .env에서 불러와지지 않았습니다!")

client = OpenAI(api_key=OPENAI_API_KEY)


def extract_title_and_references_via_llm(pdf_path: str, model_name="gpt-4") -> Dict[str, object]:
    full_text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"

    prompt = f"""
다음은 하나의 논문에서 추출한 전체 텍스트입니다. 이 텍스트를 바탕으로 아래 두 가지 정보를 JSON 형식으로 정리해줘.

1. 논문 제목: 논문 본문에서 유추 가능한 가장 정확한 제목 (ex. 첫 페이지 맨 위나 제목 형식의 큰 글씨 등에서 추정)
2. 참고문헌 목록: "References" 또는 "참고문헌" 섹션에 나오는 각 레퍼런스를 아래 형식으로 리스트로 정리

출력 형식 예시는 다음과 같아:
{{
  "title": "논문 제목",
  "references": [
    {{
      "제목": "각 레퍼런스의 논문 제목 (있다면)",
      "참조내용": "원문에서 발췌한 전체 참고문헌 문장"
    }},
    ...
  ]
}}

주의:
- 레퍼런스 개별 항목들은 줄바꿈이나 번호로 구분되는 것들만 포함
- 제목이 없는 경우 "제목 없음"으로 둬도 괜찮아
- 출력은 반드시 위 JSON 형식을 따라야 해

다음은 논문 텍스트입니다:
-----------------------------
{full_text[-10000:]}
"""

    response = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    try:
        parsed = json.loads(response.choices[0].message.content.strip())
        return parsed
    except Exception as e:
        print("❌ LLM 응답 파싱 실패:", e)
        print("🔎 원본 응답:\n", response.choices[0].message.content)
        return {"title": "", "references": []}


def save_extracted_info(pdf_path: str, extracted: Dict[str, object]):
    base_path = pdf_path.replace(".pdf", "")
    
    # 제목 저장
    title_path = base_path + "_title.txt"
    with open(title_path, "w", encoding="utf-8") as f:
        f.write(extracted.get("title", "제목 없음"))
    print(f"📄 논문 제목 저장 완료: {title_path}")
    
    # 참고문헌 저장
    refs_path = base_path + "_refs.txt"
    with open(refs_path, "w", encoding="utf-8") as f:
        for i, ref in enumerate(extracted.get("references", []), start=1):
            f.write(f"[{i}] 제목: {ref['제목']}\n참조내용: {ref['참조내용']}\n\n")
    print(f"📚 레퍼런스 {len(extracted.get('references', []))}개 저장 완료: {refs_path}")


if __name__ == "__main__":
    pdf_file = "transformer.pdf"
    result = extract_title_and_references_via_llm(pdf_file)

    print("\n🎯 논문 제목:", result.get("title", "없음"))
    print("📚 레퍼런스 개수:", len(result.get("references", [])))
    
    save_extracted_info(pdf_file, result)
