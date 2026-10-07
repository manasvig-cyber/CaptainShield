import React from 'react';
import { ArrowRight, Shield, Activity, Cpu, AlertTriangle, Lock, FileCode, CheckCircle } from 'lucide-react';

interface DefensePipelineProps {
  isRunning: boolean;
  riskScore?: number;
  defenseLevel?: string;
  rateLimitAction?: string;
  has429?: boolean;
}

export const DefensePipeline: React.FC<DefensePipelineProps> = ({
  isRunning,
  riskScore = 0.0,
  defenseLevel = 'NORMAL',
  rateLimitAction = 'NORMAL_RATE_LIMIT',
  has429 = false,
}) => {
  const isHighRisk = riskScore >= 75;
  const isAnomaly = riskScore >= 60;

  const stages = [
    {
      title: 'TRAFFIC',
      value: isRunning ? 'ACTIVE' : 'READY',
      icon: <Activity size={12} />,
      statusColor: isRunning ? '#36c7ff' : '#8b98aa',
    },
    {
      title: 'TELEMETRY',
      value: isRunning ? '7-FEATURES' : 'STANDBY',
      icon: <FileCode size={12} />,
      statusColor: isRunning ? '#36c7ff' : '#8b98aa',
    },
    {
      title: 'ML DETECTOR',
      value: isAnomaly ? 'ANOMALY' : 'NORMAL',
      icon: <Cpu size={12} />,
      statusColor: isAnomaly ? '#ff454a' : '#22d3a2',
    },
    {
      title: 'RISK SCORE',
      value: `${riskScore.toFixed(1)}/100`,
      icon: <AlertTriangle size={12} />,
      statusColor: isHighRisk ? '#ff454a' : isAnomaly ? '#ffd23f' : '#22d3a2',
    },
    {
      title: 'ADAPTIVE DEFENSE',
      value: defenseLevel,
      icon: <Shield size={12} />,
      statusColor: defenseLevel === 'HIGH_RISK' ? '#ff454a' : defenseLevel === 'SUSPICIOUS' ? '#ffd23f' : '#36c7ff',
    },
    {
      title: 'RATE LIMITER',
      value: rateLimitAction.replace('_', ' '),
      icon: <Lock size={12} />,
      statusColor: has429 ? '#ff454a' : '#22d3a2',
    },
    {
      title: 'HTTP RESPONSE',
      value: has429 ? '200 / 429' : '200 OK',
      icon: <CheckCircle size={12} />,
      statusColor: has429 ? '#ffd23f' : '#22d3a2',
    },
  ];

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '6px',
        padding: '8px 14px',
        borderRadius: '12px',
        backgroundColor: '#0a111c',
        border: '1px solid var(--border-subtle)',
        boxShadow: '0 8px 24px rgba(0, 0, 0, 0.45)',
        width: 'fit-content',
        maxWidth: '100%',
        overflowX: 'auto',
      }}
    >
      <div
        style={{
          fontFamily: 'var(--font-display)',
          fontSize: '0.64rem',
          fontWeight: 800,
          color: '#8b98aa',
          marginRight: '8px',
          letterSpacing: '0.06em',
          whiteSpace: 'nowrap',
        }}
      >
        PIPELINE
      </div>

      {stages.map((stage, idx) => (
        <React.Fragment key={idx}>
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              padding: '4px 8px',
              borderRadius: '6px',
              backgroundColor: '#101927',
              border: `1px solid ${stage.statusColor}33`,
              minWidth: '95px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <span style={{ color: stage.statusColor }}>{stage.icon}</span>
              <span
                style={{
                  fontFamily: 'var(--font-tech)',
                  fontSize: '0.62rem',
                  color: '#8b98aa',
                  fontWeight: 600,
                  whiteSpace: 'nowrap',
                }}
              >
                {stage.title}
              </span>
            </div>
            <div
              style={{
                fontFamily: 'var(--font-display)',
                fontSize: '0.68rem',
                fontWeight: 700,
                color: stage.statusColor,
                marginTop: '2px',
                whiteSpace: 'nowrap',
              }}
            >
              {stage.value}
            </div>
          </div>
          {idx < stages.length - 1 && (
            <ArrowRight size={12} color="rgba(90, 140, 190, 0.4)" style={{ flexShrink: 0 }} />
          )}
        </React.Fragment>
      ))}
    </div>
  );
};
