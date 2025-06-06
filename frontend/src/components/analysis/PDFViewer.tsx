'use client';

import { useState, useEffect } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import type { PDFPageProxy, TextContent, TextItem } from 'pdfjs-dist/types/src/display/api';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';
import { PDFFile } from '@/types';

// PDF.js worker를 로컬 파일로 강제 설정
if (typeof window !== 'undefined') {
  // 기존 설정 무시하고 강제로 로컬 worker 사용
  pdfjs.GlobalWorkerOptions.workerSrc = '/pdfjs/pdf.worker.min.js';
  console.log('PDF.js worker 설정:', pdfjs.GlobalWorkerOptions.workerSrc);
}

interface PDFViewerProps {
  pdfFile: PDFFile;
  isVisible: boolean;
  onCitationClick?: (citationNumber: number) => void;
}

export default function PDFViewer({ pdfFile, isVisible, onCitationClick }: PDFViewerProps) {
  const [numPages, setNumPages] = useState<number>(0);
  const [pageNumber, setPageNumber] = useState<number>(1);
  const [pdfData, setPdfData] = useState<ArrayBuffer | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // PDF 파일을 ArrayBuffer로 변환 (이제 모든 파일이 실제 데이터 보유)
  useEffect(() => {
    if (!pdfFile?.file) return;

    setIsLoading(true);
    console.log('📄 PDF 파일 처리 시작:', {
      name: pdfFile.name,
      size: pdfFile.file.size,
      type: pdfFile.file.type
    });
    
    const reader = new FileReader();
    reader.onload = (e) => {
      const result = e.target?.result;
      if (result instanceof ArrayBuffer) {
        setPdfData(result);
        setIsLoading(false);
        console.log('✅ PDF ArrayBuffer 변환 완료:', result.byteLength, 'bytes');
      }
    };
    
    reader.onerror = (e) => {
      console.error('❌ PDF 파일 읽기 실패:', e);
      setIsLoading(false);
    };
    
    reader.readAsArrayBuffer(pdfFile.file);
  }, [pdfFile]);

  // PDF 로드 성공 시
  function onDocumentLoadSuccess({ numPages }: { numPages: number }) {
    setNumPages(numPages);
    console.log('PDF 로드 성공:', numPages, '페이지');
  }

  // PDF 로드 실패 시
  function onDocumentLoadError(error: Error) {
    console.error('❌ PDF 로드 실패:', error);
    console.error('Worker 설정:', pdfjs.GlobalWorkerOptions.workerSrc);
    console.error('PDF 파일 정보:', {
      name: pdfFile.name,
      size: pdfFile.file.size,
      type: pdfFile.file.type
    });
  }

  // 페이지 로드 성공 시 - 인용 번호 클릭 가능하게 만들기
  function onPageLoadSuccess(page?: PDFPageProxy) {
    if (!onCitationClick) return;

    console.log('페이지 로드 완료, 인용 번호 스캔 시작...');

    // PDF.js의 getTextContent로 텍스트 추출해서 콘솔에 출력
    if (page && typeof page.getTextContent === 'function') {
      page.getTextContent().then((textContent: TextContent) => {
        // TextItem만 추출
        const allText = textContent.items
          .filter((item): item is TextItem => 'str' in item && 'fontName' in item)
          .map((item) => item.str)
          .join(' ');
        console.log('[PDF 전체 텍스트]', allText);
        
        // 각 span의 정확한 내용을 디버깅
        console.log('[PDF 텍스트 스팬 상세]', textContent.items
          .filter((item): item is TextItem => 'str' in item && 'fontName' in item)
          .map((item) => ({
            text: item.str,
            hasSpace: item.str.includes(' '),
            length: item.str.length
          })));
      });
    }

    // 텍스트 레이어가 완전히 렌더링될 때까지 대기
    const checkTextLayer = () => {
      const textElements = Array.from(document.querySelectorAll('.react-pdf__Page__textContent span'))
        .filter(el => el.textContent?.trim() !== ''); // 공백만 있는 span 제외
      
      if (textElements.length === 0) {
        setTimeout(checkTextLayer, 100); // 100ms 후 다시 시도
        return;
      }

      console.log('텍스트 요소 개수:', textElements.length);
      let citationCount = 0;

      // 연속된 span들을 하나의 텍스트로 결합하여 처리
      let combinedText = '';
      let combinedElements: HTMLElement[] = [];
      
      for (let i = 0; i < textElements.length; i++) {
        const el = textElements[i] as HTMLElement;
        const text = el.textContent?.trim() || '';
        if (!text) continue; // 공백만 있는 경우 건너뛰기
        
        // 현재 span이 숫자만 포함하고 있고, 이전 span이 '['로 끝나고, 다음 span이 ']'로 시작하는 경우
        if (/^\d+$/.test(text) && 
            i > 0 && textElements[i-1].textContent?.trim().endsWith('[') && 
            i < textElements.length - 1 && textElements[i+1].textContent?.trim().startsWith(']')) {
          
          const number = parseInt(text, 10);
          el.style.color = '#4f46e5';
          el.style.cursor = 'pointer';
          el.style.textDecoration = 'underline';
          el.style.fontWeight = 'bold';
          el.style.borderRadius = '2px';
          el.style.padding = '1px 2px';
          el.onclick = (e) => {
            e.preventDefault();
            e.stopPropagation();
            if (onCitationClick) onCitationClick(number);
          };
          el.onmouseenter = () => {
            el.style.backgroundColor = 'rgba(79, 70, 229, 0.1)';
          };
          el.onmouseleave = () => {
            el.style.backgroundColor = 'transparent';
          };
          citationCount++;
          i += 1; // ']' span 건너뛰기
          continue;
        }

        // 일반 텍스트 처리
        combinedText += text;
        combinedElements.push(el);

        // 공백이나 문장 부호로 끝나는 경우에만 처리
        if (text.endsWith(' ') || text.endsWith('.') || text.endsWith(',') || text.endsWith(';')) {
          // [숫자] 또는 [숫자, 숫자, ...] 패턴 찾기
          const matches = [...combinedText.matchAll(/\[(\d+(?:,\s*\d+)*)\]/g)];
          if (matches.length > 0) {
            matches.forEach(match => {
              const numbers = match[1].split(',').map(n => n.trim());
              const startIndex = combinedText.indexOf(match[0]);
              
              // 해당 범위의 span들 찾기
              let currentLength = 0;
              for (let j = 0; j < combinedElements.length; j++) {
                const spanText = combinedElements[j].textContent?.trim() || '';
                if (!spanText) continue; // 공백만 있는 경우 건너뛰기
                
                const spanLength = spanText.length;
                if (currentLength <= startIndex && startIndex < currentLength + spanLength) {
                  // 인용 번호가 포함된 span 찾음
                  const el = combinedElements[j] as HTMLElement;
                  const originalText = el.textContent?.trim() || '';
                  
                  // 각 숫자를 클릭 가능한 span으로 대체
                  let replaced = originalText;
                  numbers.forEach(number => {
                    const numStr = number.trim();
                    if (replaced.includes(numStr)) {
                      replaced = replaced.replace(
                        numStr,
                        `<span style="color:#4f46e5;cursor:pointer;text-decoration:underline;font-weight:bold;border-radius:2px;padding:1px 2px;" onclick="event.preventDefault();event.stopPropagation();window.dispatchEvent(new CustomEvent('citationClick',{detail:${numStr}}))">${numStr}</span>`
                      );
                    }
                  });
                  
                  if (replaced !== originalText) {
                    el.innerHTML = replaced;
                    citationCount += numbers.length;
                  }
                  break;
                }
                currentLength += spanLength;
              }
            });
          }
          
          // 버퍼 초기화
          combinedText = '';
          combinedElements = [];
        }
      }

      // 클릭 이벤트 위임(전역)
      window.addEventListener('citationClick', ((e: Event) => {
        const customEvent = e as CustomEvent<number>;
        if (onCitationClick) onCitationClick(customEvent.detail);
      }) as EventListener);

      console.log(`총 ${citationCount}개의 인용 번호를 클릭 가능하게 만들었습니다.`);
    };

    // 텍스트 레이어 체크 시작
    setTimeout(checkTextLayer, 500);
  }

  if (!isVisible) return null;

  return (
    <div style={{ 
      height: '100%', 
      display: 'flex', 
      flexDirection: 'column',
      background: '#f8fafc',
      borderRadius: 'clamp(6px, 1vw, 10px)',
      border: '1px solid #e5e7eb',
      overflow: 'hidden'
    }}>
      {/* 간단한 페이지 네비게이션 */}
      <div style={{
        padding: 'clamp(0.5rem, 1vh, 0.75rem)',
        background: 'white',
        borderBottom: '1px solid #e5e7eb',
        textAlign: 'center',
        fontSize: 'clamp(0.75rem, 1.5vw, 0.875rem)',
        color: '#64748b'
      }}>
        페이지 {pageNumber} / {numPages || '...'}
        {numPages > 1 && (
          <div style={{ marginTop: '0.5rem', display: 'flex', justifyContent: 'center', gap: '0.5rem' }}>
            <button
              onClick={() => setPageNumber(Math.max(1, pageNumber - 1))}
              disabled={pageNumber <= 1}
              style={{
                padding: '0.25rem 0.5rem',
                border: '1px solid #e5e7eb',
                borderRadius: '4px',
                background: pageNumber <= 1 ? '#f8fafc' : 'white',
                cursor: pageNumber <= 1 ? 'not-allowed' : 'pointer'
              }}
            >
              이전
            </button>
            <button
              onClick={() => setPageNumber(Math.min(numPages, pageNumber + 1))}
              disabled={pageNumber >= numPages}
              style={{
                padding: '0.25rem 0.5rem',
                border: '1px solid #e5e7eb',
                borderRadius: '4px',
                background: pageNumber >= numPages ? '#f8fafc' : 'white',
                cursor: pageNumber >= numPages ? 'not-allowed' : 'pointer'
              }}
            >
              다음
            </button>
          </div>
        )}
      </div>

      {/* PDF 콘텐츠 */}
      <div style={{ 
        flex: 1,
        overflow: 'auto',
        padding: '1rem',
        display: 'flex',
        justifyContent: 'center',
        background: '#f8fafc'
      }}>
        {isLoading ? (
          <div style={{ textAlign: 'center', padding: '2rem', color: '#64748b' }}>
            <div style={{ marginBottom: '1rem' }}>⏳</div>
            <div>PDF 파일 처리 중...</div>
            <div style={{ fontSize: '0.75rem', marginTop: '0.5rem' }}>
              {pdfFile.name}
            </div>
          </div>
        ) : pdfData ? (
          <Document
            file={pdfData}
            onLoadSuccess={onDocumentLoadSuccess}
            onLoadError={onDocumentLoadError}
            loading={
              <div style={{ textAlign: 'center', padding: '2rem', color: '#64748b' }}>
                <div style={{ marginBottom: '1rem' }}>📄</div>
                <div>PDF 렌더링 중...</div>
              </div>
            }
            error={
              <div style={{ textAlign: 'center', padding: '2rem', color: '#ef4444' }}>
                <div style={{ marginBottom: '1rem' }}>❌</div>
                <div>PDF 로드 실패</div>
                <div style={{ fontSize: '0.75rem', marginTop: '0.5rem', color: '#64748b' }}>
                  파일을 다시 업로드해주세요
                </div>
              </div>
            }
          >
            <Page
              pageNumber={pageNumber}
              onLoadSuccess={onPageLoadSuccess}
              renderTextLayer={true}
              renderAnnotationLayer={false}
              width={Math.min(800, window.innerWidth * 0.8)}
            />
          </Document>
        ) : (
          <div style={{ textAlign: 'center', padding: '2rem', color: '#ef4444' }}>
            <div style={{ marginBottom: '1rem' }}>❌</div>
            <div>PDF 파일을 읽을 수 없습니다</div>
          </div>
        )}
      </div>
    </div>
  );
} 