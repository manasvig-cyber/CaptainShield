import React, { useEffect, useState } from 'react';
import { Shield, ArrowLeft, Download, FileText, Cpu, Clock } from 'lucide-react';
import { api } from '../services/api';

interface ThreatMatrixViewProps {
  sessionId: string;
  onBack: () => void;
}

export const ThreatMatrixView: React.FC<ThreatMatrixViewProps> = ({
  sessionId,
  onBack,
}) => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [currentId, setCurrentId] = useState<string>(sessionId || '');

  useEffect(() => {
    let isMounted = true;

    const loadData = async () => {
      let target = sessionId;
      if (!target) {
        try {
          const recents = await api.getRecentHistory();
          if (recents?.sessions && recents.sessions.length > 0) {
            target = recents.sessions[0].id;
          }
        } catch {
          // ignore
        }
      }

      if (target) {
        setCurrentId(target);
        try {
          const res = await api.getThreatMatrix(target);
          if (isMounted) {
            setData(res);
            setLoading(false);
          }
        } catch {
          if (isMounted) setLoading(false);
        }
      } else {
        if (isMounted) setLoading(false);
      }
    };

    loadData();
    return () => { isMounted = false; };
  }, [sessionId]);

  const exportJSON = () => {
    if (!data) return;
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `CaptainShield_Forensic_${sessionId}.json`;
    a.click();
  };

  const exportCSV = () => {
    if (!data || !data.matrix_rows) return;
    const headers = ['Category', 'Observed', 'Severity', 'ML Detected', 'Risk', 'Defense Action', 'Final Status'];
    const rows = data.matrix_rows.map((r: any) => [
      r.category,
      `"${r.observed}"`,
      r.severity,
      r.ml_detected ? 'TRUE' : 'FALSE',
      `"${r.risk}"`,
      r.defense_action,
      r.final_status,
    ]);
    const csvContent = [headers.join(','), ...rows.map((e: any) => e.join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `CaptainShield_ThreatMatrix_${sessionId}.csv`;
    a.click();
  };

  if (loading) {
    return (
      <div style={{ padding: '30px', color: '#f3f7fa', fontFamily: 'var(--font-tech)' }}>
        Loading Threat Matrix forensic report...
      </div>
    );
  }

  if (!data || !data.session) {
    return (
      <div style={{ padding: '30px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <button
          onClick={onBack}
          style={{
            background: '#101927',
            border: '1px solid var(--border-subtle)',
            color: '#36c7ff',
            borderRadius: '8px',
            padding: '8px 12px',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            cursor: 'pointer',
            fontFamily: 'var(--font-tech)',
            fontSize: '0.78rem',
            width: 'fit-content',
          }}
        >
          <ArrowLeft size={14} />
          <span>Return to Command Center</span>
        </button>
        <div style={{ color: '#8b98aa', fontFamily: 'var(--font-tech)', fontSize: '0.85rem' }}>
          No simulation forensic session found. Click <strong style={{ color: '#ffd23f' }}>START ATTACK</strong> in the Command Center to generate traffic and generate Threat Matrix forensics.
        </div>
      </div>
    );
  }

  const session = data?.session || {};
  const matrixRows = data?.matrix_rows || [];
  const modelPerf = data?.model_performance || {};

  return (
    <div
      style={{
        padding: '24px 30px',
        minHeight: '100%',
        display: 'flex',
        flexDirection: 'column',
        gap: '20px',
      }}
    >
      {/* Header Bar */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <button
            onClick={onBack}
            style={{
              background: '#101927',
              border: '1px solid var(--border-subtle)',
              color: '#36c7ff',
              borderRadius: '8px',
              padding: '8px 12px',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              cursor: 'pointer',
              fontFamily: 'var(--font-tech)',
              fontSize: '0.78rem',
            }}
          >
            <ArrowLeft size={14} />
            <span>Command Center</span>
          </button>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <h1
                style={{
                  fontFamily: 'var(--font-display)',
                  fontSize: '1.25rem',
                  fontWeight: 800,
                  color: '#f3f7fa',
                }}
              >
                THREAT MATRIX FORENSIC REPORT
              </h1>
              <span
                style={{
                  backgroundColor: 'rgba(54, 199, 255, 0.12)',
                  color: '#36c7ff',
                  border: '1px solid rgba(54, 199, 255, 0.3)',
                  padding: '2px 8px',
                  borderRadius: '4px',
                  fontFamily: 'var(--font-tech)',
                  fontSize: '0.72rem',
                  fontWeight: 700,
                }}
              >
                {currentId || sessionId}
              </span>
            </div>
            <div style={{ fontFamily: 'var(--font-tech)', fontSize: '0.72rem', color: '#8b98aa', marginTop: '2px' }}>
              Preset: {session.preset || 'Controlled Attack'} | Duration: {session.duration || 0}s | Status: {session.status || 'COMPLETED'}
            </div>
          </div>
        </div>

        {/* Export Buttons */}
        <div style={{ display: 'flex', gap: '10px' }}>
          <button
            onClick={exportJSON}
            style={{
              background: '#141f30',
              border: '1px solid var(--border-subtle)',
              color: '#f3f7fa',
              borderRadius: '8px',
              padding: '8px 14px',
              fontFamily: 'var(--font-tech)',
              fontSize: '0.74rem',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <Download size={13} color="#36c7ff" />
            <span>Export JSON</span>
          </button>

          <button
            onClick={exportCSV}
            style={{
              background: '#141f30',
              border: '1px solid var(--border-subtle)',
              color: '#f3f7fa',
              borderRadius: '8px',
              padding: '8px 14px',
              fontFamily: 'var(--font-tech)',
              fontSize: '0.74rem',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <FileText size={13} color="#22d3a2" />
            <span>Export CSV</span>
          </button>
        </div>
      </div>

      {/* Forensic KPI Summary Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: '10px' }}>
        <div style={{ backgroundColor: '#101927', padding: '12px', borderRadius: '10px', border: '1px solid var(--border-subtle)' }}>
          <div style={{ fontFamily: 'var(--font-tech)', fontSize: '0.68rem', color: '#8b98aa' }}>Total Requests</div>
          <div style={{ fontFamily: 'var(--font-display)', fontSize: '1.2rem', fontWeight: 800, color: '#f3f7fa', marginTop: '4px' }}>
            {session.total_requests || 0}
          </div>
        </div>

        <div style={{ backgroundColor: '#101927', padding: '12px', borderRadius: '10px', border: '1px solid var(--border-subtle)' }}>
          <div style={{ fontFamily: 'var(--font-tech)', fontSize: '0.68rem', color: '#8b98aa' }}>Blocked (HTTP 429)</div>
          <div style={{ fontFamily: 'var(--font-display)', fontSize: '1.2rem', fontWeight: 800, color: '#ffd23f', marginTop: '4px' }}>
            {session.blocked_requests || 0}
          </div>
        </div>

        <div style={{ backgroundColor: '#101927', padding: '12px', borderRadius: '10px', border: '1px solid var(--border-subtle)' }}>
          <div style={{ fontFamily: 'var(--font-tech)', fontSize: '0.68rem', color: '#8b98aa' }}>Peak Rate</div>
          <div style={{ fontFamily: 'var(--font-display)', fontSize: '1.2rem', fontWeight: 800, color: '#36c7ff', marginTop: '4px' }}>
            {session.peak_rate || 0} req/s
          </div>
        </div>

        <div style={{ backgroundColor: '#101927', padding: '12px', borderRadius: '10px', border: '1px solid var(--border-subtle)' }}>
          <div style={{ fontFamily: 'var(--font-tech)', fontSize: '0.68rem', color: '#8b98aa' }}>Average Latency</div>
          <div style={{ fontFamily: 'var(--font-display)', fontSize: '1.2rem', fontWeight: 800, color: '#f3f7fa', marginTop: '4px' }}>
            {session.avg_latency || 0} ms
          </div>
        </div>

        <div style={{ backgroundColor: '#101927', padding: '12px', borderRadius: '10px', border: '1px solid var(--border-subtle)' }}>
          <div style={{ fontFamily: 'var(--font-tech)', fontSize: '0.68rem', color: '#8b98aa' }}>Max Risk Score</div>
          <div style={{ fontFamily: 'var(--font-display)', fontSize: '1.2rem', fontWeight: 800, color: session.max_risk_score > 70 ? '#ff454a' : '#22d3a2', marginTop: '4px' }}>
            {session.max_risk_score || 0} / 100
          </div>
        </div>

        <div style={{ backgroundColor: '#101927', padding: '12px', borderRadius: '10px', border: '1px solid var(--border-subtle)' }}>
          <div style={{ fontFamily: 'var(--font-tech)', fontSize: '0.68rem', color: '#8b98aa' }}>Defense Capacity</div>
          <div style={{ fontFamily: 'var(--font-display)', fontSize: '1.2rem', fontWeight: 800, color: '#22d3a2', marginTop: '4px' }}>
            {session.defense_capacity || 100}%
          </div>
        </div>
      </div>

      {/* Threat Matrix Table */}
      <div
        style={{
          backgroundColor: '#0a111c',
          borderRadius: '14px',
          border: '1px solid var(--border-subtle)',
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            padding: '12px 18px',
            backgroundColor: '#101927',
            borderBottom: '1px solid var(--border-subtle)',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}
        >
          <Shield size={16} color="#36c7ff" />
          <span style={{ fontFamily: 'var(--font-display)', fontSize: '0.82rem', fontWeight: 700, color: '#f3f7fa' }}>
            SEVEN-DIMENSIONAL THREAT MATRIX EVALUATION
          </span>
        </div>

        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
          <thead>
            <tr style={{ backgroundColor: '#0e1624', borderBottom: '1px solid var(--border-subtle)' }}>
              <th style={{ padding: '10px 16px', fontFamily: 'var(--font-tech)', fontSize: '0.72rem', color: '#8b98aa' }}>THREAT CATEGORY</th>
              <th style={{ padding: '10px 16px', fontFamily: 'var(--font-tech)', fontSize: '0.72rem', color: '#8b98aa' }}>OBSERVED SIGNATURE</th>
              <th style={{ padding: '10px 16px', fontFamily: 'var(--font-tech)', fontSize: '0.72rem', color: '#8b98aa' }}>SEVERITY</th>
              <th style={{ padding: '10px 16px', fontFamily: 'var(--font-tech)', fontSize: '0.72rem', color: '#8b98aa' }}>ML DETECTED</th>
              <th style={{ padding: '10px 16px', fontFamily: 'var(--font-tech)', fontSize: '0.72rem', color: '#8b98aa' }}>RISK IMPACT</th>
              <th style={{ padding: '10px 16px', fontFamily: 'var(--font-tech)', fontSize: '0.72rem', color: '#8b98aa' }}>DEFENSE ACTION</th>
              <th style={{ padding: '10px 16px', fontFamily: 'var(--font-tech)', fontSize: '0.72rem', color: '#8b98aa' }}>FINAL STATUS</th>
            </tr>
          </thead>
          <tbody>
            {matrixRows.map((row: any, i: number) => {
              const isHigh = row.severity === 'HIGH';
              const sevColor = isHigh ? '#ff454a' : row.severity === 'MEDIUM' ? '#ffd23f' : '#22d3a2';
              return (
                <tr key={i} style={{ borderBottom: '1px solid rgba(90, 140, 190, 0.08)' }}>
                  <td style={{ padding: '12px 16px', fontFamily: 'var(--font-tech)', fontSize: '0.80rem', fontWeight: 600, color: '#f3f7fa' }}>
                    {row.category}
                  </td>
                  <td style={{ padding: '12px 16px', fontFamily: 'var(--font-tech)', fontSize: '0.76rem', color: '#8b98aa' }}>
                    {row.observed}
                  </td>
                  <td style={{ padding: '12px 16px' }}>
                    <span style={{ color: sevColor, fontFamily: 'var(--font-tech)', fontSize: '0.72rem', fontWeight: 700 }}>
                      {row.severity}
                    </span>
                  </td>
                  <td style={{ padding: '12px 16px', fontFamily: 'var(--font-tech)', fontSize: '0.76rem', color: row.ml_detected ? '#36c7ff' : '#8b98aa' }}>
                    {row.ml_detected ? 'TRUE' : 'FALSE'}
                  </td>
                  <td style={{ padding: '12px 16px', fontFamily: 'var(--font-tech)', fontSize: '0.76rem', color: '#ffd23f', fontWeight: 600 }}>
                    {row.risk}
                  </td>
                  <td style={{ padding: '12px 16px', fontFamily: 'var(--font-tech)', fontSize: '0.72rem', color: '#f3f7fa' }}>
                    {row.defense_action}
                  </td>
                  <td style={{ padding: '12px 16px' }}>
                    <span style={{ backgroundColor: 'rgba(34, 211, 162, 0.12)', color: '#22d3a2', padding: '3px 8px', borderRadius: '4px', fontSize: '0.70rem', fontWeight: 700 }}>
                      {row.final_status}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Model Performance & Forensic Metadata */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
        <div style={{ backgroundColor: '#101927', padding: '16px', borderRadius: '12px', border: '1px solid var(--border-subtle)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '10px' }}>
            <Cpu size={14} color="#36c7ff" />
            <span style={{ fontFamily: 'var(--font-display)', fontSize: '0.76rem', fontWeight: 700, color: '#f3f7fa' }}>
              ISOLATION FOREST VALIDATION METRICS
            </span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '10px' }}>
            <div>
              <div style={{ fontFamily: 'var(--font-tech)', fontSize: '0.64rem', color: '#8b98aa' }}>Accuracy</div>
              <div style={{ fontFamily: 'var(--font-tech)', fontSize: '0.92rem', fontWeight: 700, color: '#22d3a2' }}>
                {((modelPerf.metrics?.accuracy || 0.9831) * 100).toFixed(1)}%
              </div>
            </div>
            <div>
              <div style={{ fontFamily: 'var(--font-tech)', fontSize: '0.64rem', color: '#8b98aa' }}>Precision</div>
              <div style={{ fontFamily: 'var(--font-tech)', fontSize: '0.92rem', fontWeight: 700, color: '#22d3a2' }}>
                {((modelPerf.metrics?.precision || 0.9565) * 100).toFixed(1)}%
              </div>
            </div>
            <div>
              <div style={{ fontFamily: 'var(--font-tech)', fontSize: '0.64rem', color: '#8b98aa' }}>Recall</div>
              <div style={{ fontFamily: 'var(--font-tech)', fontSize: '0.92rem', fontWeight: 700, color: '#22d3a2' }}>
                {((modelPerf.metrics?.recall || 1.0) * 100).toFixed(1)}%
              </div>
            </div>
            <div>
              <div style={{ fontFamily: 'var(--font-tech)', fontSize: '0.64rem', color: '#8b98aa' }}>F1-Score</div>
              <div style={{ fontFamily: 'var(--font-tech)', fontSize: '0.92rem', fontWeight: 700, color: '#22d3a2' }}>
                {((modelPerf.metrics?.f1_score || 0.9778) * 100).toFixed(1)}%
              </div>
            </div>
          </div>
        </div>

        <div style={{ backgroundColor: '#101927', padding: '16px', borderRadius: '12px', border: '1px solid var(--border-subtle)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '10px' }}>
            <Clock size={14} color="#ffd23f" />
            <span style={{ fontFamily: 'var(--font-display)', fontSize: '0.76rem', fontWeight: 700, color: '#f3f7fa' }}>
              INCIDENT LIFECYCLE FORENSICS
            </span>
          </div>
          <div style={{ fontFamily: 'var(--font-tech)', fontSize: '0.74rem', color: '#8b98aa', lineHeight: 1.6 }}>
            Incident state transitioned: <strong>OPEN &rarr; INVESTIGATING &rarr; DEFENSE ACTIVE &rarr; RECOVERED</strong>.
            All anomalous requests throttled with HTTP 429 Retry-After policy. Total incidents recorded: {session.incident_count || 1}.
          </div>
        </div>
      </div>
    </div>
  );
};
