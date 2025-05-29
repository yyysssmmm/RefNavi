'use client';

import { useRouter } from 'next/navigation';
import PDFUploader from '@/components/upload/PDFUploader';
import FloatingButton from '@/components/ui/FloatingButton';
import { usePDFStore } from '@/hooks/usePDFStore';
import { Upload, Search } from 'lucide-react';
import './MainScreen.css';

export default function HomePage() {
  const router = useRouter();
  const { currentPDF, uploadPDF, startAnalysis, isAnalyzing, toggleChat, isLoaded } = usePDFStore();

  const handleAnalyze = async () => {
    if (!currentPDF) return;
    
    console.log('분석 시작:', currentPDF.name);
    await startAnalysis();
    router.push('/analysis');
  };

  // 로딩 중이면 로딩 화면 표시
  if (!isLoaded) {
    return (
      <div className="simple-main-screen">
        <div className="header">
          <div className="animate-spin rounded-full h-8 w-8 border-2 border-gray-900 border-t-transparent mx-auto mb-4"></div>
          <p className="text-gray-600 text-sm">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="simple-main-screen">
      {/* 헤더 */}
      <div className="header">
        <h1 className="main-title">Reference Navigator</h1>
        <p className="main-subtitle">논문 참고문헌 분석 도구</p>
      </div>

      {/* 메인 콘텐츠 - PDF 업로드 카드만 */}
      <div className="content-grid" style={{gridTemplateColumns: '1fr', maxWidth: '600px'}}>
        
        {/* PDF 업로드 카드 */}
        <div className="content-card">
          <div className="card-header">
            <Upload className="card-icon" />
            <h2 className="card-title">PDF 파일 업로드</h2>
          </div>
          
          <PDFUploader 
            onFileUpload={uploadPDF}
            currentFile={currentPDF}
          />

          {/* 분석 버튼 */}
          {currentPDF && (
            <div className="file-actions" style={{marginTop: '20px', paddingTop: '20px', borderTop: '1px solid #e2e8f0'}}>
              <button
                onClick={handleAnalyze}
                disabled={isAnalyzing}
                className="action-btn primary"
              >
                {isAnalyzing ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent btn-icon"></div>
                    분석 중...
                  </>
                ) : (
                  <>
                    <Search className="btn-icon" />
                    논문 분석 시작
                  </>
                )}
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Floating Chat Button */}
      <FloatingButton onClick={toggleChat} />
    </div>
  );
} 