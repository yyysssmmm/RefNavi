'use client';

import { useState, useEffect } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
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
  function onPageLoadSuccess() {
    if (!onCitationClick) return;

    console.log('페이지 로드 완료, 인용 번호 스캔 시작...');

    // 짧은 지연 후 텍스트 스캔
    setTimeout(() => {
      const textElements = document.querySelectorAll('.react-pdf__Page__textContent span');
      console.log('텍스트 요소 개수:', textElements.length);
      
      let citationCount = 0;
      
      textElements.forEach((element) => {
        const htmlElement = element as HTMLElement;
        const text = htmlElement.textContent || '';
        
        // [숫자] 또는 [숫자, 숫자] 패턴 찾기
        const citationMatch = text.match(/\[(\d+(?:,\s*\d+)*)\]/);
        
        if (citationMatch) {
          citationCount++;
          const numbers = citationMatch[1].split(',').map(n => parseInt(n.trim()));
          
          console.log('인용 번호 발견:', citationMatch[0], '→', numbers);
          
          // 요소를 클릭 가능하게 만들기
          htmlElement.style.color = '#4f46e5';
          htmlElement.style.cursor = 'pointer';
          htmlElement.style.textDecoration = 'underline';
          htmlElement.style.fontWeight = 'bold';
          htmlElement.style.borderRadius = '2px';
          htmlElement.style.padding = '1px 2px';
          
          htmlElement.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            
            // 첫 번째 인용 번호 클릭 이벤트 발생
            if (numbers.length > 0) {
              onCitationClick(numbers[0]);
              console.log(`✅ 인용 번호 ${numbers[0]} 클릭됨!`);
            }
          });

          // 호버 효과
          htmlElement.addEventListener('mouseenter', () => {
            htmlElement.style.backgroundColor = 'rgba(79, 70, 229, 0.1)';
          });
          
          htmlElement.addEventListener('mouseleave', () => {
            htmlElement.style.backgroundColor = 'transparent';
          });
        }
      });
      
      console.log(`총 ${citationCount}개의 인용 번호를 클릭 가능하게 만들었습니다.`);
    }, 1000); // 더 긴 지연시간으로 안정성 확보
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

      {/* 인용 클릭 안내 - PDF.js 모드일 때만 표시 */}
      <div style={{
        position: 'absolute',
        top: 'clamp(1rem, 2vh, 1.5rem)',
        right: 'clamp(1rem, 2vw, 1.5rem)',
        background: 'rgba(34, 197, 94, 0.9)',
        color: 'white',
        padding: 'clamp(0.5rem, 1vh, 0.75rem) clamp(0.75rem, 1.5vw, 1rem)',
        borderRadius: 'clamp(6px, 1vw, 8px)',
        fontSize: 'clamp(0.75rem, 1.4vw, 0.875rem)',
        boxShadow: '0 2px 8px rgba(0, 0, 0, 0.15)',
        zIndex: 10
      }}>
        🎯 인용 번호 [1,2,3] 클릭 가능!
      </div>
    </div>
  );
} 