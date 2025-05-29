'use client'

import React, { useState, useEffect, useRef } from 'react'
import * as pdfjsLib from 'pdfjs-dist'

// PDF.js Worker 설정
pdfjsLib.GlobalWorkerOptions.workerSrc = '/pdfjs/pdf.worker.min.js'

interface PDFViewerProps {
  pdfFile: File | null;
  isVisible: boolean;
  onCitationClick?: (citationId: number) => void;
}

const PDFViewer: React.FC<PDFViewerProps> = ({ pdfFile, isVisible, onCitationClick }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [numPages, setNumPages] = useState<number>(0)
  const [currentPage, setCurrentPage] = useState<number>(1)
  const [pdfDoc, setPdfDoc] = useState<pdfjsLib.PDFDocumentProxy | null>(null)
  const [isLoading, setIsLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (pdfFile && isVisible) {
      loadPDF()
    }
  }, [pdfFile, isVisible])

  useEffect(() => {
    if (pdfDoc && currentPage) {
      renderPage(currentPage)
    }
  }, [pdfDoc, currentPage])

  const loadPDF = async () => {
    if (!pdfFile) return

    setIsLoading(true)
    setError(null)

    try {
      const arrayBuffer = await pdfFile.arrayBuffer()
      const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise
      setPdfDoc(pdf)
      setNumPages(pdf.numPages)
      setCurrentPage(1)
    } catch (err) {
      console.error('PDF 로딩 에러:', err)
      setError('PDF를 로드할 수 없습니다.')
    } finally {
      setIsLoading(false)
    }
  }

  const renderPage = async (pageNum: number) => {
    if (!pdfDoc || !canvasRef.current) return

    try {
      const page = await pdfDoc.getPage(pageNum)
      const canvas = canvasRef.current
      const context = canvas.getContext('2d')
      
      if (!context) return

      const viewport = page.getViewport({ scale: 1.2 })
      canvas.height = viewport.height
      canvas.width = viewport.width

      const renderContext = {
        canvasContext: context,
        viewport: viewport
      }

      await page.render(renderContext).promise

      // 텍스트 레이어 추가 (인용 클릭을 위해)
      await addTextLayer(page, viewport)
    } catch (err) {
      console.error('페이지 렌더링 에러:', err)
      setError('페이지를 렌더링할 수 없습니다.')
    }
  }

  const addTextLayer = async (page: pdfjsLib.PDFPageProxy, viewport: pdfjsLib.PageViewport) => {
    if (!canvasRef.current?.parentElement) return

    // 기존 텍스트 레이어 제거
    const existingTextLayer = canvasRef.current.parentElement.querySelector('.textLayer')
    if (existingTextLayer) {
      existingTextLayer.remove()
    }

    try {
      const textContent = await page.getTextContent()
      
      // 텍스트 레이어 div 생성
      const textLayer = document.createElement('div')
      textLayer.className = 'textLayer'
      textLayer.style.position = 'absolute'
      textLayer.style.left = '0'
      textLayer.style.top = '0'
      textLayer.style.right = '0'
      textLayer.style.bottom = '0'
      textLayer.style.overflow = 'hidden'
      textLayer.style.opacity = '0.2'
      textLayer.style.lineHeight = '1.0'
      textLayer.style.pointerEvents = 'auto'

      // 텍스트 아이템들을 처리
      textContent.items.forEach((item: any) => {
        // TextItem인지 확인 (TextMarkedContent가 아닌)
        if (!("str" in item)) {
          return;
        }

        const div = document.createElement('div')
        const tx = pdfjsLib.Util.transform(
          pdfjsLib.Util.transform(viewport.transform, item.transform),
          [1, 0, 0, -1, 0, 0]
        )

        div.style.position = 'absolute'
        div.style.left = tx[4] + 'px'
        div.style.top = tx[5] + 'px'
        div.style.fontSize = Math.sqrt(tx[0] * tx[0] + tx[1] * tx[1]) + 'px'
        div.style.fontFamily = item.fontName
        div.textContent = item.str

        // 인용 번호 패턴 확인 및 클릭 가능하게 만들기
        const citationPattern = /\[(\d+(?:,\s*\d+)*)\]/g
        if (citationPattern.test(item.str)) {
          div.style.color = '#4f46e5'
          div.style.textDecoration = 'underline'
          div.style.cursor = 'pointer'
          div.style.backgroundColor = 'rgba(79, 70, 229, 0.1)'
          div.style.padding = '2px 4px'
          div.style.borderRadius = '3px'
          div.style.pointerEvents = 'auto'
          
          div.addEventListener('click', (e) => {
            e.preventDefault()
            e.stopPropagation()
            
            const matches = item.str.match(/\[(\d+(?:,\s*\d+)*)\]/)
            if (matches && onCitationClick) {
              const citationIds = matches[1].split(',').map((id: string) => parseInt(id.trim()))
              // 첫 번째 인용 번호를 사용
              onCitationClick(citationIds[0])
            }
          })
        }

        textLayer.appendChild(div)
      })

      canvasRef.current.parentElement.appendChild(textLayer)
    } catch (err) {
      console.error('텍스트 레이어 추가 에러:', err)
    }
  }

  const goToPage = (page: number) => {
    if (page >= 1 && page <= numPages) {
      setCurrentPage(page)
    }
  }

  if (!isVisible) {
    return null
  }

  if (isLoading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100%',
        color: '#64748b',
        fontSize: 'clamp(1rem, 2vw, 1.25rem)'
      }}>
        📄 PDF 로딩 중...
      </div>
    )
  }

  if (error) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100%',
        color: '#ef4444',
        fontSize: 'clamp(1rem, 2vw, 1.25rem)',
        textAlign: 'center'
      }}>
        ❌ {error}
      </div>
    )
  }

  if (!pdfFile) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100%',
        color: '#94a3b8',
        fontSize: 'clamp(1rem, 2vw, 1.25rem)'
      }}>
        📄 PDF 파일을 선택해주세요
      </div>
    )
  }

  return (
    <div style={{ 
      display: 'flex', 
      flexDirection: 'column', 
      height: '100%',
      background: '#f8fafc'
    }}>
      {/* PDF 컨트롤 */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: 'clamp(0.75rem, 1.5vh, 1rem)',
        background: 'white',
        borderBottom: '1px solid #e5e7eb',
        fontSize: 'clamp(0.8rem, 1.6vw, 0.9rem)'
      }}>
        <button
          onClick={() => goToPage(currentPage - 1)}
          disabled={currentPage <= 1}
          style={{
            padding: 'clamp(0.5rem, 1vh, 0.75rem) clamp(0.75rem, 1.5vw, 1rem)',
            background: currentPage <= 1 ? '#f1f5f9' : '#4f46e5',
            color: currentPage <= 1 ? '#94a3b8' : 'white',
            border: 'none',
            borderRadius: 'clamp(4px, 0.8vw, 6px)',
            cursor: currentPage <= 1 ? 'not-allowed' : 'pointer',
            fontSize: 'clamp(0.8rem, 1.6vw, 0.9rem)',
            fontWeight: 500
          }}
        >
          이전
        </button>
        
        <span style={{
          fontWeight: 600,
          color: '#374151'
        }}>
          {currentPage} / {numPages}
        </span>
        
        <button
          onClick={() => goToPage(currentPage + 1)}
          disabled={currentPage >= numPages}
          style={{
            padding: 'clamp(0.5rem, 1vh, 0.75rem) clamp(0.75rem, 1.5vw, 1rem)',
            background: currentPage >= numPages ? '#f1f5f9' : '#4f46e5',
            color: currentPage >= numPages ? '#94a3b8' : 'white',
            border: 'none',
            borderRadius: 'clamp(4px, 0.8vw, 6px)',
            cursor: currentPage >= numPages ? 'not-allowed' : 'pointer',
            fontSize: 'clamp(0.8rem, 1.6vw, 0.9rem)',
            fontWeight: 500
          }}
        >
          다음
        </button>
      </div>

      {/* PDF 뷰어 */}
      <div style={{ 
        flex: 1, 
        overflow: 'auto',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'flex-start',
        padding: 'clamp(1rem, 2vh, 1.5rem)',
        background: '#f1f5f9'
      }}>
        <div style={{ 
          position: 'relative',
          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
          borderRadius: 'clamp(8px, 1vw, 12px)',
          overflow: 'hidden',
          background: 'white'
        }}>
          <canvas 
            ref={canvasRef}
            style={{ 
              display: 'block',
              maxWidth: '100%',
              height: 'auto'
            }}
          />
        </div>
      </div>
    </div>
  )
}

export default PDFViewer 