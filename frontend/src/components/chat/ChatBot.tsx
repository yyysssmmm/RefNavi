'use client';

import { useState } from 'react';
import { Send, X } from 'lucide-react';
import { ChatMessage } from '@/types';

interface ChatBotProps {
  isOpen: boolean;
  onClose: () => void;
  messages: ChatMessage[];
  onSendMessage: (
    message: string,
    type?: 'user' | 'assistant',
    sources?: {
      title?: string;
      year?: number;
      authors?: string[];
      summary?: string;
    }[]
  ) => void;
}

interface Source {
  title?: string;
  year?: number;
  authors?: string[];
  summary?: string;
}

interface AnswerResponse {
  answer: string;
  sources: Source[];
}

async function fetchAnswer(query: string, top_k: number = 3): Promise<AnswerResponse> {
  const response = await fetch(`http://${process.env.NEXT_PUBLIC_API_URL}:8000/query`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ query, top_k }),
  });

  const raw = await response.text();
  console.log("📦 Raw Response Text:", raw);

  if (!response.ok) {
    throw new Error("❌ 답변을 가져오는 데 실패했습니다.");
  }

  return JSON.parse(raw);
}

export default function ChatBot({ isOpen, onClose, messages, onSendMessage }: ChatBotProps) {
  const [inputMessage, setInputMessage] = useState('');

  const handleSend = async () => {
    if (inputMessage.trim()) {
      const userMessage = inputMessage.trim();
      onSendMessage(userMessage, 'user');
      setInputMessage('');

      try {
        const { answer, sources } = await fetchAnswer(userMessage, 3);
        onSendMessage(answer, 'assistant', sources);
      } catch (error) {
        console.error('❌ LLM 응답 실패:', error);
        onSendMessage('⚠️ 답변을 불러오지 못했습니다. 다시 시도해주세요.', 'assistant');
      }
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  if (!isOpen) return null;

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      zIndex: 50,
      display: 'flex',
      alignItems: 'flex-end',
      justifyContent: 'flex-end',
      padding: 'clamp(1rem, 2vw, 2rem)'
    }}>
      <div style={{
        width: '40vw',
        height: '90vh',
        background: 'white',
        borderRadius: 'clamp(12px, 2vw, 20px)',
        boxShadow: '0 20px 40px rgba(0, 0, 0, 0.15)',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden'
      }}>
        {/* 헤더 */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: 'clamp(1rem, 3vh, 1.5rem) clamp(1rem, 3vw, 1.5rem)',
          borderBottom: '2px solid #f1f5f9',
          background: '#4f46e5',
          color: 'white'
        }}>
          <h3 style={{
            fontSize: 'clamp(1rem, 2.5vw, 1.25rem)',
            fontWeight: 600,
            margin: 0
          }}>
            논문 분석 도우미 챗봇
          </h3>
          <button
            onClick={onClose}
            style={{
              padding: 'clamp(0.25rem, 0.5vh, 0.5rem)',
              background: 'rgba(255, 255, 255, 0.1)',
              border: 'none',
              borderRadius: 'clamp(4px, 0.5vw, 6px)',
              color: 'white',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = 'rgba(255, 255, 255, 0.2)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = 'rgba(255, 255, 255, 0.1)';
            }}
          >
            <X style={{ 
              width: 'clamp(16px, 2vw, 20px)', 
              height: 'clamp(16px, 2vw, 20px)' 
            }} />
          </button>
        </div>
        
        {/* 메시지 영역 */}
        <div style={{
          flex: 1,
          padding: 'clamp(1rem, 3vh, 1.5rem)',
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column',
          gap: 'clamp(0.75rem, 2vh, 1rem)'
        }}>
          {messages.length === 0 ? (
            <div>안녕하세요. 논문 분석 도우미 챗봇🤖입니다. 무엇이든 물어보세요.</div>
          ) : messages.map((message) => (
            <div
              key={message.id}
              style={{
                display: 'flex',
                justifyContent: message.type === 'user' ? 'flex-end' : 'flex-start',
              }}
            >
              <div
                style={{
                  maxWidth: '80%',
                  padding: 'clamp(0.5rem, 1.5vh, 0.75rem) clamp(0.75rem, 2vw, 1rem)',
                  borderRadius: 'clamp(8px, 1.5vw, 12px)',
                  fontSize: 'clamp(0.875rem, 1.8vw, 1rem)',
                  lineHeight: 1.4,
                  background: message.type === 'user' ? '#4f46e5' : '#f3f4f6',
                  color: message.type === 'user' ? 'white' : '#111827',
                  whiteSpace: 'pre-wrap',
                }}
              >
                {message.content}
                {message.type === 'assistant' && message.sources && message.sources.length > 0 && (
                  <div style={{ marginTop: '0.5rem', fontSize: '0.85em', color: '#6b7280' }}>
                    🔗 출처:
                    <ul style={{ paddingLeft: '1rem', margin: 0 }}>
                      {message.sources.map((src, idx) => (
                        <li key={idx}>
                          <strong>{src.title || '제목 없음'}</strong>
                          {src.year && ` (${src.year})`}<br />
                          {src.authors?.join(', ')}<br />
                          {src.summary && <em>{src.summary}</em>}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
        
        {/* 입력 영역 */}
        <div style={{
          padding: 'clamp(1rem, 3vh, 1.5rem)',
          borderTop: '1px solid #e5e7eb',
          background: '#fafbfc'
        }}>
          <div style={{
            display: 'flex',
            gap: 'clamp(0.5rem, 1vw, 0.75rem)'
          }}>
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="메시지를 입력하세요..."
              style={{
                flex: 1,
                padding: 'clamp(0.5rem, 1.5vh, 0.75rem) clamp(0.75rem, 2vw, 1rem)',
                border: '1px solid #d1d5db',
                borderRadius: 'clamp(6px, 1vw, 10px)',
                fontSize: 'clamp(0.875rem, 1.8vw, 1rem)',
                background: 'white',
                transition: 'all 0.2s ease',
                outline: 'none'
              }}
              onFocus={(e) => {
                e.currentTarget.style.borderColor = '#4f46e5';
                e.currentTarget.style.boxShadow = '0 0 0 3px rgba(79, 70, 229, 0.1)';
              }}
              onBlur={(e) => {
                e.currentTarget.style.borderColor = '#d1d5db';
                e.currentTarget.style.boxShadow = 'none';
              }}
            />
            <button
              onClick={handleSend}
              disabled={!inputMessage.trim()}
              style={{
                padding: 'clamp(0.5rem, 1.5vh, 0.75rem)',
                background: inputMessage.trim() ? '#4f46e5' : '#d1d5db',
                color: 'white',
                border: 'none',
                borderRadius: 'clamp(6px, 1vw, 10px)',
                cursor: inputMessage.trim() ? 'pointer' : 'not-allowed',
                transition: 'all 0.2s ease',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
              onMouseEnter={(e) => {
                if (inputMessage.trim()) {
                  e.currentTarget.style.background = '#4338ca';
                  e.currentTarget.style.transform = 'translateY(-1px)';
                }
              }}
              onMouseLeave={(e) => {
                if (inputMessage.trim()) {
                  e.currentTarget.style.background = '#4f46e5';
                  e.currentTarget.style.transform = 'none';
                }
              }}
            >
              <Send style={{ 
                width: 'clamp(16px, 2vw, 20px)', 
                height: 'clamp(16px, 2vw, 20px)' 
              }} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
} 