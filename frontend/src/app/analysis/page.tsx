'use client';

import { useRouter } from 'next/navigation';
import { useState, useMemo } from 'react';
import { usePDFStore } from '@/hooks/usePDFStore';
import ReferenceList from '@/components/analysis/ReferenceList';
import PDFViewer from '@/components/analysis/PDFViewer';
import ChatBot from '@/components/chat/ChatBot';
import FloatingButton from '@/components/ui/FloatingButton';
import { ArrowLeft, Search, BookOpen } from 'lucide-react';
import '../MainScreen.css';

type ViewMode = 'none' | 'references' | 'pdf';

export default function AnalysisPage() {
  const router = useRouter();
  const {
    currentPDF,
    analysisResult,
    selectedReference,
    selectedReference_second_tab,
    setSelectedReference,
    setSelectedReference_second_tab,
    chatMessages,
    isChatOpen,
    toggleChat,
    addChatMessage,
    reset,
    isLoaded,
  } = usePDFStore();

  const [viewMode, setViewMode] = useState<ViewMode>('none');
  const [citationPurpose, setCitationPurpose] = useState<string | null>(null);
  const [isPurposeLoading, setIsPurposeLoading] = useState(false);
  const [purposeError, setPurposeError] = useState<string | null>(null);

  // Reference 타입을 analysisResult가 정의된 이후에 선언 (실제 타입 추론)
  type Reference = NonNullable<typeof analysisResult>['references'][number];

  const referenceMap = useMemo(() => {
    const map = new Map<number, Reference>();
    if (!analysisResult?.references) return map;
    analysisResult.references.forEach(ref => {
      const matches = String(ref.ref_number).match(/\[(.*?)\]/);
      if (!matches) return;
      const numbers = matches[1].split(',').map(num => parseInt(num.trim()));
      numbers.forEach(num => {
        map.set(num, ref);
      });
    });
    return map;
  }, [analysisResult?.references]);

  // 로딩 중이거나 데이터가 없는 경우 로딩 표시
  if (!isLoaded || !currentPDF || !analysisResult) {
    return (
      <div className="simple-main-screen">
        <div className="header">
          <div className="animate-spin rounded-full h-8 w-8 border-2 border-gray-900 border-t-transparent mx-auto mb-4"></div>
          <p className="text-gray-600 text-sm">
            {!isLoaded ? '데이터를 로드하고 있습니다...' : '페이지를 이동하고 있습니다...'}
          </p>
        </div>
      </div>
    );
  }

  const handleBackToHome = () => {
    reset();
    router.push('/');
  };

  // 인용 번호 클릭 핸들러
  const handleCitationClick = async (
    citationNumber: number,
    contextSentences: string[],
    exactCitationSentence: string,
    options?: { clearReferences?: boolean; keepViewMode?: boolean }
  ) => {
    console.log('🔎 클릭된 citationNumber:', citationNumber);

    const reference = referenceMap.get(citationNumber);

    if (reference) {
      setSelectedReference_second_tab(reference);
      if (!options?.keepViewMode) setViewMode('pdf');
      if (options?.clearReferences) setSelectedReference(null);
      console.log(`✅ 인용 번호 ${citationNumber} 클릭됨:`, reference.ref_title);

      // Citation purpose 요청
      setCitationPurpose(null);
      setPurposeError(null);
      setIsPurposeLoading(true);
      try {
        // 1. 모든 문맥 (reference의 citation_contexts에서 가져오기)
        const all_contexts = reference.citation_contexts ? 
          (typeof reference.citation_contexts === 'string' ? 
            [reference.citation_contexts] : 
            reference.citation_contexts) : 
          [];
        
        // 2. abstract
        const abstract = reference.abstract || '';
        const ref_title = reference.ref_title || '';
        
        // 3. full text (본문 텍스트) - analysisResult의 body_fixed 사용
        const full_text = analysisResult.body_fixed || '';
        
        console.log('Citation data:', {
          citationNumber,
          ref_title,
          localContext: contextSentences,
          exactCitationSentence,
          allContexts: all_contexts,
          abstract,
          fullTextLength: full_text.length
        });

        // 4. API 호출
        const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL;
        if (!apiUrl) {
          throw new Error('API Gateway URL is not defined');
        }

        const response = await fetch(apiUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            citation_number: citationNumber,
            local_context: contextSentences,
            exact_citation_sentence: exactCitationSentence,
            all_contexts,
            abstract,
            full_text,
            ref_title
          }),
        });
        if (!response.ok) throw new Error('API 요청 실패');
        console.log('citationNumber', citationNumber);
        console.log('contextSentenses', contextSentences);
        console.log('all_contexts', all_contexts);
        console.log('abstract', abstract);
        console.log('full_text', full_text);
        console.log('ref_title', ref_title);
        const data = await response.json();
        let purpose = "";
        if (typeof data.body === "string") {
          // body가 JSON string이면 한 번 더 파싱
          const bodyObj = JSON.parse(data.body);
          purpose = bodyObj.purpose;
        } else if (data.purpose) {
          // 혹시 바로 purpose가 있으면
          purpose = data.purpose;
        }
        setCitationPurpose(purpose);
      } catch (err: unknown) {
        setPurposeError(err instanceof Error ? err.message : '오류 발생');
      } finally {
        setIsPurposeLoading(false);
      }
    } else {
      console.warn(`❌ 인용 번호 ${citationNumber}에 해당하는 논문을 찾을 수 없습니다.`);
    }
  };

  const renderRightContent = () => {
    switch (viewMode) {
      case 'references':
        return (
          <div className="content-card">
            <div className="card-header">
              <BookOpen className="card-icon" />
              <h2 className="card-title">참고문헌 목록</h2>
            </div>
            
            <div style={{ 
              flex: 1, 
              overflow: 'hidden',
              display: 'flex',
              flexDirection: 'row', // 🔁 핵심 수정!
              gap: '1rem' // 🔧 카드 간 간격 추가
            }}>
              {/* 왼쪽: 참고문헌 리스트 */}
              <div style={{ flex: 1, overflowY: 'auto' }}>
                <ReferenceList
                  references={analysisResult.references}
                  selectedReference={selectedReference}
                  onSelectReference={(ref) => {
                    setSelectedReference(ref);
                    if (viewMode !== 'references') {
                      setViewMode('pdf');
                    }
                  }}
                />
              </div>

              {/* 오른쪽: 상세정보 카드 */}
              {selectedReference && (
                <div style={{
                  flex: 1,
                  padding: '1rem', 
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px',
                  background: '#f9fafb',
                  overflowY: 'auto'
                }}>
                  <h3 style={{ fontSize: '1.2rem', fontWeight: 600 }}>{selectedReference.ref_title}</h3>
                  <p style={{ fontSize: '0.9rem', color: '#475569' }}>
                    👥 {selectedReference.authors?.join(', ')} | 📅 {selectedReference.year} | 📊 {selectedReference.citation_count?.toLocaleString()}회 인용
                  </p>
                  <p style={{ marginTop: '0.5rem', fontSize: '0.9rem', color: '#334155' }}>
                    {selectedReference.abstract || '초록 정보가 없습니다.'}
                  </p>
                  <div style={{ textAlign: 'right', marginTop: '0.75rem' }}>
                    <button 
                      onClick={() => setSelectedReference(null)}
                      style={{
                        padding: '0.4rem 0.8rem',
                        background: '#e0e7ff',
                        border: 'none',
                        borderRadius: '4px',
                        fontSize: '0.85rem',
                        cursor: 'pointer'
                      }}
                    >
                      닫기
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        );


      case 'pdf':
        return (
          <>
            {/* 가운데: PDF 뷰어 */}
            <div className="content-card" style={{ padding: 0 , maxWidth: '100%'}}>
              <div style={{ 
                flex: 1,
                overflow: 'hidden',
                display: 'flex',
                flexDirection: 'column',
                height: '100%'
              }}>
                <PDFViewer
                  pdfFile={currentPDF}
                  isVisible={viewMode === 'pdf'}
                  onCitationClick={(citationNumber, contextSentences, exactCitationSentence) => {
                    handleCitationClick(citationNumber, contextSentences, exactCitationSentence, { clearReferences: true, keepViewMode: true });
                  }}
                />
              </div>
            </div>

            {/* 오른쪽: 선택된 논문 카드 */}
            <div className="content-card">
              <div className="card-header">
                <Search className="card-icon" />
                <h2 className="card-title" >논문 정보</h2>
              </div>
              
              <div style={{ 
                flex: 1,
                overflow: 'auto',
                display: 'flex',
                flexDirection: 'column'
              }}>
                {selectedReference_second_tab ? (
                  <div style={{
                    padding: '1rem',
                    background: '#f8fafc',
                    borderRadius: '8px',
                    border: '2px solid #4f46e5'
                  }}>
                    <div style={{
                      marginBottom: '1rem',
                      padding: '0.5rem',
                      background: '#4f46e5',
                      color: 'white',
                      borderRadius: '6px',
                      textAlign: 'center',
                      fontSize: 'clamp(0.875rem, 1.8vw, 1rem)',
                      fontWeight: 600
                    }}>
                      📄 인용 번호 [{selectedReference_second_tab.ref_number}]
                    </div>

                    <h3 style={{
                      fontSize: '1.25rem',
                      fontWeight: 700,
                      color: '#1e293b',
                      margin: '0 0 1rem 0',
                      lineHeight: 1.3
                    }}>
                      {selectedReference_second_tab.ref_title}
                    </h3>
                    
                    <div style={{
                      marginBottom: '1rem'
                    }}>
                      <p style={{
                        fontSize: '1rem',
                        color: '#475569',
                        margin: '0 0 0.75rem 0',
                        fontWeight: 500
                      }}>
                        👥 {selectedReference_second_tab.authors.join(', ')}
                      </p>
                      
                      <div style={{
                        display: 'flex',
                        gap: '1.5rem',
                        flexWrap: 'wrap',
                        fontSize: '0.9rem',
                        color: '#64748b'
                      }}>
                        <span>📅 {selectedReference_second_tab.year}</span>
                        <span>📖 {selectedReference_second_tab.citation_contexts}</span>
                        <span>📊 {selectedReference_second_tab.citation_count.toLocaleString()}회 인용</span>
                      </div>
                    </div>

                    <div style={{
                      background: 'white',
                      padding: '1rem',
                      borderRadius: '6px',
                      border: '1px solid #e5e7eb'
                    }}>
                      <h4 style={{
                        fontSize: '1rem',
                        fontWeight: 600,
                        color: '#374151',
                        margin: '0 0 0.75rem 0'
                      }}>
                        📝 초록
                      </h4>
                      <p style={{
                        fontSize: '0.9rem',
                        color: '#4b5563',
                        lineHeight: 1.6,
                        margin: 0
                      }}>
                        {selectedReference_second_tab.abstract}
                      </p>
                    </div>

                    <div style={{
                      marginTop: '1rem',
                      textAlign: 'center'
                    }}>
                      <button 
                        onClick={() => setSelectedReference_second_tab(null)}
                        style={{
                          padding: 'clamp(0.5rem, 1vh, 0.75rem) clamp(1rem, 2vw, 1.5rem)',
                          background: '#f1f5f9',
                          color: '#475569',
                          border: '1px solid #cbd5e1',
                          borderRadius: 'clamp(6px, 1vw, 8px)',
                          fontSize: 'clamp(0.8rem, 1.6vw, 0.9rem)',
                          cursor: 'pointer',
                          fontWeight: 500
                        }}
                      >
                        닫기
                      </button>
                    </div>
                  </div>
                ) : (
                  <div style={{
                    flex: 1,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    textAlign: 'center',
                    color: '#94a3b8',
                    fontSize: 'clamp(0.875rem, 1.8vw, 1rem)',
                    padding: 'clamp(2rem, 5vh, 4rem)'
                  }}>
                    <div>
                      <div style={{ 
                        fontSize: 'clamp(2rem, 5vw, 3rem)',
                        marginBottom: 'clamp(1rem, 2vh, 1.5rem)'
                      }}>
                        🎯
                      </div>
                      <h3 style={{
                        fontSize: 'clamp(1rem, 2.5vw, 1.5rem)',
                        fontWeight: 600,
                        color: '#64748b',
                        margin: '0 0 clamp(0.5rem, 1vh, 1rem) 0'
                      }}>
                        인용 번호를 클릭하세요
                      </h3>
                      <p style={{ margin: 0, lineHeight: 1.5 }}>
                        PDF에서 파란색 인용 번호<br />
                        <strong>[1], [2], [3]</strong>을 클릭하면<br />
                        여기에 논문 정보가 나타납니다.
                      </p>
                    </div>
                  </div>
                )}

                {isPurposeLoading ? (
                  <div style={{ marginTop: '1rem', color: '#4f46e5' }}>인용 목적 분석 중...</div>
                ) : purposeError ? (
                  <div style={{ marginTop: '1rem', color: 'red' }}>{purposeError}</div>
                ) : citationPurpose && (
                  <div style={{ marginTop: '1rem', background: '#eef2ff', padding: '1rem', borderRadius: '8px' }}>
                    <strong>📌 Citation Purpose:</strong>
                    <div style={{ marginTop: '0.5rem', color: '#1e293b', whiteSpace: 'pre-wrap' }}>{citationPurpose}</div>
                  </div>
                )}
              </div>
            </div>
          </>
        );

      default:
        return (
          <div className="content-card">
            <div style={{
              flex: 1,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              textAlign: 'center',
              color: '#94a3b8',
              fontSize: 'clamp(0.875rem, 1.8vw, 1rem)',
              padding: 'clamp(2rem, 5vh, 4rem)'
            }}>
              <div>
                <Search style={{ 
                  width: 'clamp(48px, 8vw, 72px)', 
                  height: 'clamp(48px, 8vw, 72px)',
                  margin: '0 auto clamp(1rem, 2vh, 2rem)',
                  display: 'block'
                }} />
                <h3 style={{
                  fontSize: 'clamp(1rem, 2.5vw, 1.5rem)',
                  fontWeight: 600,
                  color: '#64748b',
                  margin: '0 0 clamp(0.5rem, 1vh, 1rem) 0'
                }}>
                  분석을 시작하세요
                </h3>
                <p style={{ margin: 0, lineHeight: 1.5 }}>
                  왼쪽에서 참고문헌 목록을 보거나<br />
                  PDF에서 인용 문장을 분석해보세요.
                </p>
              </div>
            </div>
          </div>
        );
    }
  };

  return (
    <div className="simple-main-screen">
      {/* 헤더 */}
      <div className="header" style={{ 
        paddingTop: 'clamp(0.5rem, 1vh, 0.75rem)',
        paddingBottom: 'clamp(0.5rem, 1vh, 0.75rem)',
        marginBottom: 'clamp(0.75rem, 1.5vh, 1rem)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'clamp(0.75rem, 1.5vw, 1rem)', marginBottom: 'clamp(0.4rem, 0.8vh, 0.5rem)' }}>
          <button
            onClick={handleBackToHome}
            className="action-btn secondary"
            style={{ 
              width: 'auto', 
              padding: 'clamp(0.4rem, 0.8vh, 0.5rem) clamp(0.6rem, 1.2vh, 0.8rem)', 
              fontSize: 'clamp(0.75rem, 1.3vw, 0.875rem)',
              background: '#f8fafc',
              color: '#475569',
              border: '1px solid #e2e8f0'
            }}
          >
            <ArrowLeft style={{ width: '14px', height: '14px', marginRight: '0.3rem' }} />
            돌아가기
          </button>
        </div>
        
        <h1 className="main-title" style={{ 
          marginBottom: 'clamp(0.3rem, 0.6vh, 0.4rem)',
          fontSize: 'clamp(1.25rem, 2.5vw, 1.75rem)',
          fontWeight: 700,
          lineHeight: 1.1
        }}>분석 결과</h1>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'clamp(0.15rem, 0.3vh, 0.25rem)' }}>
          <p className="main-subtitle" style={{ 
            marginBottom: 'clamp(0.1rem, 0.2vh, 0.2rem)',
            fontSize: 'clamp(0.875rem, 1.5vw, 1rem)',
            lineHeight: 1.2
          }}>{currentPDF.name}</p>
          <p style={{ 
            fontSize: 'clamp(0.75rem, 1.3vw, 0.875rem)', 
            color: '#64748b',
            margin: 0,
            lineHeight: 1.2
          }}>
            {analysisResult.references.length}개 논문 인용됨
          </p>
        </div>
      </div>

      {/* 메인 콘텐츠 - 3단 레이아웃 */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: viewMode === 'pdf' ? '120px 700px 3fr' : '120px 1fr',
        gap: '10px',
        margin: '0 auto',
        width: '100%',
        height: 'calc(100vh - 180px)'
      }}>
        
        {/* 왼쪽 - 좁은 사이드바 */}
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '10px'
        }}>
          
          {/* 참고문헌 목록 버튼 */}
          <button
            onClick={() => setViewMode('references')}
            style={{
              background: viewMode === 'references' ? '#eef2ff' : 'white',
              border: viewMode === 'references' ? '2px solid #4f46e5' : '1px solid #e5e7eb',
              borderRadius: '6px',
              padding: '10px',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
              boxShadow: viewMode === 'references' 
                ? '0 4px 12px rgba(79, 70, 229, 0.15)' 
                : '0 2px 4px rgba(0, 0, 0, 0.1)',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '5px',
              textAlign: 'center'
            }}
            onMouseEnter={(e) => {
              if (viewMode !== 'references') {
                e.currentTarget.style.background = '#f8fafc';
                e.currentTarget.style.borderColor = '#cbd5e1';
                e.currentTarget.style.transform = 'translateY(-1px)';
              }
            }}
            onMouseLeave={(e) => {
              if (viewMode !== 'references') {
                e.currentTarget.style.background = 'white';
                e.currentTarget.style.borderColor = '#e5e7eb';
                e.currentTarget.style.transform = 'none';
              }
            }}
          >
            <BookOpen style={{
              width: '30px',
              height: '30px',
              color: viewMode === 'references' ? '#4f46e5' : '#64748b'
            }} />
            <div>
              <h3 style={{
                fontSize: '15px',
                fontWeight: 600,
                color: viewMode === 'references' ? '#4f46e5' : '#111827',
                margin: '0 0 5px 0',
                lineHeight: 1.2
              }}>
                참고문헌
              </h3>
              <p style={{
                fontSize: '13px',
                color: '#64748b',
                margin: 0,
                lineHeight: 1.3
              }}>
                {analysisResult.references.length}개
              </p>
            </div>
          </button>

          {/* 인용문장 분석 버튼 */}
          <button
            onClick={() => setViewMode('pdf')}
            style={{
              background: viewMode === 'pdf' ? '#eef2ff' : 'white',
              border: viewMode === 'pdf' ? '2px solid #4f46e5' : '1px solid #e5e7eb',
              borderRadius: '6px',
              padding: '10px',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
              boxShadow: viewMode === 'pdf' 
                ? '0 4px 12px rgba(79, 70, 229, 0.15)' 
                : '0 2px 4px rgba(0, 0, 0, 0.1)',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '5px',
              textAlign: 'center'
            }}
            onMouseEnter={(e) => {
              if (viewMode !== 'pdf') {
                e.currentTarget.style.background = '#f8fafc';
                e.currentTarget.style.borderColor = '#cbd5e1';
                e.currentTarget.style.transform = 'translateY(-1px)';
              }
            }}
            onMouseLeave={(e) => {
              if (viewMode !== 'pdf') {
                e.currentTarget.style.background = 'white';
                e.currentTarget.style.borderColor = '#e5e7eb';
                e.currentTarget.style.transform = 'none';
              }
            }}
          >
            <Search style={{
              width: '30px',
              height: '30px',
              color: viewMode === 'pdf' ? '#4f46e5' : '#64748b'
            }} />
            <div>
              <h3 style={{
                fontSize: '15px',
                fontWeight: 600,
                color: viewMode === 'pdf' ? '#4f46e5' : '#111827',
                margin: '0 0 5px 0',
                lineHeight: 1.2
              }}>
                인용분석
              </h3>
              <p style={{
                fontSize: '13px',
                color: '#64748b',
                margin: 0,
                lineHeight: 1.3
              }}>
                PDF 분석
              </p>
            </div>
          </button>
        </div>

        {/* 오른쪽 - 동적 콘텐츠 */}
        {renderRightContent()}
      </div>

      {/* Chat Bot */}
      <ChatBot
        isOpen={isChatOpen}
        onClose={toggleChat}
        messages={chatMessages}
        onSendMessage={addChatMessage}
      />

      {/* Floating Chat Button */}
      <FloatingButton onClick={toggleChat} />
    </div>
  );
} 