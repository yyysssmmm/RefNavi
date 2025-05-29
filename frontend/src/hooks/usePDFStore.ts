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
    
    // 기존 데이터 형식과 호환성 문제로 한 번 클리어 (개발 중에만)
    const hasOldFormat = localStorage.getItem('refnavi_pdf_file');
    if (hasOldFormat) {
      try {
        const oldData = JSON.parse(hasOldFormat);
        if (!oldData.data) {
          console.log('🔄 구 형식 데이터 감지 - localStorage 클리어');
          clearStorageData();
        }
      } catch (e) {
        console.log('🔄 잘못된 데이터 형식 - localStorage 클리어:', e);
        clearStorageData();
      }
    }
    
    const storedPDF = loadPDFFromStorage();
    const storedAnalysis = loadAnalysisFromStorage();
    
    if (storedPDF) {
      setCurrentPDF(storedPDF);
      console.log('✅ 저장된 PDF 복원됨:', storedPDF.name, '(실제 데이터 포함)');
    }
    
    if (storedAnalysis) {
      setAnalysisResult(storedAnalysis);
      console.log('✅ 저장된 분석 결과 복원됨');
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
            id: 1,
            title: "Attention Is All You Need",
            authors: ["Ashish Vaswani", "Noam Shazeer", "Niki Parmar", "Jakob Uszkoreit", "Llion Jones", "Aidan N. Gomez", "Lukasz Kaiser", "Illia Polosukhin"],
            year: 2017,
            venue: "Advances in Neural Information Processing Systems",
            citationCount: 97523,
            doi: "10.5555/3295222.3295349",
            abstract: "이 논문에서는 오직 attention 메커니즘에만 기반한 새로운 신경망 아키텍처인 Transformer를 제안합니다. RNN이나 CNN을 완전히 배제하면서도 기계번역에서 최고 성능을 달성했으며, 병렬화가 가능하고 학습 시간도 크게 단축되었습니다. 이 모델은 현재 대부분의 최신 언어 모델의 기반이 되고 있습니다."
          },
          {
            id: 2,
            title: "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding",
            authors: ["Jacob Devlin", "Ming-Wei Chang", "Kenton Lee", "Kristina Toutanova"],
            year: 2018,
            venue: "NAACL-HLT",
            citationCount: 68420,
            doi: "10.18653/v1/N19-1423",
            abstract: "BERT는 모든 층에서 좌우 문맥을 모두 고려하는 깊은 양방향 표현을 사전 훈련하는 새로운 언어 표현 모델입니다. 사전 훈련된 BERT는 질의응답, 언어 추론 등 다양한 자연어처리 태스크에서 최고 성능을 달성했습니다."
          },
          {
            id: 3,
            title: "GPT-3: Language Models are Few-Shot Learners",
            authors: ["Tom B. Brown", "Benjamin Mann", "Nick Ryder", "Melanie Subbiah", "Jared Kaplan"],
            year: 2020,
            venue: "Advances in Neural Information Processing Systems",
            citationCount: 42156,
            doi: "10.5555/3495724.3496261",
            abstract: "GPT-3는 1750억 개의 매개변수를 가진 자동회귀 언어 모델로, 다양한 NLP 태스크에서 몇 개의 예시만으로도 강력한 성능을 보입니다. 별도의 파인튜닝 없이도 번역, 질의응답, 창작 등에서 인간 수준의 성능을 달성했습니다."
          },
          {
            id: 4,
            title: "ResNet: Deep Residual Learning for Image Recognition",
            authors: ["Kaiming He", "Xiangyu Zhang", "Shaoqing Ren", "Jian Sun"],
            year: 2016,
            venue: "IEEE Conference on Computer Vision and Pattern Recognition",
            citationCount: 95832,
            doi: "10.1109/CVPR.2016.90",
            abstract: "잔차 연결을 도입한 깊은 신경망 아키텍처인 ResNet을 제안합니다. 기울기 소실 문제를 해결하여 매우 깊은 네트워크(152층)의 훈련을 가능하게 했으며, ImageNet에서 최고 성능을 달성했습니다."
          },
          {
            id: 23,
            title: "Adam: A Method for Stochastic Optimization",
            authors: ["Diederik P. Kingma", "Jimmy Ba"],
            year: 2014,
            venue: "International Conference on Learning Representations",
            citationCount: 78542,
            doi: "10.48550/arXiv.1412.6980",
            abstract: "확률적 목적함수 최적화를 위한 Adam 알고리즘을 제안합니다. 적응적 학습률을 사용하여 효율적이고 안정적인 최적화를 제공하며, 대부분의 딥러닝 모델에서 표준 옵티마이저로 사용되고 있습니다."
          },
          {
            id: 24,
            title: "Dropout: A Simple Way to Prevent Neural Networks from Overfitting",
            authors: ["Nitish Srivastava", "Geoffrey Hinton", "Alex Krizhevsky", "Ilya Sutskever", "Ruslan Salakhutdinov"],
            year: 2014,
            venue: "Journal of Machine Learning Research",
            citationCount: 45623,
            doi: "10.5555/2627435.2670313",
            abstract: "드롭아웃은 신경망의 과적합을 방지하는 간단하면서도 효과적인 정규화 기법입니다. 훈련 중 무작위로 뉴런을 제거하여 모델의 일반화 성능을 크게 향상시킵니다."
          }
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