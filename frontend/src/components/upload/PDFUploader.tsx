'use client';

import { useCallback, useState } from 'react';
import { FileText } from 'lucide-react';
import { PDFFile } from '@/types';
import { formatFileSize } from '@/lib/utils';

interface PDFUploaderProps {
  onFileUpload: (file: File) => void;
  currentFile?: PDFFile | null;
}

export default function PDFUploader({ onFileUpload, currentFile }: PDFUploaderProps) {
  const [isDragOver, setIsDragOver] = useState(false);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    
    const files = Array.from(e.dataTransfer.files);
    console.log('드롭된 파일들:', files.map(f => ({ name: f.name, type: f.type, size: f.size })));
    
    const pdfFile = files.find(file => 
      file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')
    );
    
    if (pdfFile) {
      console.log('PDF 파일 업로드 시작:', pdfFile.name);
      onFileUpload(pdfFile);
    } else {
      console.log('PDF 파일이 아님:', files.map(f => f.type));
      alert('PDF 파일만 업로드 가능합니다.');
    }
  }, [onFileUpload]);

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    console.log('선택된 파일:', file ? { name: file.name, type: file.type, size: file.size } : 'null');
    
    if (file && (file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf'))) {
      console.log('PDF 파일 업로드 시작:', file.name);
      onFileUpload(file);
      // 입력 필드 초기화
      e.target.value = '';
    } else {
      console.log('PDF 파일이 아님:', file?.type);
      alert('PDF 파일만 업로드 가능합니다.');
    }
  }, [onFileUpload]);

  if (currentFile) {
    return (
      <div className="uploaded-file">
        <FileText className="file-icon success" />
        <div className="file-info">
          <h3 className="file-name">{currentFile.name}</h3>
          <p className="file-size">{formatFileSize(currentFile.size)}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="uploader-container">
      <div
        className={`upload-dropzone ${isDragOver ? 'drag-over' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <div className="dropzone-content">
          <FileText className="upload-icon" />
          
          <div className="upload-text">
            <h3 className="upload-title">PDF 파일을 드래그하여 놓거나 클릭하여 선택하세요</h3>
            <p className="upload-subtitle">지원 형식: PDF (최대 100MB)</p>
          </div>
        </div>
        
        <input
          type="file"
          accept=".pdf"
          onChange={handleFileInput}
          className="file-input"
        />
      </div>
    </div>
  );
} 