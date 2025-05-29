import { PDFFile, AnalysisResult } from '@/types';

const STORAGE_KEYS = {
  PDF_FILE: 'refnavi_pdf_file',
  ANALYSIS_RESULT: 'refnavi_analysis_result',
} as const;

export interface StoredPDFFile {
  name: string;
  size: number;
  type: string;
  uploadedAt: string;
  data: string; // base64 encoded file data
}

export function savePDFToStorage(pdfFile: PDFFile): void {
  try {
    const reader = new FileReader();
    reader.onload = (e) => {
      const result = e.target?.result;
      if (typeof result === 'string') {
        const storedPDF: StoredPDFFile = {
          name: pdfFile.name,
          size: pdfFile.size,
          type: pdfFile.file.type,
          uploadedAt: pdfFile.uploadedAt.toISOString(),
          data: result, // base64 data URL
        };
        
        localStorage.setItem(STORAGE_KEYS.PDF_FILE, JSON.stringify(storedPDF));
        console.log('✅ PDF 파일 데이터가 localStorage에 저장됨:', {
          name: storedPDF.name,
          size: storedPDF.size,
          dataLength: result.length
        });
      }
    };
    
    reader.onerror = (e) => {
      console.error('❌ PDF 파일 읽기 실패:', e);
    };
    
    // base64 data URL로 변환
    reader.readAsDataURL(pdfFile.file);
  } catch (error) {
    console.error('❌ PDF 저장 실패:', error);
  }
}

export function loadPDFFromStorage(): PDFFile | null {
  try {
    const stored = localStorage.getItem(STORAGE_KEYS.PDF_FILE);
    if (!stored) return null;
    
    const storedPDF: StoredPDFFile = JSON.parse(stored);
    
    // base64 data URL을 다시 File 객체로 변환
    const response = fetch(storedPDF.data);
    response.then(res => res.blob()).then(blob => {
      const file = new File([blob], storedPDF.name, { 
        type: storedPDF.type 
      });
      
      console.log('✅ PDF 파일이 localStorage에서 복원됨:', {
        name: file.name,
        size: file.size,
        type: file.type
      });
    });
    
    // 임시로 data URL을 사용 (동기적 처리를 위해)
    const byteCharacters = atob(storedPDF.data.split(',')[1]);
    const byteNumbers = new Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
      byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    const file = new File([byteArray], storedPDF.name, { 
      type: storedPDF.type 
    });
    
    const pdfFile: PDFFile = {
      file: file,
      name: storedPDF.name,
      size: storedPDF.size,
      url: storedPDF.data, // data URL 사용
      uploadedAt: new Date(storedPDF.uploadedAt),
    };
    
    console.log('✅ PDF 파일 정보가 localStorage에서 로드됨 (실제 데이터 포함):', {
      name: pdfFile.name,
      size: pdfFile.size,
      fileSize: pdfFile.file.size
    });
    return pdfFile;
  } catch (error) {
    console.error('❌ PDF 로드 실패:', error);
    return null;
  }
}

export function saveAnalysisToStorage(analysisResult: AnalysisResult): void {
  try {
    localStorage.setItem(STORAGE_KEYS.ANALYSIS_RESULT, JSON.stringify(analysisResult));
    console.log('✅ 분석 결과가 localStorage에 저장됨');
  } catch (error) {
    console.error('❌ 분석 결과 저장 실패:', error);
  }
}

export function loadAnalysisFromStorage(): AnalysisResult | null {
  try {
    const stored = localStorage.getItem(STORAGE_KEYS.ANALYSIS_RESULT);
    if (!stored) return null;
    
    const analysisResult: AnalysisResult = JSON.parse(stored);
    console.log('✅ 분석 결과가 localStorage에서 로드됨');
    return analysisResult;
  } catch (error) {
    console.error('❌ 분석 결과 로드 실패:', error);
    return null;
  }
}

export function clearStorageData(): void {
  try {
    localStorage.removeItem(STORAGE_KEYS.PDF_FILE);
    localStorage.removeItem(STORAGE_KEYS.ANALYSIS_RESULT);
    console.log('✅ 저장된 데이터가 모두 삭제됨');
  } catch (error) {
    console.error('❌ 데이터 삭제 실패:', error);
  }
} 