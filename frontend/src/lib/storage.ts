import { PDFFile, AnalysisResult } from '@/types';

const STORAGE_KEYS = {
  PDF_FILE: 'refnavi_pdf_file',
  ANALYSIS_RESULT: 'refnavi_analysis_result',
} as const;

export interface StoredPDFFile {
  name: string;
  size: number;
  url: string;
  uploadedAt: string;
  type: string;
}

export function savePDFToStorage(pdfFile: PDFFile): void {
  try {
    const storedPDF: StoredPDFFile = {
      name: pdfFile.name,
      size: pdfFile.size,
      url: pdfFile.url,
      uploadedAt: pdfFile.uploadedAt.toISOString(),
      type: pdfFile.file.type,
    };
    
    localStorage.setItem(STORAGE_KEYS.PDF_FILE, JSON.stringify(storedPDF));
    console.log('PDF 파일 정보가 localStorage에 저장됨:', storedPDF);
  } catch (error) {
    console.error('PDF 저장 실패:', error);
  }
}

export function loadPDFFromStorage(): PDFFile | null {
  try {
    const stored = localStorage.getItem(STORAGE_KEYS.PDF_FILE);
    if (!stored) return null;
    
    const storedPDF: StoredPDFFile = JSON.parse(stored);
    
    // 가짜 File 객체 생성 (실제 파일은 저장할 수 없으므로)
    const mockFile = new File([''], storedPDF.name, { 
      type: storedPDF.type 
    });
    
    const pdfFile: PDFFile = {
      file: mockFile,
      name: storedPDF.name,
      size: storedPDF.size,
      url: storedPDF.url,
      uploadedAt: new Date(storedPDF.uploadedAt),
    };
    
    console.log('PDF 파일 정보가 localStorage에서 로드됨:', pdfFile);
    return pdfFile;
  } catch (error) {
    console.error('PDF 로드 실패:', error);
    return null;
  }
}

export function saveAnalysisToStorage(analysisResult: AnalysisResult): void {
  try {
    localStorage.setItem(STORAGE_KEYS.ANALYSIS_RESULT, JSON.stringify(analysisResult));
    console.log('분석 결과가 localStorage에 저장됨');
  } catch (error) {
    console.error('분석 결과 저장 실패:', error);
  }
}

export function loadAnalysisFromStorage(): AnalysisResult | null {
  try {
    const stored = localStorage.getItem(STORAGE_KEYS.ANALYSIS_RESULT);
    if (!stored) return null;
    
    const analysisResult: AnalysisResult = JSON.parse(stored);
    console.log('분석 결과가 localStorage에서 로드됨');
    return analysisResult;
  } catch (error) {
    console.error('분석 결과 로드 실패:', error);
    return null;
  }
}

export function clearStorageData(): void {
  try {
    localStorage.removeItem(STORAGE_KEYS.PDF_FILE);
    localStorage.removeItem(STORAGE_KEYS.ANALYSIS_RESULT);
    console.log('저장된 데이터가 모두 삭제됨');
  } catch (error) {
    console.error('데이터 삭제 실패:', error);
  }
} 