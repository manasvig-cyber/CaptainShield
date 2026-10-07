import React, { useState } from 'react';

interface CTAButtonProps {
  label: string;
  onClick?: () => void;
  className?: string;
  disabled?: boolean;
}

export const CTAButton: React.FC<CTAButtonProps> = ({
  label,
  onClick,
  disabled = false,
}) => {
  const [isHovered, setIsHovered] = useState(false);
  const [isPressed, setIsPressed] = useState(false);

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => {
        setIsHovered(false);
        setIsPressed(false);
      }}
      onMouseDown={() => setIsPressed(true)}
      onMouseUp={() => setIsPressed(false)}
      style={{
        width: '100%',
        padding: '13px 18px',
        backgroundColor: '#ffd83d',
        color: '#0c0e14',
        border: 'none',
        borderRadius: '14px',
        fontFamily: 'var(--font-display)',
        fontSize: '0.78rem',
        fontWeight: 800,
        letterSpacing: '0.08em',
        textTransform: 'uppercase',
        cursor: disabled ? 'not-allowed' : 'pointer',
        transform: isPressed ? 'scale(0.97)' : isHovered ? 'scale(1.02)' : 'scale(1)',
        boxShadow: isHovered
          ? '0 0 25px rgba(255, 216, 61, 0.5), 0 4px 15px rgba(0, 0, 0, 0.4)'
          : '0 0 14px rgba(255, 216, 61, 0.25)',
        transition: 'all 0.22s cubic-bezier(0.16, 1, 0.3, 1)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '8px',
        outline: 'none',
      }}
    >
      <span>{label}</span>
    </button>
  );
};
