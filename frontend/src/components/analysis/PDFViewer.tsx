'use client';

import { PDFFile } from '@/types';

interface PDFViewerProps {
  pdfFile: PDFFile;
  isVisible: boolean;
}

export default function PDFViewer({ pdfFile, isVisible }: PDFViewerProps) {
  if (!isVisible) {
    return null; // 상위 컴포넌트에서 처리
  }

  return (
    <div style={{ 
      height: '100%', 
      display: 'flex', 
      flexDirection: 'column'
    }}>
      <div style={{ 
        marginBottom: 'clamp(0.75rem, 2vh, 1.5rem)',
        paddingBottom: 'clamp(0.5rem, 1vh, 1rem)',
        borderBottom: '1px solid #e5e7eb'
      }}>
        <h3 style={{
          fontSize: 'clamp(0.875rem, 1.8vw, 1rem)',
          fontWeight: 600,
          color: '#111827',
          margin: 0,
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap'
        }}>
          {pdfFile.name}
        </h3>
      </div>
      
      <div style={{ 
        flex: 1,
        background: '#f8fafc',
        borderRadius: 'clamp(6px, 1vw, 10px)',
        border: '1px solid #e5e7eb',
        overflow: 'hidden'
      }}>
        <iframe
          src={pdfFile.url}
          style={{
            width: '100%',
            height: '100%',
            border: 'none',
            borderRadius: 'clamp(6px, 1vw, 10px)'
          }}
          title="PDF Viewer"
        />
      </div>
    </div>
  );
} 