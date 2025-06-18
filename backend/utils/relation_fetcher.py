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

    Your task is to classify the relationship between the citing paper and each of its references based on the citation context, the citing abstract, and the referenced paper's abstract.

    You must select one or more of the following standardized relation labels.  
    Use **multiple labels if the reference serves multiple purposes**.  
    Try to ensure that all available labels are represented at least once in the overall output.  
    If a relation label is **even weakly implied** or **partially applicable**, you **must include it** in the prediction.  
    Aim to **extract as many relevant relations as possible** for each reference.

    ---

    ### ✅ Relation Labels

    1. **has background on**  
    - Reference paper provides basic theory or prior findings for the citing paper.  
    - Typically found in: *Introduction, Related Work, Motivation*

    2. **use method of**  
    - The citing paper uses or adapts a technique, dataset, or tool from the reference.  
    - Typically found in: *Methodology, Evaluation, Results*

    3. **is motivated by**  
    - The citing paper is inspired or justified by the reference.  
    - Typically found in: *Introduction*

    4. **compares or contrasts with**  
    - The citing paper compares or contrasts its approach or results with the reference.  
    - Typically found in: *Related Work, Results, Discussion*

    5. **extend idea of**  
    - The citing paper builds upon, generalizes, or adapts the core idea of the reference.  
    - Typically found in: *Methodology, Conclusion, Discussion*

    ---

    Note: `citation_contexts` describes how the cited paper is referenced and used in the citing paper, and is considered a property of the **cited paper**.

    
    ### 🧠 INSTRUCTION:

    You MUST predict relations for **every single reference** provided in the CITED REFERENCES section.
    Even if the context is ambiguous or weak, make the **best effort** to assign at least one label.
    Never skip any reference.


    Return a JSON list in the following format:
    [
    {{
        "ref_number": 1,
        "ref_title": "Reference Title",
        "relations": ["use method of", "extend idea of"]
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

    
    Return a **complete and valid JSON list**.
    Do not truncate the output. Do not skip references.
    Ensure that every reference listed in CITED REFERENCES appears in the output.

    ---

    ### 💡 FEW-SHOT EXAMPLES

    Example 1:
    Citing abstract:  
    "We enhance GraphSAGE by adding attention modules and benchmark against GCN and GAT."

    Citation contexts:  
    - "We extend GraphSAGE [5] using attention-weighted message passing."  
    - "Compared to GCN and GAT, our model achieves better generalization."

    Reference abstract:  
    "[5] GraphSAGE introduces an inductive learning framework with neighborhood aggregation."

    Prediction:

    json
    {{
    "ref_number": 5,
    "ref_title": "GraphSAGE",
    "relations": ["extend idea of", "use method of", "compares or contrasts with"]
    }}

    Example 2:
    Citation contexts:

    "We directly reuse the learning rate schedule of [3] and apply their regularization technique."

    "Our baseline model configuration is based on their implementation."

    Reference abstract:
    "[3] proposes a training setup with learning rate warm-up and regularization."

    Prediction:

    json
    {{
    "ref_number": 3,
    "ref_title": "Warmup & Regularization Setup",
    "relations": ["use method of"]
    }}

    Example 3:
    Citation contexts:

    "The idea of addressing imbalance introduced by [7] inspired our formulation."

    "We propose a solution to the issues discussed in their work."

    Reference abstract:
    "[7] identifies label imbalance issues in object detection and proposes focal loss."

    Prediction:

    json
    {{
    "ref_number": 7,
    "ref_title": "Focal Loss",
    "relations": ["is motivated by", "has background on"]
    }}

    Example 4:
    Citation contexts:

    "We compare our model against their results shown in [12]."

    "Their architecture serves as our benchmark in all tables."

    Reference abstract:
    "[12] introduces an attention-based dual encoder network."

    Prediction:

    json
    {{
    "ref_number": 12,
    "ref_title": "Dual Encoder Network",
    "relations": ["compares or contrasts with", "use method of"]
    }}

    Example 5:
    Citation contexts:

    "We adapt the transformer memory module from [9] and propose a fusion mechanism."

    "Our work builds on their sequence modeling approach."

    Reference abstract:
    "[9] proposes a memory-based attention model for long sequences."

    Prediction:

    json
    {{
    "ref_number": 9,
    "ref_title": "Memory Attention Model",
    "relations": ["extend idea of", "use method of"]
    }}

    Example 6:
    Citation contexts:

    "We tackle the same limitations outlined in [8], particularly in the multi-domain setting."

    "Our method addresses the gap left open in their approach."

    Reference abstract:
    "[8] highlights challenges in adapting models to new domains without supervision."

    Prediction:

    json
    {{
    "ref_number": 8,
    "ref_title": "Domain Adaptation Challenges",
    "relations": ["is motivated by", "has background on"]
    }}

    Example 7:
    Citation contexts:

    "Unlike [11], we propose a unified module that generalizes their local attention block."

    "We extend their approach by enabling cross-layer interactions."

    Reference abstract:
    "[11] introduces a local attention mechanism for modeling intra-sentence dependencies."

    Prediction:

    json
    {{
    "ref_number": 11,
    "ref_title": "Local Attention",
    "relations": ["extend idea of", "use method of"]
    }}


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
