'use client';

import { Reference } from '@/types';
import { formatAuthors } from '@/lib/utils';
import { ExternalLink, Quote } from 'lucide-react';

interface ReferenceListProps {
  references: Reference[];
  selectedReference?: Reference | null;
  onSelectReference: (reference: Reference) => void;
}

export default function ReferenceList({ references, selectedReference, onSelectReference }: ReferenceListProps) {
  return (
    <div style={{ 
      height: '100%', 
      display: 'flex', 
      flexDirection: 'column'
    }}>
      <div style={{ 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'space-between',
        marginBottom: 'clamp(0.75rem, 2vh, 1.5rem)',
        paddingBottom: 'clamp(0.5rem, 1vh, 1rem)',
        borderBottom: '1px solid #e5e7eb'
      }}>
        <h3 style={{
          fontSize: 'clamp(1rem, 2vw, 1.25rem)',
          fontWeight: 600,
          color: '#111827',
          margin: 0
        }}>
          인용된 논문 ({references.length})
        </h3>
        <div style={{
          fontSize: 'clamp(0.75rem, 1.5vw, 0.875rem)',
          color: '#6b7280'
        }}>
          클릭하여 상세 정보 보기
        </div>
      </div>
      
      <div style={{ 
        flex: 1,
        overflowY: 'auto',
        display: 'flex',
        flexDirection: 'column',
        gap: 'clamp(0.5rem, 1vh, 0.75rem)'
      }}>
        {references.map((reference) => (
          <div
            key={reference.id}
            onClick={() => onSelectReference(reference)}
            style={{
              background: selectedReference?.id === reference.id ? '#eef2ff' : 'white',
              border: selectedReference?.id === reference.id ? '2px solid #4f46e5' : '1px solid #e5e7eb',
              borderRadius: 'clamp(6px, 1vw, 10px)',
              padding: 'clamp(0.75rem, 2vh, 1rem)',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
              boxShadow: selectedReference?.id === reference.id 
                ? '0 4px 12px rgba(79, 70, 229, 0.1)' 
                : '0 1px 3px rgba(0, 0, 0, 0.1)'
            }}
            onMouseEnter={(e) => {
              if (selectedReference?.id !== reference.id) {
                e.currentTarget.style.background = '#f8fafc';
                e.currentTarget.style.borderColor = '#cbd5e1';
              }
            }}
            onMouseLeave={(e) => {
              if (selectedReference?.id !== reference.id) {
                e.currentTarget.style.background = 'white';
                e.currentTarget.style.borderColor = '#e5e7eb';
              }
            }}
          >
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'clamp(0.25rem, 0.5vh, 0.5rem)' }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
                <h4 style={{
                  fontSize: 'clamp(0.875rem, 1.8vw, 1rem)',
                  fontWeight: 500,
                  color: '#111827',
                  margin: 0,
                  flex: 1,
                  lineHeight: 1.4,
                  display: '-webkit-box',
                  WebkitLineClamp: 2,
                  WebkitBoxOrient: 'vertical',
                  overflow: 'hidden'
                }}>
                  {reference.title}
                </h4>
                {reference.url && (
                  <ExternalLink style={{ 
                    width: 'clamp(12px, 1.5vw, 16px)', 
                    height: 'clamp(12px, 1.5vw, 16px)', 
                    color: '#9ca3af',
                    marginLeft: 'clamp(0.25rem, 0.5vw, 0.5rem)',
                    flexShrink: 0
                  }} />
                )}
              </div>
              
              <div style={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: 'clamp(0.25rem, 0.5vw, 0.5rem)',
                fontSize: 'clamp(0.75rem, 1.4vw, 0.875rem)',
                color: '#6b7280'
              }}>
                <span>{formatAuthors(reference.authors)}</span>
                <span>•</span>
                <span>{reference.year}</span>
                {reference.venue && (
                  <>
                    <span>•</span>
                    <span style={{ 
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                      maxWidth: '100px'
                    }}>
                      {reference.venue}
                    </span>
                  </>
                )}
              </div>
              
              {reference.citationCount !== undefined && (
                <div style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: 'clamp(0.25rem, 0.5vw, 0.5rem)'
                }}>
                  <Quote style={{ 
                    width: 'clamp(10px, 1.2vw, 12px)', 
                    height: 'clamp(10px, 1.2vw, 12px)', 
                    color: '#9ca3af'
                  }} />
                  <span style={{
                    fontSize: 'clamp(0.7rem, 1.3vw, 0.8rem)',
                    color: '#6b7280'
                  }}>
                    {reference.citationCount.toLocaleString()} citations
                  </span>
                </div>
              )}
              
              {reference.abstract && (
                <p style={{
                  fontSize: 'clamp(0.75rem, 1.4vw, 0.875rem)',
                  color: '#6b7280',
                  margin: 0,
                  lineHeight: 1.4,
                  display: '-webkit-box',
                  WebkitLineClamp: 2,
                  WebkitBoxOrient: 'vertical',
                  overflow: 'hidden'
                }}>
                  {reference.abstract}
                </p>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
} 