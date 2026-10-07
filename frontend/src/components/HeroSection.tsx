import React from 'react';
import { Sparkles, Shield, Cpu } from 'lucide-react';

interface HeroSectionProps {
  onLearnMore?: () => void;
}

export const HeroSection: React.FC<HeroSectionProps> = ({ onLearnMore }) => {
  return (
    <div
      style={{
        position: 'absolute',
        left: '28px',
        top: '90px',
        bottom: '28px',
        width: '420px',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        pointerEvents: 'none',
        zIndex: 20,
      }}
    >
      {/* Top Text Content */}
      <div>
        {/* Intro Subtitle */}
        <div
          style={{
            fontFamily: 'var(--font-tech)',
            fontSize: '0.80rem',
            color: '#6f717a',
            marginBottom: '18px',
            letterSpacing: '0.04em',
            textTransform: 'uppercase',
          }}
        >
          CaptainShield &bull; Adaptive DDoS Defense & Rate Limiting
        </div>

        {/* Display Headline */}
        <h1
          style={{
            fontFamily: 'var(--font-display)',
            fontSize: '2.55rem',
            fontWeight: 800,
            lineHeight: 1.18,
            letterSpacing: '0.06em',
            color: '#f4f4f4',
            textTransform: 'uppercase',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span>CONTROLLED</span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span
              style={{
                color: '#ffd83d',
                textShadow: '0 0 20px rgba(255, 216, 61, 0.45)',
                fontFamily: "var(--font-tech), 'Inter', sans-serif",
                fontWeight: 900,
                letterSpacing: '0.06em',
                textTransform: 'none',
              }}
            >
              DDoS
            </span>
            <Sparkles size={20} color="#ffd83d" style={{ filter: 'drop-shadow(0 0 8px #ffd83d)' }} />
            <span>SIMULATION</span>
          </div>

          <div>& ADAPTIVE</div>

          <div
            style={{
              color: '#ffd83d',
              textShadow: '0 0 20px rgba(255, 216, 61, 0.45)',
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
            }}
          >
            <Shield size={20} color="#ffd83d" style={{ filter: 'drop-shadow(0 0 8px #ffd83d)' }} />
            <span>RATE DEFENSE</span>
          </div>
        </h1>
      </div>

      {/* Bottom Info Pill (Matches reference's lower-left info pill) */}
      <div
        onClick={onLearnMore}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          padding: '12px 16px',
          borderRadius: '16px',
          backgroundColor: 'rgba(20, 23, 33, 0.85)',
          backdropFilter: 'blur(16px)',
          border: '1px solid rgba(255, 255, 255, 0.07)',
          boxShadow: '0 10px 25px rgba(0, 0, 0, 0.4)',
          width: 'fit-content',
          maxWidth: '340px',
          cursor: 'pointer',
          pointerEvents: 'auto',
          transition: 'all 0.2s ease',
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.borderColor = 'rgba(255, 216, 61, 0.3)';
          e.currentTarget.style.transform = 'translateY(-2px)';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.07)';
          e.currentTarget.style.transform = 'translateY(0)';
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: '28px',
            height: '28px',
            borderRadius: '8px',
            backgroundColor: 'rgba(255, 255, 255, 0.04)',
            border: '1px solid rgba(255, 255, 255, 0.08)',
          }}
        >
          <Cpu size={15} color="#ffd83d" />
        </div>
        <div
          style={{
            fontFamily: 'var(--font-tech)',
            fontSize: '0.72rem',
            color: '#b8bac2',
            lineHeight: 1.35,
          }}
        >
          Autonomous ML defense active on over 13 000 nodes worldwide
        </div>
      </div>
    </div>
  );
};
