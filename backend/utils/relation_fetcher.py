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

        Your task is to classify the relationship between the citing paper and each of its references based on the citation context, citing abstract, and referenced paper's abstract.

        You must select one or more of the following standardized relation labels.  
        Use **multiple labels if the reference serves multiple purposes**.  
        Aim to include **3~5 labels per reference**, and ensure **every label** is used across all predictions if possible.

        ---

        ### ✅ Relation Labels

        1. **provides background**  
        - Explains basic theory or prior findings.  
        - Found in: *Introduction, Related Work, Motivation*

        2. **describes method**  
        - Describes a method used or modified.  
        - Found in: *Methodology*

        3. **presents result**  
        - Specific numerical or experimental result.  
        - Found in: *Results*

        4. **motivates** 
        - Provides rationale or justification for current work.  
        - Found in: *Introduction*

        5. **is used**  
        - A technique, dataset, or tool is directly used.  
        - Found in: *Motivation, Evaluation, Methodology, Results*

        6. **compares or contrasts with**  
        - Compared in performance or approach.  
        - Found in: *Related Work, Results, Discussion*

        7. **extends**  
        - Builds upon or expands prior work.  
        - Found in: *Motivation, Methodology*

        8. **plans to build upon**  
        - Future work plans to extend or adopt it.  
        - Found in: *Conclusion, Discussion*

        9. **cites**  
        - Generic citation. Use only if no specific label fits.

        ---

        ### 🧠 INSTRUCTION:

        Return a JSON list in the format:
        [
        {{
            "ref_number": 1,
            "ref_title": "Reference Title",
            "relations": ["is used", "extends", "motivates"]
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
        
        ---

        ### 💡 FEW-SHOT EXAMPLES

        Example 1:
        Citing abstract:  
        "We build upon GraphSAGE by introducing edge-wise attention and compare to both GAT and GCN baselines."

        Citation contexts:  
        - "We extend GraphSAGE [5] by replacing mean aggregation with attention-weighted updates."  
        - "Our method outperforms GCN and GAT in semi-supervised settings."

        Reference abstract:  
        "[5] GraphSAGE introduces an inductive framework for learning node embeddings using neighborhood sampling."

        Prediction:
        
    json
        {{
        "ref_number": 5,
        "ref_title": "GraphSAGE",
        "relations": ["extends", "describes method", "compares or contrasts with", "motivates"]
        }}


        
        Example 2:
        Citation contexts:

        "We adopt the architecture described in [3]."

        "In our experiments, we use their configuration as the baseline."

        "This architecture is popular for its performance."

        Reference abstract:
        "[3] introduces a deep convolutional encoder-decoder architecture for segmentation tasks."

        Prediction:
        
    json
        {{
        "ref_number": 3,
        "ref_title": "CNN Segmentation Architecture",
        "relations": ["is used", "describes method", "presents result"]
        }}


        
        Example 3:
        Citation contexts:

        "The motivation for this study stems from the limitation identified in [9]."

        "We aim to address the scalability issues highlighted there."

        "Future work may integrate their distributed processing scheme."

        Reference abstract:
        "[9] investigates bottlenecks in distributed training and proposes partial gradient update schemes."
        
        Prediction:
        
    json
        {{
        "ref_number": 9,
        "ref_title": "Distributed Training Bottlenecks",
        "relations": ["motivates", "provides background", "plans to build upon"]
        }}


        Example 4:
        Citation contexts:

        "We use the training schedule of [7] and their learning rate warmup strategy."

        "Our comparison to their final results is shown in Table 2."

        "They benchmarked multiple optimization strategies."

        Reference abstract:
        "[7] proposes learning rate warm-up for deep networks and presents extensive benchmarks."

        Prediction:
        
    json
        {{
        "ref_number": 7,
        "ref_title": "Warmup Schedules",
        "relations": ["is used", "compares or contrasts with", "presents result"]
        }}

        
        Example 5:
        Citation contexts:

        "Transformer [1] serves as the foundational architecture in our encoder."

        "Their attention mechanism is directly used in our setup."

        "We propose a slight modification and show performance gains."

        "In the future, we plan to extend their cross-attention block."

        Reference abstract:
        "[1] Introduces the Transformer, based entirely on attention mechanisms."

        Prediction:
        
    json
        {{
        "ref_number": 1,
        "ref_title": "Transformer",
        "relations": ["provides background", "is used", "extends", "plans to build upon"]
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
