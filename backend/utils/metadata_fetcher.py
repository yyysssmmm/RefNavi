import os
import json
import time
import requests
import unicodedata
from typing import Dict, List, Optional
from difflib import SequenceMatcher

# ============================== #
#       유틸 함수 정의          #
# ============================== #

def normalize_title(title: str) -> str:
    title = unicodedata.normalize("NFKC", title)
    title = title.lower().strip()
    title = title.replace("’", "'").replace("‘", "'")
    title = title.replace("“", '"').replace("”", '"')
    title = title.replace("–", "-").replace("—", "-")
    return ' '.join(title.split())

def similarity(a, b):
    return SequenceMatcher(None, normalize_title(a), normalize_title(b)).ratio()

def load_cache(cache_dir: str, key: str) -> Optional[Dict]:
    path = os.path.join(cache_dir, f"{key}.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def save_cache(cache_dir: str, key: str, data: Dict) -> None:
    os.makedirs(cache_dir, exist_ok=True)
    path = os.path.join(cache_dir, f"{key}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def is_metadata_aligned(best_meta: Dict, ref_meta: Dict) -> bool:
    """메타데이터 정합성 검증"""
    # 연도 비교 (오차 ±1 허용)
    year_match = (
        "year" not in ref_meta or
        best_meta.get("year") is None or
        abs(best_meta.get("year", 0) - ref_meta.get("year", 0)) <= 1
    )
    # 저자 이름 중 하나 이상 포함 여부
    ref_authors = [normalize_title(a) for a in ref_meta.get("authors", [])]
    best_authors = [normalize_title(a["name"]) for a in best_meta.get("authors", [])]
    author_match = any(a in best_authors for a in ref_authors) if ref_authors else True

    return year_match and author_match

# ============================== #
#       OpenAlex API 호출       #
# ============================== #

# 🔁 OpenAlex abstract 재구성
def reconstruct_abstract(index: Dict[str, List[int]]) -> str:
    if not index:
        return ""
    tokens = ["" for _ in range(max(i for v in index.values() for i in v) + 1)]
    for word, positions in index.items():
        for pos in positions:
            tokens[pos] = word
    return " ".join(tokens)

def search_openalex_metadata(title: str, ref_meta: Dict, cache_dir: str) -> Optional[Dict]:

    norm_title = normalize_title(title)
    cached = load_cache(cache_dir, norm_title)
    if cached:
        return cached

    try:
        url = "https://api.openalex.org/works"
        params = {"search": norm_title, "per-page": 5}
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        results = response.json().get("results", [])

        if results:
            best = max(results, key=lambda r: similarity(r.get("title", ""), title))
            sim_score = similarity(best.get("title", ""), title)

            print(sim_score)
            print(normalize_title(best.get("title", "")))
            print(norm_title)

            if sim_score == 1 or (sim_score > 0.5 and is_metadata_aligned(best, ref_meta)):
                result = {
                    "title": best.get("title"),
                    "abstract": reconstruct_abstract(best.get("abstract_inverted_index")),
                    "doi": best.get("doi"),
                    "year": best.get("publication_year"),
                    "authors": [a['author']['display_name'] for a in best.get("authorships", [])],
                    "citation_count": best.get("cited_by_count"),
                    "source": "openalex"
                }
                save_cache(cache_dir, norm_title, result)
                return result

    except Exception as e:
        print(f"❌ OpenAlex 예외 발생: {e}")
    return None

# ============================== #
#  Semantic Scholar API 호출    #
# ============================== #

def search_semanticscholar_metadata(title: str, ref_meta: Dict, cache_dir: str, max_retries: int = 3) -> Optional[Dict]:
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    norm_title = normalize_title(title)

    cached = load_cache(cache_dir, norm_title)
    if cached:
        return cached

    backoff = 2

    for attempt in range(max_retries):
        try:
            params = {
                "query": norm_title,
                "limit": 5,
                "fields": "title,abstract,year,authors,citationCount,externalIds"
            }
            headers = {"User-Agent": "RefNavi/1.0"}
            response = requests.get(url, params=params, headers=headers, timeout=20)

            if response.status_code == 429:
                print(f"⚠️ Rate limit 발생. {backoff}초 후 재시도...")
                time.sleep(backoff)
                backoff *= 2
                continue

            response.raise_for_status()
            data = response.json()

            if data.get("data"):
                # best = max(data["data"], key=lambda x: similarity(x.get("title", ""), title))
                best = data["data"][0]
                sim_score = similarity(best.get("title", ""), title)

                print(sim_score)
                print(normalize_title(best.get("title", "")))
                print(norm_title)

                if sim_score == 1 or (sim_score > 0.5 and is_metadata_aligned(best, ref_meta)):
                    result = {
                        "title": best.get("title"),
                        "abstract": best.get("abstract"),
                        "doi": best.get("externalIds", {}).get("DOI"),
                        "year": best.get("year"),
                        "authors": [a["name"] for a in best.get("authors", [])],
                        "citation_count": best.get("citationCount", 0),
                        "source": "semantic scholar"
                    }
                    save_cache(cache_dir, norm_title, result)
                    return result


        except Exception as e:
            print(f"❌ Semantic Scholar 예외 발생: {e}")
            break

    return None

# ============================== #
#     통합 메타데이터 검색     #
# ============================== #

def enrich_metadata_with_fallback(pdf_metadata_path: str, save_path: str, cache_dir: str) -> None:
    with open(pdf_metadata_path, "r", encoding="utf-8") as f:
        base_metadata = json.load(f)

    references = base_metadata.get("references", [])
    enriched_refs = []

    total = len(references)
    for i, ref in enumerate(references, start=1):
        title = ref.get("ref_title", "").strip()
        print(f"[{i}/{total}] 🔎 제목: {title}")
        if not title:
            print("⚠️ 제목 없음 → 스킵")
            enriched_refs.append(ref)
            continue

        metadata = search_openalex_metadata(title, ref, cache_dir)
        if metadata:
            ref.update(metadata)
            print(f"    ✅ 메타데이터 추출 성공 → 출처: OpenAlex")
        
        else:
            metadata = search_semanticscholar_metadata(title, ref, cache_dir)
            if metadata:
                ref.update(metadata)
                print(f"    ✅ 메타데이터 추출 성공 → 출처: Semantic Scholar")
                time.sleep(2)

            else:
                metadata = {
                    "title": "",
                    "abstract": "",
                    "doi": "",
                    "year": None,
                    "authors": [],
                    "citation_count": 0,
                    "source": "none"
                }
                ref.update(metadata)
                print(f"    ❌ 메타데이터 추출 실패")

        enriched_refs.append(ref)

    base_metadata["references"] = enriched_refs

    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(base_metadata, f, ensure_ascii=False, indent=2)

    print(f"\n📁 최종 메타데이터 저장 완료 → {save_path}")

# ============================== #
#             실행              #
# ============================== #

if __name__ == "__main__":
    enrich_metadata_with_fallback("transformer_metadata.json", "integrated_metadata.json", ".cache")
