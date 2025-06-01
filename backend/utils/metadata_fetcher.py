"""
metadata_fetcher_semanticscholar.py

Description:
    This module fetches paper metadata (title, abstract, DOI, authors, etc.)
    using the Semantic Scholar API, based on reference titles extracted from PDFs.

Background:
    - Originally, metadata was retrieved using the OpenAlex API.
    - However, OpenAlex does not cover all scholarly publications, causing frequent lookup failures.
    - Semantic Scholar was found to have broader coverage and better support for various paper types.
    - This version replaces OpenAlex with Semantic Scholar as the primary metadata provider.

Improvements:
    - Added request throttling (timeouts and backoff) to handle Semantic Scholar's rate limits.
    - Integrated local caching to avoid redundant API calls and reduce load.
    - Fallback logic includes approximate title matching with validation to avoid hallucinated matches.

Author: Sungmin Yang
Last Modified: 2025-06-01
"""

import os
import json
import time
import requests
import unicodedata
from typing import List, Dict, Optional
from difflib import SequenceMatcher

# ============================== #
#       유틸 함수 정의          #
# ============================== #

def normalize_title(title: str) -> str:
    """유사도 비교 및 캐싱을 위한 제목 정규화"""
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
#     Semantic Scholar 검색     #
# ============================== #

def search_semantic_scholar_metadata(title: str, ref_meta: Dict, cache_dir=".cache") -> Dict:
    norm_title = normalize_title(title)
    cached = load_cache(cache_dir, norm_title)
    if cached:
        return cached

    try:
        url = "https://api.semanticscholar.org/graph/v1/paper/search"
        params = {
            "query": title,
            "limit": 5,
            "fields": "title,abstract,year,authors,citationCount,externalIds"
        }
        headers = {"User-Agent": "RefNavi-MetadataFetcher/1.0"}
        response = requests.get(url, params=params, headers=headers, timeout=20)
        response.raise_for_status()
        data = response.json()

        if data.get("data"):
            best = max(data["data"], key=lambda x: similarity(x.get("title", ""), title))
            sim_score = similarity(best.get("title", ""), title)

            print(sim_score)
            print(normalize_title(best.get("title", "")))
            print(norm_title)

            if sim_score == 1 or (sim_score > 0.6 and is_metadata_aligned(best, ref_meta)):
                result = {
                    "title": best.get("title"),
                    "abstract": best.get("abstract"),
                    "doi": best.get("externalIds", {}).get("DOI"),
                    "year": best.get("year"),
                    "authors": [a["name"] for a in best.get("authors", [])],
                    "citation_count": best.get("citationCount", 0)
                }
                save_cache(cache_dir, norm_title, result)
                return result

    except Exception as e:
        print(f"❌ Semantic Scholar 예외 발생: {e}")

    # ✅ 실패 시에도 동일한 템플릿으로 반환
    fallback_result = {
        "title": "",
        "abstract": "",
        "doi": "",
        "year": None,
        "authors": [],
        "citation_count": 0
    }
    save_cache(cache_dir, norm_title, fallback_result)
    return fallback_result

# ============================== #
#      메타데이터 통합 처리     #
# ============================== #

def enrich_metadata_with_semanticscholar(pdf_metadata_path: str, save_path="final_metadata_ss.json") -> None:
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

        metadata = search_semantic_scholar_metadata(title, ref)
        if metadata:
            ref.update({
                "abstract": metadata.get("abstract", ""),
                "doi": metadata.get("doi", ""),
                "year": metadata.get("year"),
                "authors": metadata.get("authors", []),
                "citation_count": metadata.get("citation_count", 0)
            })
            print(f"    ✅ 메타데이터 추출 성공 → 출처: SemanticScholar")
        else:
            print(f"    ❌ 메타데이터 추출 실패")

        enriched_refs.append(ref)
        time.sleep(2)

    base_metadata["references"] = enriched_refs

    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(base_metadata, f, ensure_ascii=False, indent=2)

    print(f"\n📁 최종 메타데이터 저장 완료 → {save_path}")

# ============================== #
#             실행              #
# ============================== #

if __name__ == "__main__":
    enrich_metadata_with_semanticscholar("transformer_metadata.json", "integrated_metadata.json")
