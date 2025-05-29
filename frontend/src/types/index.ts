export interface PDFFile {
  file: File;
  name: string;
  size: number;
  url: string;
  uploadedAt: Date;
}

export interface Reference {
  id: string;
  title: string;
  authors: string[];
  year: number;
  venue?: string;
  citationCount?: number;
  abstract?: string;
  url?: string;
}

export interface CitationContext {
  id: string;
  sentence: string;
  section: string;
  pageNumber?: number;
  context: string;
  references: string[]; // reference IDs
}

export interface AnalysisResult {
  references: Reference[];
  citations: CitationContext[];
  summary: {
    totalReferences: number;
    totalCitations: number;
    sections: string[];
  };
}

export interface ChatMessage {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export interface AppState {
  currentPDF: PDFFile | null;
  analysisResult: AnalysisResult | null;
  isAnalyzing: boolean;
  selectedReference: Reference | null;
  chatMessages: ChatMessage[];
  isChatOpen: boolean;
} 