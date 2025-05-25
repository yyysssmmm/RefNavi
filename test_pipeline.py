# 📁 파일: backend/test_pipeline.py

from backend.utils.pdf_parser import extract_references_from_pdf
from backend.utils.abstract_fetcher import fetch_abstract_from_reference
from backend.vectorstore.store_builder import add_abstract
import time
import re

# ✅ 멀티라인 reference 병합 함수

def merge_multiline_references(lines: list[str]) -> list[str]:
    refs = []
    current = ""
    for line in lines:
        if re.match(r"^\[\d+\]", line):  # [1], [2], ... 으로 시작
            if current:
                refs.append(current.strip())
            current = line
        else:
            current += " " + line
    if current:
        refs.append(current.strip())
    return refs

# ✅ 통합 실행 파이프라인 함수

def run_pipeline(pdf_path: str):
    print(f"\n🚀 PDF로부터 reference 추출 시작: {pdf_path}\n")
    lines = extract_references_from_pdf(pdf_path)
    refs = merge_multiline_references(lines)
    print(f"📄 총 {len(refs)}개 reference 병합 완료\n")

    for i, ref in enumerate(refs[:10]):  # 상위 10개만 테스트
        print(f"🔍 [{i+1}/{len(refs)}] 검색 중: {ref[:80]}...")
        info = fetch_abstract_from_reference(ref)
        if info and info.get("abstract"):
            add_abstract(info["title"], info["abstract"], id=f"ref_{i}")
        else:
            print("⚠️ abstract 없음 or 검색 실패")
        time.sleep(1.2)  # rate limit 회피용 대기

if __name__ == "__main__":
    run_pipeline("transformer.pdf")