#!/usr/bin/env python3
"""
arXiv HTML 크롤러 - Attention Is All You Need 논문 구조 분석
섹션별로 인용 문장과 컨텍스트를 추출하여 JSON으로 저장
"""

import requests
import json
import re
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import os

class ArxivHTMLCrawler:
    def __init__(self, arxiv_id: str = "1706.03762v7"):
        self.arxiv_id = arxiv_id
        self.base_url = f"https://arxiv.org/html/{arxiv_id}"
        self.headers = {
            'User-Agent': 'RefNavi/1.0 (academic research tool)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }
    
    def fetch_html(self) -> BeautifulSoup:
        """arXiv HTML 페이지를 가져와서 BeautifulSoup 객체로 반환"""
        print(f"🔍 arXiv HTML 페이지 요청: {self.base_url}")
        
        response = requests.get(self.base_url, headers=self.headers, timeout=30)
        
        if response.status_code == 200:
            print(f"✅ HTML 페이지 성공적으로 가져옴 (크기: {len(response.content)} bytes)")
            return BeautifulSoup(response.content, 'html.parser')
        else:
            raise Exception(f"❌ HTML 요청 실패: {response.status_code}")
    
    def extract_sections(self, soup: BeautifulSoup) -> List[Dict]:
        """문서의 모든 섹션과 서브섹션을 추출"""
        print("📖 섹션 구조 분석 중...")
        
        sections = []
        
        # 섹션과 서브섹션 제목 찾기
        section_titles = soup.find_all(['h2', 'h3', 'h4'], 
                                      class_=lambda x: x and ('ltx_title_section' in x or 'ltx_title_subsection' in x))
        
        print(f"🎯 발견된 섹션/서브섹션 제목: {len(section_titles)}개")
        
        # 섹션 번호별로 그룹화하여 subsection이 있으면 section은 제외하지만 계층 정보는 보존
        section_groups = {}
        section_hierarchy = {}  # 부모 섹션 정보 저장
        
        for i, title_elem in enumerate(section_titles):
            section_text = title_elem.get_text(strip=True)
            class_list = title_elem.get('class', [])
            
            # 섹션 타입 판별
            if 'ltx_title_section' in class_list:
                section_type = 'section'
            elif 'ltx_title_subsection' in class_list:
                section_type = 'subsection'
            else:
                continue
            
            # 섹션 번호 추출
            section_match = re.match(r'^(\d+(?:\.\d+)*)', section_text)
            if section_match:
                section_number = section_match.group(1)
                base_section_number = section_number.split('.')[0]  # 기본 섹션 번호 (예: "3.1" -> "3")
                
                if base_section_number not in section_groups:
                    section_groups[base_section_number] = {'sections': [], 'subsections': []}
                
                section_info = {
                    'index': i,
                    'element': title_elem,
                    'section_number': section_number,
                    'section_title': section_text.replace(section_number, '').strip(),
                    'full_title': section_text,
                    'section_type': section_type
                }
                
                if section_type == 'section':
                    section_groups[base_section_number]['sections'].append(section_info)
                    # 부모 섹션 정보 저장
                    section_hierarchy[base_section_number] = {
                        'parent_section_number': section_number,
                        'parent_section_title': section_text.replace(section_number, '').strip(),
                        'parent_full_title': section_text
                    }
                else:
                    section_groups[base_section_number]['subsections'].append(section_info)
        
        # subsection이 있으면 해당 section은 제외하고 subsection만 포함하되, 부모 정보 추가
        for base_num, group in section_groups.items():
            if group['subsections']:
                # subsection이 있으면 subsection만 추가하되 부모 정보 포함
                parent_info = section_hierarchy.get(base_num, {})
                for subsection in group['subsections']:
                    # 부모 섹션 정보 추가
                    subsection['parent_section'] = parent_info
                sections.extend(group['subsections'])
                print(f"  📁 섹션 {base_num}: subsection만 처리 ({len(group['subsections'])}개) - 부모: {parent_info.get('parent_full_title', 'Unknown')}")
            else:
                # subsection이 없으면 section 추가
                sections.extend(group['sections'])
                print(f"  📄 섹션 {base_num}: section 처리 ({len(group['sections'])}개)")
        
        # 인덱스 순으로 정렬
        sections.sort(key=lambda x: x['index'])
        
        for i, section in enumerate(sections):
            parent_info = section.get('parent_section', {})
            if parent_info:
                print(f"  {i+1}. [{section['section_type']}] {parent_info.get('parent_full_title', '')} > {section['full_title']}")
            else:
                print(f"  {i+1}. [{section['section_type']}] {section['full_title']}")
        
        return sections
    
    def extract_section_content(self, section_elem, next_section_elem=None) -> Dict:
        """특정 섹션의 내용과 인용 정보를 추출"""
        
        # 섹션 시작 요소부터 다음 섹션 시작 전까지의 모든 내용 수집
        content_elements = []
        current_elem = section_elem
        
        # 현재 섹션 요소의 부모를 찾아서 더 넓은 범위로 탐색
        parent_elem = section_elem.parent
        if parent_elem:
            # 부모 내의 모든 자식 요소를 순회
            found_start = False
            for child in parent_elem.children:
                if hasattr(child, 'name') and child.name:
                    # 현재 섹션 제목을 찾았으면 다음 요소들부터 수집
                    if child == section_elem:
                        found_start = True
                        continue
                    
                    # 다음 섹션 제목이 나오면 중단
                    if found_start and next_section_elem and child == next_section_elem:
                        break
                    
                    # 다른 섹션/서브섹션 제목이 나오면 중단
                    if found_start and child.name in ['h2', 'h3', 'h4']:
                        class_list = child.get('class', [])
                        if any('ltx_title' in cls for cls in class_list):
                            break
                    
                    # 수집 시작된 후라면 내용 요소 추가
                    if found_start:
                        content_elements.append(child)
        
        # 텍스트 내용 추출 - 더 포괄적으로
        full_text = ""
        paragraphs = []
        table_contexts = []  # 표 관련 정보 저장
        
        for elem in content_elements:
            # 텍스트가 포함된 모든 요소에서 내용 추출
            elem_text = elem.get_text(strip=True) if hasattr(elem, 'get_text') else str(elem).strip()
            
            # 표(table) 요소 특별 처리
            if elem.name == 'table' or (hasattr(elem, 'find') and elem.find('table')):
                table_text = elem.get_text(strip=True)
                if table_text and len(table_text) > 20:
                    # 표 캡션 찾기
                    caption = ""
                    caption_elem = elem.find('caption') or elem.find_previous('caption') or elem.find_next('caption')
                    if caption_elem:
                        caption = caption_elem.get_text(strip=True)
                    
                    table_contexts.append({
                        "table_text": table_text,
                        "caption": caption,
                        "citations": re.findall(r'\[(\d+(?:,\s*\d+)*)\]', table_text)
                    })
                    
                    paragraphs.append(f"[TABLE] {caption}: {table_text}")
                    full_text += f"[TABLE] {caption}: {table_text} "
            
            elif elem_text and len(elem_text) > 10:  # 의미있는 텍스트만
                # 특정 태그들은 개별 문단으로 처리
                if elem.name in ['p', 'div', 'section', 'article']:
                    paragraphs.append(elem_text)
                    full_text += elem_text + " "
                # 기타 요소들도 텍스트가 있으면 포함
                elif elem_text not in full_text:  # 중복 방지
                    paragraphs.append(elem_text)
                    full_text += elem_text + " "
        
        # 문단이 비어있다면 전체 텍스트를 하나의 문단으로 처리
        if not paragraphs and full_text.strip():
            paragraphs = [full_text.strip()]
        
        # 인용 분석
        all_citations = set()
        citation_sentences = []
        
        for paragraph_text in paragraphs:
            # 문장 분리
            sentences = re.split(r'[.!?]+\s+', paragraph_text)
            
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) < 10:  # 너무 짧은 문장 제외
                    continue
                    
                # 여러 인용 패턴을 모두 찾기
                citation_pattern = r'\[(\d+(?:,\s*\d+)*)\]'
                citations_in_sentence = re.findall(citation_pattern, sentence)
                
                if citations_in_sentence:
                    # 각 인용 그룹을 개별 번호로 분리
                    all_citation_numbers = []
                    for citation_group in citations_in_sentence:
                        # 쉼표로 구분된 인용 번호들 분리
                        citation_numbers = [num.strip() for num in citation_group.split(',')]
                        all_citation_numbers.extend(citation_numbers)
                    
                    # 중복 제거하면서 순서 유지
                    unique_citations = []
                    for num in all_citation_numbers:
                        if num not in unique_citations:
                            unique_citations.append(num)
                    
                    if unique_citations:
                        # 문맥 유형 판별 (표, 그림, 일반 텍스트)
                        context_type = "text"
                        context_info = {}
                        
                        # 표 컨텍스트 감지
                        if any(keyword in sentence.lower() for keyword in ["table", "training cost", "bleu", "model", "baseline"]):
                            context_type = "table"
                            # 주변 텍스트에서 표 제목이나 설명 찾기
                            for para in paragraphs:
                                if "table" in para.lower() and any(str(cite) in para for cite in unique_citations):
                                    table_match = re.search(r'table\s*\d+[:\.]?\s*([^.]+)', para.lower())
                                    if table_match:
                                        context_info["table_caption"] = table_match.group(1).strip()
                                        break
                        
                        # 그림/Figure 컨텍스트 감지
                        elif any(keyword in sentence.lower() for keyword in ["figure", "fig", "shown in", "depicted"]):
                            context_type = "figure"
                            figure_match = re.search(r'figure\s*\d+', sentence.lower())
                            if figure_match:
                                context_info["figure_reference"] = figure_match.group(0)
                        
                        # 수식 컨텍스트 감지
                        elif any(symbol in sentence for symbol in ["\\", "equation", "formula", "=", "≡"]):
                            context_type = "equation"
                        
                        citation_sentences.append({
                            "sentence": sentence,
                            "citation_numbers": unique_citations,
                            "full_paragraph": paragraph_text,
                            "context_type": context_type,
                            "context_info": context_info
                        })
                        
                        # 전체 인용 목록에 추가
                        for citation_num in unique_citations:
                            all_citations.add(citation_num)
        
        # 중복 제거된 인용 번호들
        unique_citations_list = sorted(list(all_citations), key=lambda x: int(x) if x.isdigit() else float('inf'))
        
        print(f"    ✅ 섹션 완료: {len(unique_citations_list)}개 고유 인용, {len(citation_sentences)}개 인용 문장")
        if len(paragraphs) == 0:
            print(f"    ⚠️ 경고: 이 섹션에서 문단을 찾을 수 없음")
            print(f"    📝 수집된 요소: {len(content_elements)}개")
        
        return {
            'paragraphs': paragraphs,
            'full_text': full_text.strip(),
            'citations': unique_citations_list,
            'citation_sentences': citation_sentences,
            'total_citations': len(unique_citations_list),
            'total_citation_instances': len(citation_sentences),
            'table_contexts': table_contexts
        }
    
    def extract_full_document(self) -> Dict:
        """전체 문서를 섹션별로 분석"""
        print("🎯 전체 문서 분석 시작")
        
        soup = self.fetch_html()
        sections = self.extract_sections(soup)
        
        all_sections_data = []
        total_citations = set()
        total_citation_instances = []
        
        for i, section in enumerate(sections):
            print(f"\n📖 섹션 {i+1}/{len(sections)} 처리 중: {section['full_title']}")
            
            # 다음 섹션 찾기
            next_section_elem = None
            if i + 1 < len(sections):
                next_section_elem = sections[i + 1]['element']
            
            # 섹션 내용 추출
            content = self.extract_section_content(section['element'], next_section_elem)
            
            section_data = {
                'section_info': {
                    'section_number': section['section_number'],
                    'section_title': section['section_title'],
                    'full_title': section['full_title'],
                    'section_type': section['section_type'],
                    'parent_section': section.get('parent_section', None)
                },
                'content': content
            }
            
            all_sections_data.append(section_data)
            
            # 전체 통계 누적
            total_citations.update(content['citations'])
            total_citation_instances.extend(content['citation_sentences'])
            
            print(f"  ✅ 섹션 완료: {content['total_citations']}개 고유 인용, {content['total_citation_instances']}개 인용 문장")
        
        # 전체 텍스트 합치기
        all_text = " ".join([section['content']['full_text'] for section in all_sections_data])
        all_paragraphs = []
        for section in all_sections_data:
            all_paragraphs.extend(section['content']['paragraphs'])
        
        result = {
            'arxiv_id': self.arxiv_id,
            'document_info': {
                'total_sections': len(all_sections_data),
                'total_paragraphs': len(all_paragraphs),
                'total_word_count': len(all_text.split()),
                'unique_citations': len(total_citations),
                'total_citation_instances': len(total_citation_instances)
            },
            'sections': all_sections_data,
            'global_summary': {
                'all_citations': sorted(list(total_citations), key=lambda x: int(x) if x.isdigit() else 999),
                'all_citation_sentences': total_citation_instances,
                'full_document_text': all_text
            }
        }
        
        print(f"\n🎉 전체 문서 분석 완료!")
        print(f"  📖 총 섹션: {result['document_info']['total_sections']}개")
        print(f"  📄 총 문단: {result['document_info']['total_paragraphs']}개")
        print(f"  📊 고유 인용: {result['document_info']['unique_citations']}개")
        print(f"  🎯 인용 인스턴스: {result['document_info']['total_citation_instances']}개")
        
        return result
    
    def save_to_json(self, data: Dict, filename: str = "full_document_analysis.json"):
        """결과를 JSON 파일로 저장"""
        filepath = os.path.join(os.path.dirname(__file__), filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"💾 결과 저장: {filepath}")
        return filepath

def main():
    """메인 실행 함수"""
    print("🚀 arXiv HTML 크롤링 시작 - 전체 문서 분석")
    print("="*60)
    
    crawler = ArxivHTMLCrawler()
    
    try:
        # 전체 문서 분석
        full_doc_data = crawler.extract_full_document()
        
        # JSON 파일로 저장
        crawler.save_to_json(full_doc_data)
        
        # 주요 결과 출력
        print("\n📋 전체 문서 분석 결과:")
        print(f"  📖 총 섹션: {full_doc_data['document_info']['total_sections']}")
        print(f"  📄 총 문단: {full_doc_data['document_info']['total_paragraphs']}")
        print(f"  📝 총 단어: {full_doc_data['document_info']['total_word_count']}")
        print(f"  📊 고유 인용 논문: {full_doc_data['document_info']['unique_citations']}개")
        print(f"  🎯 총 인용 인스턴스: {full_doc_data['document_info']['total_citation_instances']}개")
        
        print(f"\n📚 인용된 논문 번호들: {full_doc_data['global_summary']['all_citations']}")
        
        print("\n📖 섹션별 요약:")
        for i, section in enumerate(full_doc_data['sections'], 1):
            info = section['section_info']
            content = section['content']
            print(f"  {i}. [{info['section_type']}] {info['full_title']}")
            print(f"     - 인용: {content['total_citations']}개, 인용문장: {content['total_citation_instances']}개")
        
        print(f"\n✅ 전체 문서 분석 완료! full_document_analysis.json 파일을 확인하세요.")
        
    except Exception as e:
        print(f"오류: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 