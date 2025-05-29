import os
import json
import time
import requests
from typing import List, Dict, Optional
from difflib import SequenceMatcher

# 🔄 inverted_index에서 abstract 재구성
def reconstruct_abstract(index: Dict[str, List[int]]) -> str:
    if not index:
        return ""
    tokens = ["" for _ in range(max(i for v in index.values() for i in v) + 1)]
    for word, positions in index.items():
        for pos in positions:
            tokens[pos] = word
    return " ".join(tokens)

# 🔎 OpenAlex 기반 논문 메타데이터 검색
def search_openalex_metadata(title: str) -> Optional[Dict]:
    try:
        url = "https://api.openalex.org/works"
        params = {"search": title, "per_page": 5}
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if 'results' in data and data['results']:
            def similarity(a, b):
                return SequenceMatcher(None, a.lower(), b.lower()).ratio()

            best = max(data['results'], key=lambda x: similarity(x.get("title", ""), title))
            if similarity(best.get("title", ""), title) > 0.6:
                return {
                    "title": best.get("title"),
                    "abstract": reconstruct_abstract(best.get("abstract_inverted_index")),
                    "doi": best.get("doi"),
                    "year": best.get("publication_year"),
                    "authors": [a['author']['display_name'] for a in best.get("authorships", [])],
                    "citation_count": best.get("cited_by_count"),
                }
    except Exception as e:
        print(f"❌ OpenAlex 검색 실패: {e}")
    return None

# 🧠 전체 파이프라인: 제목 기반으로 메타데이터 수집
def fetch_metadata_from_titles(refs: List[Dict[str, str]], save_path="openalex_metadata.jsonl") -> List[Dict]:
    results = []
    for i, ref_obj in enumerate(refs, start=1):
        title = ref_obj.get("제목", "").strip()
        if not title:
            print(f"⚠️ 제목 없음 → 스킵 (#{i})")
            continue

        print(f"🔍 [{i}] 제목 검색 중: {title}")
        metadata = search_openalex_metadata(title)
        if metadata:
            results.append(metadata)
            print(f"✅ 검색 성공: {metadata.get('title')}")
        else:
            print(f"❌ 검색 실패: {title}")
        time.sleep(1)  # OpenAlex API 남용 방지

    with open(save_path, "w", encoding="utf-8") as f:
        for item in results:
            formatted = {
                "title": item.get("title", ""),
                "abstract": item.get("abstract", ""),
                "doi": item.get("doi", ""),
                "year": item.get("year", None),
                "authors": item.get("authors", []),
                "citation_count": item.get("citation_count", 0)
            }
            f.write(json.dumps(formatted, ensure_ascii=False) + "\n")

    print(f"\n📁 총 {len(results)}개 논문 메타데이터 저장 완료 → {save_path}")
    return results

# ✅ 단독 실행 테스트용
if __name__ == "__main__":
    from pprint import pprint

    refs = [
        {
            "제목": "Layer normalization",
            "참조내용": "[1] JimmyLeiBa,JamieRyanKiros,andGeoffreyEHinton. Layernormalization. arXivpreprint arXiv:1607.06450,2016."
        },
        {
            "제목": "Neural machine translation by jointly learning to align and translate",
            "참조내용": "[2] DzmitryBahdanau,KyunghyunCho,andYoshuaBengio. Neuralmachinetranslationbyjointly learningtoalignandtranslate. CoRR,abs/1409.0473,2014."
        },
        {
            "제목": "Massive exploration of neural machine translation architectures",
            "참조내용": "[3] DennyBritz,AnnaGoldie,Minh-ThangLuong,andQuocV.Le. Massiveexplorationofneural machinetranslationarchitectures. CoRR,abs/1703.03906,2017."
        },
        {
            "제목": "Long short-term memory-networks for machine reading",
            "참조내용": "[4] JianpengCheng,LiDong,andMirellaLapata. Longshort-termmemory-networksformachine reading. arXivpreprintarXiv:1601.06733,2016."
        },
        {
            "제목": "Learning phrase representations using rnn encoder-decoder for statistical machine translation",
            "참조내용": "[5] KyunghyunCho,BartvanMerrienboer,CaglarGulcehre,FethiBougares,HolgerSchwenk, andYoshuaBengio. Learningphraserepresentationsusingrnnencoder-decoderforstatistical machinetranslation. CoRR,abs/1406.1078,2014."
        }
    ]

    metadata_list = fetch_metadata_from_titles(refs)
    pprint(metadata_list)
