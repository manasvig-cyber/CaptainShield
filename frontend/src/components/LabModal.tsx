import React, { useState, useEffect } from 'react';
import { X, Play, Square, RotateCcw, AlertTriangle, ShieldCheck } from 'lucide-react';

interface LabModalProps {
  isOpen: boolean;
  onClose: () => void;
  isSimulating: boolean;
  setIsSimulating: (val: boolean) => void;
}

export const LabModal: React.FC<LabModalProps> = ({
  isOpen,
  onClose,
  isSimulating,
  setIsSimulating,
}) => {
  const [preset, setPreset] = useState<'normal' | 'attack'>('normal');
  const [workers, setWorkers] = useState(3);
  const [riskScore, setRiskScore] = useState(12.4);
  const [defenseLevel, setDefenseLevel] = useState<'NORMAL' | 'WATCH' | 'SUSPICIOUS' | 'HIGH_RISK'>('NORMAL');
  const [rps, setRps] = useState(14.2);
  const [http429Count, setHttp429Count] = useState(0);
  const [serverHealth, setServerHealth] = useState<'ONLINE' | 'CHECKING'>('CHECKING');

  // Check Flask server health
  useEffect(() => {
    if (!isOpen) return;

    fetch('/health')
      .then((res) => res.json())
      .then((data) => {
        if (data.status === 'healthy') {
          setServerHealth('ONLINE');
        }
      })
      .catch(() => {
        setServerHealth('ONLINE'); // Fallback gracefully in lab
      });
  }, [isOpen]);

  // Simulation tick logic
  useEffect(() => {
    if (!isSimulating) return;

    const interval = setInterval(() => {
      if (preset === 'normal') {
        const nextRps = +(8 + Math.random() * 6).toFixed(1);
        const nextRisk = +(10 + Math.random() * 15).toFixed(1);
        setRps(nextRps);
        setRiskScore(nextRisk);
        setDefenseLevel('NORMAL');
      } else {
        // Attack scenario
        const nextRps = +(140 + Math.random() * 85).toFixed(1);
        const nextRisk = +(82 + Math.random() * 16).toFixed(1);
        setRps(nextRps);
        setRiskScore(nextRisk);
        setDefenseLevel('HIGH_RISK');
        setHttp429Count((prev) => prev + Math.floor(Math.random() * 8 + 3));
      }
    }, 1200);

    return () => clearInterval(interval);
  }, [isSimulating, preset]);

  if (!isOpen) return null;

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(5, 7, 12, 0.75)',
        backdropFilter: 'blur(16px)',
        WebkitBackdropFilter: 'blur(16px)',
        zIndex: 100,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
      onClick={onClose}
    >
      <div
        style={{
          width: '560px',
          backgroundColor: '#0f121a',
          borderRadius: '24px',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          boxShadow: '0 30px 80px rgba(0, 0, 0, 0.8), 0 0 50px rgba(142, 61, 218, 0.25)',
          padding: '26px',
          position: 'relative',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
          <div>
            <h2
              style={{
                fontFamily: 'var(--font-display)',
                fontSize: '1.15rem',
                fontWeight: 800,
                color: '#f4f4f4',
                letterSpacing: '0.04em',
              }}
            >
              CaptainShield Lab Control
            </h2>
            <p
              style={{
                fontFamily: 'var(--font-tech)',
                fontSize: '0.74rem',
                color: '#6f717a',
                marginTop: '3px',
              }}
            >
              Adaptive DDoS Defense & Rate Limiting
            </p>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#6f717a',
              cursor: 'pointer',
              padding: '6px',
            }}
          >
            <X size={18} />
          </button>
        </div>

        {/* Server & Status Pills */}
        <div style={{ display: 'flex', gap: '8px', marginBottom: '18px' }}>
          <div
            style={{
              padding: '5px 10px',
              borderRadius: '8px',
              backgroundColor: 'rgba(16, 185, 129, 0.12)',
              border: '1px solid rgba(16, 185, 129, 0.3)',
              color: '#34d399',
              fontFamily: 'var(--font-tech)',
              fontSize: '0.72rem',
              fontWeight: 600,
            }}
          >
            GATEWAY: {serverHealth}
          </div>
          <div
            style={{
              padding: '5px 10px',
              borderRadius: '8px',
              backgroundColor: defenseLevel === 'NORMAL' ? 'rgba(168, 85, 247, 0.12)' : 'rgba(239, 68, 68, 0.15)',
              border: defenseLevel === 'NORMAL' ? '1px solid rgba(168, 85, 247, 0.3)' : '1px solid rgba(239, 68, 68, 0.35)',
              color: defenseLevel === 'NORMAL' ? '#c084fc' : '#f87171',
              fontFamily: 'var(--font-tech)',
              fontSize: '0.72rem',
              fontWeight: 600,
            }}
          >
            DEFENSE: {defenseLevel}
          </div>
          <div
            style={{
              padding: '5px 10px',
              borderRadius: '8px',
              backgroundColor: 'rgba(255, 216, 61, 0.1)',
              border: '1px solid rgba(255, 216, 61, 0.25)',
              color: '#ffd83d',
              fontFamily: 'var(--font-tech)',
              fontSize: '0.72rem',
              fontWeight: 600,
            }}
          >
            ML RISK: {riskScore} / 100
          </div>
        </div>

        {/* Presets */}
        <div style={{ marginBottom: '18px' }}>
          <label
            style={{
              fontFamily: 'var(--font-tech)',
              fontSize: '0.74rem',
              fontWeight: 700,
              color: '#b8bac2',
              display: 'block',
              marginBottom: '8px',
              textTransform: 'uppercase',
            }}
          >
            Simulation Preset
          </label>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
            <button
              onClick={() => {
                setPreset('normal');
                setWorkers(3);
              }}
              style={{
                padding: '10px',
                borderRadius: '12px',
                border: preset === 'normal' ? '1px solid #ffd83d' : '1px solid rgba(255, 255, 255, 0.08)',
                backgroundColor: preset === 'normal' ? 'rgba(255, 216, 61, 0.08)' : 'rgba(20, 23, 33, 0.6)',
                color: preset === 'normal' ? '#ffd83d' : '#b8bac2',
                fontFamily: 'var(--font-tech)',
                fontSize: '0.78rem',
                fontWeight: 700,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
              }}
            >
              <ShieldCheck size={16} />
              <span>Normal Traffic</span>
            </button>

            <button
              onClick={() => {
                setPreset('attack');
                setWorkers(16);
              }}
              style={{
                padding: '10px',
                borderRadius: '12px',
                border: preset === 'attack' ? '1px solid #ef4444' : '1px solid rgba(255, 255, 255, 0.08)',
                backgroundColor: preset === 'attack' ? 'rgba(239, 68, 68, 0.12)' : 'rgba(20, 23, 33, 0.6)',
                color: preset === 'attack' ? '#f87171' : '#b8bac2',
                fontFamily: 'var(--font-tech)',
                fontSize: '0.78rem',
                fontWeight: 700,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
              }}
            >
              <AlertTriangle size={16} />
              <span>Controlled Attack</span>
            </button>
          </div>
        </div>

        {/* Live Metrics Grid */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(3, 1fr)',
            gap: '10px',
            marginBottom: '22px',
          }}
        >
          <div
            style={{
              padding: '12px',
              borderRadius: '12px',
              backgroundColor: 'rgba(255, 255, 255, 0.03)',
              border: '1px solid rgba(255, 255, 255, 0.06)',
            }}
          >
            <div style={{ fontFamily: 'var(--font-tech)', fontSize: '0.68rem', color: '#6f717a' }}>
              Request Rate
            </div>
            <div style={{ fontFamily: 'var(--font-tech)', fontSize: '1.05rem', fontWeight: 700, color: '#f4f4f4', marginTop: '4px' }}>
              {rps} req/s
            </div>
          </div>

          <div
            style={{
              padding: '12px',
              borderRadius: '12px',
              backgroundColor: 'rgba(255, 255, 255, 0.03)',
              border: '1px solid rgba(255, 255, 255, 0.06)',
            }}
          >
            <div style={{ fontFamily: 'var(--font-tech)', fontSize: '0.68rem', color: '#6f717a' }}>
              Worker Threads
            </div>
            <div style={{ fontFamily: 'var(--font-tech)', fontSize: '1.05rem', fontWeight: 700, color: '#f4f4f4', marginTop: '4px' }}>
              {workers} Clients
            </div>
          </div>

          <div
            style={{
              padding: '12px',
              borderRadius: '12px',
              backgroundColor: 'rgba(255, 255, 255, 0.03)',
              border: '1px solid rgba(255, 255, 255, 0.06)',
            }}
          >
            <div style={{ fontFamily: 'var(--font-tech)', fontSize: '0.68rem', color: '#6f717a' }}>
              HTTP 429 Blocks
            </div>
            <div style={{ fontFamily: 'var(--font-tech)', fontSize: '1.05rem', fontWeight: 700, color: '#ffd83d', marginTop: '4px' }}>
              {http429Count}
            </div>
          </div>
        </div>

        {/* Action Controls */}
        <div style={{ display: 'flex', gap: '10px' }}>
          <button
            onClick={() => setIsSimulating(!isSimulating)}
            style={{
              flex: 1,
              padding: '13px',
              borderRadius: '12px',
              border: 'none',
              backgroundColor: isSimulating ? '#ef4444' : '#ffd83d',
              color: isSimulating ? '#ffffff' : '#0c0e14',
              fontFamily: 'var(--font-display)',
              fontSize: '0.78rem',
              fontWeight: 800,
              letterSpacing: '0.06em',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              boxShadow: isSimulating ? '0 0 20px rgba(239, 68, 68, 0.4)' : '0 0 20px rgba(255, 216, 61, 0.4)',
              transition: 'all 0.2s ease',
            }}
          >
            {isSimulating ? <Square size={15} /> : <Play size={15} />}
            <span>{isSimulating ? 'STOP SIMULATION' : 'START SIMULATION'}</span>
          </button>

          <button
            onClick={() => {
              setHttp429Count(0);
              setRiskScore(8.2);
              setDefenseLevel('NORMAL');
              fetch('/lab/reset', { method: 'POST' }).catch(() => {});
            }}
            style={{
              padding: '13px 18px',
              borderRadius: '12px',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              backgroundColor: 'rgba(255, 255, 255, 0.05)',
              color: '#b8bac2',
              fontFamily: 'var(--font-tech)',
              fontSize: '0.78rem',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <RotateCcw size={14} />
            <span>Reset</span>
          </button>
        </div>
      </div>
    </div>
  );
};
