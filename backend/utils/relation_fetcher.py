import os
import json
from typing import List, Dict
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path

# ✅ 환경변수 로드 및 OpenAI client 초기화
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# ✅ GPT를 통해 논문 전체 reference 관계 추론 (1회 호출)
def classify_all_relations(metadata: Dict) -> List[Dict]:
    title = metadata.get("title", "")
    abstract_orig = metadata.get("abstract_original", "")
    abstract_llm = metadata.get("abstract_llm", "")
    references = metadata.get("references", [])

    # Prompt 구성
    ref_texts = []
    for ref in references:
        ref_num = ref.get("ref_number", -1)
        ref_title = ref.get("ref_title", "Unknown Title")
        ref_abstract = ref.get("ref_abstract", "")
        contexts = ref.get("citation_contexts", [])
        if not contexts:
            continue
        ctx_text = "\n".join([f"- {ctx}" for ctx in contexts])
        ref_texts.append(
            f"[{ref_num}] Title: {ref_title}\nAbstract: {ref_abstract}\nContexts:\n{ctx_text}"
        )
    
    cited_block = "\n\n".join(ref_texts)

    prompt = f"""
You are a scientific citation relation classifier.

Given the citing paper and a list of references with citation contexts,
classify the relationship between the citing paper and each reference using one or more of the following labels:
["uses", "extends", "compares with", "improves upon", "is motivated by", "provides background", "plans to build upon", "cites"]

If a reference has multiple citation purposes, return all applicable relations.

Return a JSON list in this format:
[
  {{
    "ref_number": 1,
    "ref_title": "Reference Title",
    "relations": ["uses", "extends"]
  }},
  ...
]

CITING PAPER TITLE:
{title}

CITING ABSTRACT (Original):
{abstract_orig}

CITING ABSTRACT (LLM Summary):
{abstract_llm}

CITED REFERENCES:
{cited_block}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        result = response.choices[0].message.content
        return json.loads(result)
    except Exception as e:
        print(f"[Error] LLM 호출 실패: {e}")
        return []

# ✅ triple 리스트 생성: flatten 구조로 변환
def generate_triples(metadata: Dict) -> List[List[str]]:
    refs = {ref["ref_number"]: ref.get("ref_title", "") for ref in metadata.get("references", [])}
    predictions = classify_all_relations(metadata)
    source_title = metadata.get("title", "")

    triples = []
    for pred in predictions:
        ref_num = pred.get("ref_number")
        raw_title = pred.get("ref_title") or refs.get(ref_num, "Unknown Reference")
        relations = pred.get("relations", ["cites"])
        # ✅ ref_num 붙인 제목
        ref_title = f"[{ref_num}] {raw_title}"
        for relation in relations:
            triples.append([source_title, relation, ref_title])
            print(f"[✓] [{ref_num}] {relation} → {raw_title}")
    return triples

# ✅ enriched_metadata 생성
def convert_to_enriched_metadata(integrated_path: str, enriched_path: str):
    if os.path.exists(enriched_path):
        print(f"[⚠] Skipped: {enriched_path} already exists.")
        return

    with open(integrated_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    enriched_metadata = {
        "title": metadata.get("title", ""),
        "abstract_original": metadata.get("abstract_original", ""),
        "abstract_llm": metadata.get("abstract_llm", ""),
        "triples": generate_triples(metadata),
        "references": metadata.get("references", [])
    }

    with open(enriched_path, "w", encoding="utf-8") as f:
        json.dump(enriched_metadata, f, indent=2, ensure_ascii=False)

    print(f"[✓] Enriched metadata saved to: {enriched_path}")

# ✅ CLI 실행 예시
if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent
    integrated_path = base_dir / "metadata" / "integrated_metadata.json"
    enriched_path = base_dir / "metadata" / "enriched_metadata.json"

    convert_to_enriched_metadata(str(integrated_path), str(enriched_path))
