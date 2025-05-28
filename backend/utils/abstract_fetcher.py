# 📁 파일: backend/utils/abstract_fetcher.py

import requests
import os
from dotenv import load_dotenv
import re

load_dotenv()

S2_API_KEY = os.getenv("S2_API_KEY")
USE_FALLBACK = not S2_API_KEY

# ✅ reference string을 간단히 정제해서 검색에 쓸 query 생성
def simplify_reference(ref: str) -> str:
    ref = re.sub(r"\[[0-9]+\]", "", ref)              # [1], [2] 제거
    ref = re.sub(r"[^\w\s]", "", ref)                  # 특수문자 제거
    words = ref.split()
    keywords = [w for w in words if len(w) > 2]
    return " ".join(keywords[:10])  # 상위 10단어만 사용

# ✅ Semantic Scholar API 또는 fallback 모드로 abstract 검색
def fetch_abstract_from_reference(ref_string: str) -> dict:
    if not ref_string.strip():
        return {}

    query = simplify_reference(ref_string)

    if USE_FALLBACK:
        print("⚠️ S2_API_KEY 없음: fallback 모드 사용 중")
        url = "https://api.semanticscholar.org/graph/v1/paper/search"
        headers = {"Accept": "application/json"}
        params = {
            "query": query,
            "fields": "title,abstract,authors,year,externalIds",
            "limit": 3
        }
    else:
        url = "https://api.semanticscholar.org/graph/v1/paper/search"
        headers = {
            "x-api-key": S2_API_KEY,
            "Accept": "application/json"
        }
        params = {
            "query": query,
            "fields": "title,abstract,authors,year,externalIds",
            "limit": 3
        }

    try:
        res = requests.get(url, headers=headers, params=params)
        if res.status_code != 200:
            print(f"❌ 요청 실패 ({res.status_code}): {res.text}")
            return {}

        items = res.json().get("data", [])
        if not items:
            print("⚠️ 검색 결과 없음")
            return {}

        for item in items:
            title = item.get("title", "").lower()
            if "attention" in title and "need" in title:
                return {
                    "title": item.get("title"),
                    "abstract": item.get("abstract", ""),
                    "doi": item.get("externalIds", {}).get("DOI", "")
                }

        item = items[0]
        return {
            "title": item.get("title"),
            "abstract": item.get("abstract", ""),
            "doi": item.get("externalIds", {}).get("DOI", "")
        }

    except Exception as e:
        print(f"❗ 예외 발생: {e}")
        return {}

# ✅ 테스트용 코드
if __name__ == "__main__":
    ref = "[6] Vaswani, A., Shazeer, N., Parmar, N., Uszkoreit, J., Attention Is All You Need. NIPS 2017."
    print(f"\n🔍 검색어: {simplify_reference(ref)}")
    result = fetch_abstract_from_reference(ref)
    print("\n✅ 추출 결과:")
    for k, v in result.items():
        print(f"{k}: {v}")