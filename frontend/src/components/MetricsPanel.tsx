import React from 'react';
import { ShieldCheck, Ban, AlertTriangle, Activity, FileText, Radio } from 'lucide-react';
import { CircularProgress } from './CircularProgress';
import { CTAButton } from './CTAButton';

interface MetricsPanelProps {
  isSimulating?: boolean;
  capacity?: number;
  requestsSent?: number;
  successfulRequests?: number;
  blockedRequests?: number;
  activeClients?: number;
  telemetryCount?: number;
  incidentCount?: number;
  onStartAttack?: () => void;
  onStopSimulation?: () => void;
  onOpenLiveSOC?: () => void;
}

export const MetricsPanel: React.FC<MetricsPanelProps> = ({
  isSimulating = false,
  capacity = 100.0,
  requestsSent = 0,
  successfulRequests = 0,
  blockedRequests = 0,
  activeClients = 0,
  telemetryCount = 0,
  incidentCount = 0,
  onStartAttack,
  onStopSimulation,
  onOpenLiveSOC,
}) => {
  // Format numbers nicely with space separation
  const fmt = (n: number) => n.toLocaleString();

  const metrics = [
    {
      icon: <ShieldCheck size={16} color="#36c7ff" />,
      title: 'Benign Ingress',
      subtitle: `${fmt(successfulRequests)} reqs`,
      value: `${((successfulRequests * 256) / (1024 * 1024)).toFixed(1)} MB`,
    },
    {
      icon: <Ban size={16} color={blockedRequests > 0 ? '#ffd23f' : '#8b98aa'} />,
      title: 'Rate-Limited 429',
      subtitle: `${fmt(blockedRequests)} blocks`,
      value: `${((blockedRequests * 128) / (1024 * 1024)).toFixed(1)} MB`,
    },
    {
      icon: <AlertTriangle size={16} color={activeClients > 10 ? '#ff454a' : '#36c7ff'} />,
      title: 'Quarantined IPs',
      subtitle: `${activeClients} nodes`,
      value: isSimulating ? 'ACTIVE' : 'READY',
    },
    {
      icon: <Activity size={16} color="#36c7ff" />,
      title: 'Telemetry Stream',
      subtitle: `${fmt(telemetryCount || requestsSent)} events`,
      value: '7-FEATS',
    },
    {
      icon: <FileText size={16} color={incidentCount > 0 ? '#ffd23f' : '#22d3a2'} />,
      title: 'Incident Forensics',
      subtitle: `${incidentCount} detected`,
      value: incidentCount > 0 ? 'ALERT' : 'NORMAL',
    },
  ];

  return (
    <div
      style={{
        position: 'absolute',
        right: '24px',
        top: '68px',
        bottom: '24px',
        width: '240px',
        backgroundColor: '#101927',
        borderRadius: '20px',
        border: '1px solid var(--border-subtle)',
        boxShadow: '0 20px 50px rgba(0, 0, 0, 0.7), inset 0 1px 1px rgba(255, 255, 255, 0.08)',
        display: 'flex',
        flexDirection: 'column',
        padding: '20px 18px',
        zIndex: 20,
        pointerEvents: 'auto',
      }}
    >
      {/* Panel Header */}
      <div
        style={{
          fontFamily: 'var(--font-display)',
          fontSize: '0.78rem',
          fontWeight: 700,
          letterSpacing: '0.08em',
          color: '#f3f7fa',
          textAlign: 'center',
          textTransform: 'uppercase',
          marginBottom: '14px',
        }}
      >
        Defense Capacity
      </div>

      {/* Circular Progress Gauge */}
      <div style={{ marginBottom: '14px' }}>
        <CircularProgress
          percentage={Math.round(capacity)}
          value={isSimulating ? `${capacity.toFixed(0)}%` : '375 GB'}
          subtext={isSimulating ? 'DEFENSE INTEGRITY' : 'of 500 GB'}
          size={165}
          strokeWidth={9}
        />
      </div>

      {/* Metric Breakdown Rows */}
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '11px',
          flex: 1,
          justifyContent: 'center',
          marginBottom: '14px',
        }}
      >
        {metrics.map((row, index) => (
          <div
            key={index}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '2px 4px',
            }}
          >
            {/* Left: Icon and Titles */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  width: '24px',
                  height: '24px',
                  borderRadius: '6px',
                  backgroundColor: 'rgba(255, 255, 255, 0.03)',
                }}
              >
                {row.icon}
              </div>
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <span
                  style={{
                    fontFamily: 'var(--font-tech)',
                    fontSize: '0.76rem',
                    fontWeight: 600,
                    color: '#f3f7fa',
                    lineHeight: 1.1,
                  }}
                >
                  {row.title}
                </span>
                <span
                  style={{
                    fontFamily: 'var(--font-tech)',
                    fontSize: '0.66rem',
                    color: '#8b98aa',
                    marginTop: '2px',
                  }}
                >
                  {row.subtitle}
                </span>
              </div>
            </div>

            {/* Right: Numeric Value */}
            <div
              style={{
                fontFamily: 'var(--font-tech)',
                fontSize: '0.76rem',
                fontWeight: 700,
                color: '#36c7ff',
              }}
            >
              {row.value}
            </div>
          </div>
        ))}
      </div>

      {/* Primary Action Button (START ATTACK vs STOP SIMULATION / EMERGENCY STOP) */}
      <div style={{ marginTop: 'auto', display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {isSimulating ? (
          <>
            <button
              onClick={onOpenLiveSOC}
              style={{
                width: '100%',
                padding: '11px 14px',
                backgroundColor: 'rgba(239, 68, 68, 0.2)',
                color: '#ff454a',
                border: '1px solid rgba(239, 68, 68, 0.6)',
                borderRadius: '10px',
                fontFamily: 'var(--font-display)',
                fontSize: '0.72rem',
                fontWeight: 800,
                letterSpacing: '0.06em',
                textTransform: 'uppercase',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
                boxShadow: '0 0 15px rgba(239, 68, 68, 0.25)',
                transition: 'all 0.2s ease',
              }}
            >
              <Radio size={14} className="pulse" />
              <span>VIEW LIVE ATTACK</span>
            </button>
            <button
              onClick={onStopSimulation}
              style={{
                width: '100%',
                padding: '10px 14px',
                backgroundColor: '#ef4444',
                color: '#ffffff',
                border: '1px solid rgba(255, 69, 74, 0.8)',
                borderRadius: '10px',
                fontFamily: 'var(--font-display)',
                fontSize: '0.70rem',
                fontWeight: 800,
                letterSpacing: '0.06em',
                textTransform: 'uppercase',
                cursor: 'pointer',
                boxShadow: '0 0 20px rgba(239, 68, 68, 0.5)',
                transition: 'all 0.2s ease',
                outline: 'none',
              }}
            >
              STOP SIMULATION
            </button>
          </>
        ) : (
          <CTAButton
            label="START ATTACK"
            onClick={onStartAttack}
          />
        )}
      </div>
    </div>
  );
};
