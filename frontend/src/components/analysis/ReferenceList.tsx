'use client';

import { Reference } from '@/types';
import { formatAuthors } from '@/lib/utils';
import { ExternalLink, Quote, ArrowUpDown, ArrowUp, ArrowDown } from 'lucide-react';
import { useState, useMemo } from 'react';

interface ReferenceListProps {
  references: Reference[];
  selectedReference?: Reference | null;
  onSelectReference: (reference: Reference) => void;
}

type SortType = 'default' | 'citations' | 'year';
type SortOrder = 'asc' | 'desc';

export default function ReferenceList({ references, selectedReference, onSelectReference }: ReferenceListProps) {
  const [sortType, setSortType] = useState<SortType>('default');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');

  const sortedReferences = useMemo(() => {
    const refs = [...references];
    if (sortType === 'default') return refs;

    return refs.sort((a, b) => {
      const valueA = sortType === 'citations' ? (a.citation_count || 0) : (a.year || 0);
      const valueB = sortType === 'citations' ? (b.citation_count || 0) : (b.year || 0);
      return sortOrder === 'desc' ? valueB - valueA : valueA - valueB;
    });
  }, [references, sortType, sortOrder]);

  const handleSort = (type: SortType) => {
    if (sortType === type) {
      if (sortOrder === 'desc') {
        setSortOrder('asc');
      } else {
        setSortType('default');
        setSortOrder('desc');
      }
    } else {
      setSortType(type);
      setSortOrder('desc');
    }
  };

  const SortButton = ({ type, label }: { type: SortType; label: string }) => (
    <button
      onClick={() => handleSort(type)}
      style={{
        padding: '0.5rem',
        background: sortType === type ? '#eef2ff' : 'white',
        border: '1px solid #e5e7eb',
        borderRadius: '0.375rem',
        cursor: 'pointer',
        display: 'flex',
        alignItems: 'center',
        gap: '0.25rem',
        fontSize: '0.875rem',
        color: sortType === type ? '#4f46e5' : '#6b7280'
      }}
    >
      {sortType === type ? (
        sortOrder === 'desc' ? <ArrowDown size={16} /> : <ArrowUp size={16} />
      ) : (
        <ArrowUpDown size={16} />
      )}
      {label}
    </button>
  );

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
          display: 'flex',
          gap: '0.5rem',
          alignItems: 'center'
        }}>
          <SortButton type="citations" label="인용수" />
          <SortButton type="year" label="발행년도" />
        </div>
      </div>
      
      <div style={{ 
        flex: 1,
        overflowY: 'auto',
        display: 'flex',
        flexDirection: 'column',
        gap: 'clamp(0.5rem, 1vh, 0.75rem)'
      }}>
        {sortedReferences.map((reference) => (
          <div
            key={reference.ref_number}
            onClick={() => onSelectReference(reference)}
            style={{
              background: selectedReference?.ref_number === reference.ref_number ? '#eef2ff' : 'white',
              border: selectedReference?.ref_number === reference.ref_number ? '2px solid #4f46e5' : '1px solid #e5e7eb',
              borderRadius: 'clamp(6px, 1vw, 10px)',
              padding: 'clamp(0.75rem, 2vh, 1rem)',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
              boxShadow: selectedReference?.ref_number === reference.ref_number
                ? '0 4px 12px rgba(79, 70, 229, 0.1)' 
                : '0 1px 3px rgba(0, 0, 0, 0.1)'
            }}
            onMouseEnter={(e) => {
              if (selectedReference?.ref_number !== reference.ref_number) {
                e.currentTarget.style.background = '#f8fafc';
                e.currentTarget.style.borderColor = '#cbd5e1';
              }
            }}
            onMouseLeave={(e) => {
              if (selectedReference?.ref_number !== reference.ref_number) {
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
                  {reference.ref_title}
                </h4>
                {reference.doi && (
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
                {reference.citation_contexts && (
                  <>
                    <span>•</span>
                    <span style={{ 
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                      maxWidth: '100px'
                    }}>
                      {reference.citation_contexts}
                    </span>
                  </>
                )}
              </div>
              
              {reference.citation_count !== undefined && (
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
                    {reference.citation_count.toLocaleString()} citations
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