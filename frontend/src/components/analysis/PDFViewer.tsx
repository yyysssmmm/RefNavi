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
  onCitationClick?: (citationNumber: number, contextSentences: string[], exactCitationSentence: string) => void;
}

interface CitationClickEvent extends CustomEvent {
  detail: number;
  extraSpanIdx?: number;
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

      // 문장 단위로 span을 그룹핑
      const sentences: { text: string, spans: HTMLElement[] }[] = [];
      let currentSentence = '';
      let currentSpans: HTMLElement[] = [];
      const sentenceEndRegex = /[.!?]\s*$/;
      textElements.forEach((el, idx) => {
        const t = el.textContent || '';
        currentSentence += t;
        currentSpans.push(el as HTMLElement);
        if (sentenceEndRegex.test(t) || idx === textElements.length - 1) {
          sentences.push({ text: currentSentence, spans: [...currentSpans] });
          currentSentence = '';
          currentSpans = [];
        }
      });

      // 1. 페이지 전체 텍스트 합치기
      const allText = textElements.map(el => el.textContent).join('');

      // 2. [] 쌍 찾기
      const refPattern = /\[(.*?)\]/g;
      let match;
      let citationCount = 0;
      const refRanges: { start: number, end: number, numbers: string[] }[] = [];
      while ((match = refPattern.exec(allText)) !== null) {
        // 3. [] 안의 숫자 추출 (공백, 쉼표 등 무시)
        const numbers = match[1].split(',').map(n => n.replace(/\s/g, '')).filter(Boolean);
        refRanges.push({ start: match.index, end: match.index + match[0].length, numbers });
      }

      // 4. 각 span의 시작/끝 인덱스 기록
      let runningIdx = 0;
      const spanRanges = textElements.map(el => {
        const text = el.textContent || '';
        const start = runningIdx;
        const end = runningIdx + text.length;
        runningIdx = end;
        return { el, start, end, text };
      });

      // 5. 각 reference에 대해 해당하는 span에 스타일/이벤트 부여
      refRanges.forEach(ref => {
        // reference가 걸쳐 있는 span 모두 찾기
        const targetSpans = spanRanges.filter(
          span => !(span.end <= ref.start || span.start >= ref.end)
        );
        // 각 span에서 숫자 또는 숫자가 아닌 부분으로 분리 (정규식)
        targetSpans.forEach(span => {
          let replaced = span.text;
          ref.numbers.forEach(numStr => {
            // 이미 span으로 감싸진 숫자는 제외하고, 숫자만 감쌈
            replaced = replaced.replace(
              new RegExp(`(?<!<span[^>]*?>)${numStr}(?![^<]*?</span>)`, 'g'),
              `<span style="color:#4f46e5;cursor:pointer;text-decoration:underline;padding: 0px 1px;font-weight:bold;border-radius:2px;font-family:'Times New Roman',Times,serif;" data-citation-number="${numStr}" onclick="event.preventDefault();event.stopPropagation();window.dispatchEvent(new CustomEvent('citationClick',{detail:${numStr}, bubbles:true, composed:true, cancelable:true, extraSpanIdx:${spanRanges.findIndex(s => s.el === span.el)}}))">${numStr}</span>`
            );
          });
          if (replaced !== span.text) {
            span.el.innerHTML = replaced;
            citationCount += ref.numbers.length;
          }
        });
      });

      // 클릭 이벤트 위임(전역)
      window.addEventListener('citationClick', ((e: Event) => {
        const customEvent = e as CitationClickEvent;
        const citationNumber = customEvent.detail;
        // 클릭된 span의 인덱스 추출
        let clickedSpanIdx = customEvent.extraSpanIdx;
        if (typeof clickedSpanIdx !== 'number') {
          // fallback: citationNumber가 포함된 첫 span 인덱스
          clickedSpanIdx = spanRanges.findIndex(s => s.text.includes(String(citationNumber)));
        }
        // span이 속한 문장 인덱스 찾기
        const sentenceIdx = sentences.findIndex(sen => sen.spans.some(sp => spanRanges[clickedSpanIdx]?.el === sp));
        // 앞뒤 3문장 추출
        const contextSentences = sentences.slice(Math.max(0, sentenceIdx - 3), sentenceIdx + 4).map(s => s.text);
        // 정확한 인용 문장 추출
        const exactCitationSentence = sentences[sentenceIdx]?.text || '';
        console.log('Context sentences:', contextSentences);
        console.log('Exact citation sentence:', exactCitationSentence);
        if (onCitationClick) onCitationClick(citationNumber, contextSentences, exactCitationSentence);
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
      borderRadius: '1vw',
      border: '1px solid #e5e7eb',
      overflow: 'hidden'
    }}>
      {/* 간단한 페이지 네비게이션 */}
      <div style={{
        padding: '1vh',
        background: 'white',
        borderBottom: '1px solid #e5e7eb',
        textAlign: 'center',
        fontSize: '0.8vw',
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
        background: '#f8fafc',
        fontFamily: `'Times New Roman', Times, serif`
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