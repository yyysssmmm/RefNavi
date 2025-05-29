'use client';

import { HelpCircle } from 'lucide-react';

interface FloatingButtonProps {
  onClick: () => void;
  className?: string;
}

export default function FloatingButton({ onClick, className }: FloatingButtonProps) {
  return (
    <button
      onClick={onClick}
      style={{
        position: 'fixed',
        bottom: 'clamp(1rem, 3vh, 2rem)',
        right: 'clamp(1rem, 3vw, 2rem)',
        zIndex: 50,
        width: 'clamp(48px, 8vw, 64px)',
        height: 'clamp(48px, 8vw, 64px)',
        background: '#4f46e5',
        borderRadius: '50%',
        border: 'none',
        boxShadow: '0 8px 20px rgba(79, 70, 229, 0.3)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: 'white',
        cursor: 'pointer',
        transition: 'all 0.2s ease'
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.background = '#4338ca';
        e.currentTarget.style.transform = 'translateY(-2px)';
        e.currentTarget.style.boxShadow = '0 12px 24px rgba(79, 70, 229, 0.4)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.background = '#4f46e5';
        e.currentTarget.style.transform = 'none';
        e.currentTarget.style.boxShadow = '0 8px 20px rgba(79, 70, 229, 0.3)';
      }}
      className={className}
      aria-label="도움말 챗봇 열기"
    >
      <HelpCircle style={{ 
        width: 'clamp(20px, 4vw, 28px)', 
        height: 'clamp(20px, 4vw, 28px)' 
      }} />
    </button>
  );
} 