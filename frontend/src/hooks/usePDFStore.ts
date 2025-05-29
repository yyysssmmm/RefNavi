'use client';

import { useState, useCallback, useEffect } from 'react';
import { PDFFile, AnalysisResult, Reference, ChatMessage } from '@/types';
import { generateId } from '@/lib/utils';
import { 
  savePDFToStorage, 
  loadPDFFromStorage, 
  saveAnalysisToStorage, 
  loadAnalysisFromStorage,
  clearStorageData 
} from '@/lib/storage';

export function usePDFStore() {
  const [currentPDF, setCurrentPDF] = useState<PDFFile | null>(null);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [selectedReference, setSelectedReference] = useState<Reference | null>(null);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [showPDFViewer, setShowPDFViewer] = useState(false);
  const [isLoaded, setIsLoaded] = useState(false);

  // 컴포넌트 마운트 시 localStorage에서 데이터 복원
  useEffect(() => {
    console.log('usePDFStore 초기화 - localStorage에서 데이터 로드 중...');
    
    const storedPDF = loadPDFFromStorage();
    const storedAnalysis = loadAnalysisFromStorage();
    
    if (storedPDF) {
      setCurrentPDF(storedPDF);
      console.log('저장된 PDF 복원됨:', storedPDF.name);
    }
    
    if (storedAnalysis) {
      setAnalysisResult(storedAnalysis);
      console.log('저장된 분석 결과 복원됨');
    }
    
    setIsLoaded(true);
  }, []);

  const uploadPDF = useCallback((file: File) => {
    console.log('usePDFStore.uploadPDF 호출됨:', file.name);
    
    const pdfFile: PDFFile = {
      file,
      name: file.name,
      size: file.size,
      url: URL.createObjectURL(file),
      uploadedAt: new Date(),
    };
    
    console.log('PDFFile 객체 생성:', pdfFile);
    setCurrentPDF(pdfFile);
    
    // localStorage에 저장
    savePDFToStorage(pdfFile);
    console.log('setCurrentPDF 및 localStorage 저장 완료');
  }, []);

  const startAnalysis = useCallback(async () => {
    if (!currentPDF) return;
    
    setIsAnalyzing(true);
    
    // 임시 목업 데이터 (실제로는 백엔드 API 호출)
    setTimeout(() => {
      const mockResult: AnalysisResult = {
        references: [
          {
            id: '1',
            title: 'Neural Machine Translation by Jointly Learning to Align and Translate',
            authors: ['Dzmitry Bahdanau', 'Kyunghyun Cho', 'Yoshua Bengio'],
            year: 2014,
            venue: 'ICLR',
            citationCount: 27162,
            abstract: 'Neural machine translation is a recently proposed approach to machine translation...',
          },
          {
            id: '2', 
            title: 'Long Short-Term Memory',
            authors: ['Sepp Hochreiter', 'Jürgen Schmidhuber'],
            year: 1997,
            venue: 'Neural Computation',
            citationCount: 89868,
            abstract: 'Learning to store information over extended time intervals by recurrent backpropagation...',
          },
          {
            id: '3',
            title: 'Effective Approaches to Attention-based Neural Machine Translation',
            authors: ['Minh-Thang Luong', 'Hieu Pham', 'Christopher D. Manning'],
            year: 2015,
            venue: 'EMNLP',
            citationCount: 7939,
            abstract: 'An attentional mechanism has lately been used to improve neural machine translation...',
          },
        ],
        citations: [
          {
            id: '1',
            sentence: 'Attention mechanisms have become an integral part of compelling sequence modeling and transduction models in various tasks, allowing modeling of dependencies without regard to their distance in the input or output sequences [2,19].',
            section: 'Introduction',
            context: 'Establishing the importance of attention mechanisms in sequence modeling',
            references: ['1', '3'],
          },
          {
            id: '2',
            sentence: 'long short-term memory [13] and gated recurrent [7] networks in particular, have been firmly established as state of the art approaches in sequence modeling and transduction problems',
            section: 'Introduction', 
            context: 'Describing current state-of-the-art sequence modeling approaches',
            references: ['2'],
          },
        ],
        summary: {
          totalReferences: 3,
          totalCitations: 2,
          sections: ['Introduction', 'Background', 'Model Architecture'],
        },
      };
      
      setAnalysisResult(mockResult);
      saveAnalysisToStorage(mockResult);
      setIsAnalyzing(false);
      console.log('분석 완료 및 localStorage 저장됨');
    }, 2000);
  }, [currentPDF]);

  const addChatMessage = useCallback((content: string, type: 'user' | 'assistant' = 'user') => {
    const message: ChatMessage = {
      id: generateId(),
      type,
      content,
      timestamp: new Date(),
    };
    setChatMessages(prev => [...prev, message]);
  }, []);

  const toggleChat = useCallback(() => {
    setIsChatOpen(prev => !prev);
  }, []);

  const togglePDFViewer = useCallback(() => {
    setShowPDFViewer(prev => !prev);
  }, []);

  const reset = useCallback(() => {
    setCurrentPDF(null);
    setAnalysisResult(null);
    setIsAnalyzing(false);
    setSelectedReference(null);
    setChatMessages([]);
    setIsChatOpen(false);
    setShowPDFViewer(false);
    
    // localStorage도 클리어
    clearStorageData();
    console.log('모든 상태 및 localStorage 클리어됨');
  }, []);

  return {
    // State
    currentPDF,
    analysisResult,
    isAnalyzing,
    selectedReference,
    chatMessages,
    isChatOpen,
    showPDFViewer,
    isLoaded, // 초기 로딩 완료 여부
    
    // Actions
    uploadPDF,
    startAnalysis,
    setSelectedReference,
    addChatMessage,
    toggleChat,
    togglePDFViewer,
    reset,
  };
} 