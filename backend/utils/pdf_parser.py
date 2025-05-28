import pdfplumber
from typing import List

# def extract_references_from_pdf(pdf_path: str) -> List[str]:
#     refs = []
#     with pdfplumber.open(pdf_path) as pdf:
#         pages = pdf.pages[-3:]  # 마지막 3페이지만 확인

#         for page in pages:
#             text = page.extract_text()
#             if not text:
#                 continue
#             lines = text.split('\n')

#             for i, line in enumerate(lines):
#                 if "references" in line.lower():
#                     refs += lines[i+1:]
#                     break
#             if refs:
#                 break  # references 찾았으면 반복 중단

#     # 최소 길이 필터링 (ex. 번호 있는 논문만)
#     return [line.strip() for line in refs if len(line.strip()) > 30]

import pdfplumber

def extract_references_from_pdf(pdf_path: str) -> list[str]:
    refs_started = False
    ref_text = ""

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue

            if not refs_started:
                if "References" in text or "REFERENCES" in text:
                    refs_started = True
                    # 레퍼런스 시작 이후부터 저장
                    text = text.split("References")[-1] if "References" in text else text.split("REFERENCES")[-1]
                    ref_text += text + "\n"
            elif refs_started:
                # 레퍼런스 시작 이후 페이지는 전부 누적
                ref_text += text + "\n"

    # 🔧 정규표현식으로 [1] ~ [32] 패턴 추출
    import re
    refs = re.findall(r"\[\d{1,3}\][^\[]+", ref_text)
    return [r.strip() for r in refs]


if __name__ == "__main__":
    from pprint import pprint
    refs = extract_references_from_pdf("transformer.pdf")
    pprint(refs[:5])  # 상위 5개만 출력
