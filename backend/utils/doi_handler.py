# TODO: CrossRef API 문제로 DOI 기반 reference 추출 보류 중
# 참고 DOI: 10.1145/3454287.3454785
# 해결 방안: VPN 테스트, 네트워크 변경, 또는 Semantic Scholar로 우회


import requests

def extract_references_from_doi(doi: str):
    url = f"https://api.crossref.org/works/{doi.strip()}"
    headers = {
        "Accept": "application/json",
        "User-Agent": "RefNavi/0.1 (mailto:sheep@example.com)"
    }
    res = requests.get(url, headers=headers)

    if res.status_code != 200:
        print(f"❌ 요청 실패: {res.status_code}")
        print(res.text)
        return []

    data = res.json()
    refs = data.get("message", {}).get("reference", [])
    print(f"✅ {len(refs)}개 reference 추출됨")
    return [r.get("article-title") or r.get("unstructured") or r.get("journal-title") for r in refs if r]


if __name__ == "__main__":
    doi = "10.1145/3454287.3454785"  # 예시용
    print(repr(doi))
    refs = extract_references_from_doi(doi)
    for i, ref in enumerate(refs[:5]):
        print(f"{i+1}. {ref}")
