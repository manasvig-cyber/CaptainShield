import React, { useEffect, useState } from 'react';
import { Eye, Download, Trash2 } from 'lucide-react';
import { api } from '../services/api';

interface RecentViewProps {
  onViewReport: (sessionId: string) => void;
}

export const RecentView: React.FC<RecentViewProps> = ({ onViewReport }) => {
  const [sessions, setSessions] = useState<any[]>([]);
  const [analytics, setAnalytics] = useState<any>({});
  const [loading, setLoading] = useState(true);

  const fetchRecent = () => {
    setLoading(true);
    api.getRecentHistory()
      .then((res) => {
        setSessions(res.sessions || []);
        setAnalytics(res.analytics || {});
        setLoading(false);
      })
      .catch(() => setLoading(false));
  };

  useEffect(() => {
    fetchRecent();
  }, []);

  const handleDelete = async (id: string) => {
    if (window.confirm(`Delete simulation record ${id}?`)) {
      await api.deleteRecent(id);
      fetchRecent();
    }
  };

  const handleExport = (session: any) => {
    const blob = new Blob([JSON.stringify(session, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Session_${session.id}.json`;
    a.click();
  };

  if (loading) {
    return (
      <div style={{ padding: '30px', color: '#f3f7fa', fontFamily: 'var(--font-tech)' }}>
        Loading simulation audit logs from SQLite...
      </div>
    );
  }

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
      {/* Title */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h1
            style={{
              fontFamily: 'var(--font-display)',
              fontSize: '1.25rem',
              fontWeight: 800,
              color: '#f3f7fa',
              letterSpacing: '0.04em',
            }}
          >
            SIMULATION HISTORY & AUDIT TRAIL
          </h1>
          <p style={{ fontFamily: 'var(--font-tech)', fontSize: '0.72rem', color: '#8b98aa', marginTop: '3px' }}>
            Persisted laboratory sessions recorded in SQLite with forensic telemetry metrics.
          </p>
        </div>

        <button
          onClick={fetchRecent}
          style={{
            background: '#141f30',
            border: '1px solid var(--border-subtle)',
            color: '#36c7ff',
            borderRadius: '8px',
            padding: '7px 12px',
            fontFamily: 'var(--font-tech)',
            fontSize: '0.74rem',
            cursor: 'pointer',
          }}
        >
          Refresh Data
        </button>
      </div>

      {/* Analytics Summary */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px' }}>
        <div style={{ backgroundColor: '#101927', padding: '14px', borderRadius: '12px', border: '1px solid var(--border-subtle)' }}>
          <div style={{ fontFamily: 'var(--font-tech)', fontSize: '0.68rem', color: '#8b98aa' }}>Total Simulations</div>
          <div style={{ fontFamily: 'var(--font-display)', fontSize: '1.3rem', fontWeight: 800, color: '#f3f7fa', marginTop: '4px' }}>
            {analytics.total_simulations || 0}
          </div>
        </div>

        <div style={{ backgroundColor: '#101927', padding: '14px', borderRadius: '12px', border: '1px solid var(--border-subtle)' }}>
          <div style={{ fontFamily: 'var(--font-tech)', fontSize: '0.68rem', color: '#8b98aa' }}>Total Traffic Packets</div>
          <div style={{ fontFamily: 'var(--font-display)', fontSize: '1.3rem', fontWeight: 800, color: '#36c7ff', marginTop: '4px' }}>
            {analytics.total_requests || 0}
          </div>
        </div>

        <div style={{ backgroundColor: '#101927', padding: '14px', borderRadius: '12px', border: '1px solid var(--border-subtle)' }}>
          <div style={{ fontFamily: 'var(--font-tech)', fontSize: '0.68rem', color: '#8b98aa' }}>Threats Throttled (429)</div>
          <div style={{ fontFamily: 'var(--font-display)', fontSize: '1.3rem', fontWeight: 800, color: '#ffd23f', marginTop: '4px' }}>
            {analytics.total_blocked || 0}
          </div>
        </div>

        <div style={{ backgroundColor: '#101927', padding: '14px', borderRadius: '12px', border: '1px solid var(--border-subtle)' }}>
          <div style={{ fontFamily: 'var(--font-tech)', fontSize: '0.68rem', color: '#8b98aa' }}>Avg Defense Capacity</div>
          <div style={{ fontFamily: 'var(--font-display)', fontSize: '1.3rem', fontWeight: 800, color: '#22d3a2', marginTop: '4px' }}>
            {analytics.average_defense_capacity || 100}%
          </div>
        </div>
      </div>

      {/* History Table */}
      <div
        style={{
          backgroundColor: '#0a111c',
          borderRadius: '14px',
          border: '1px solid var(--border-subtle)',
          overflow: 'hidden',
        }}
      >
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
          <thead>
            <tr style={{ backgroundColor: '#0e1624', borderBottom: '1px solid var(--border-subtle)' }}>
              <th style={{ padding: '10px 16px', fontFamily: 'var(--font-tech)', fontSize: '0.72rem', color: '#8b98aa' }}>SESSION ID</th>
              <th style={{ padding: '10px 16px', fontFamily: 'var(--font-tech)', fontSize: '0.72rem', color: '#8b98aa' }}>PRESET</th>
              <th style={{ padding: '10px 16px', fontFamily: 'var(--font-tech)', fontSize: '0.72rem', color: '#8b98aa' }}>DURATION</th>
              <th style={{ padding: '10px 16px', fontFamily: 'var(--font-tech)', fontSize: '0.72rem', color: '#8b98aa' }}>TOTAL REQS</th>
              <th style={{ padding: '10px 16px', fontFamily: 'var(--font-tech)', fontSize: '0.72rem', color: '#8b98aa' }}>BLOCKED (429)</th>
              <th style={{ padding: '10px 16px', fontFamily: 'var(--font-tech)', fontSize: '0.72rem', color: '#8b98aa' }}>AVG RISK</th>
              <th style={{ padding: '10px 16px', fontFamily: 'var(--font-tech)', fontSize: '0.72rem', color: '#8b98aa' }}>DEFENSE CAPACITY</th>
              <th style={{ padding: '10px 16px', fontFamily: 'var(--font-tech)', fontSize: '0.72rem', color: '#8b98aa' }}>STATUS</th>
              <th style={{ padding: '10px 16px', fontFamily: 'var(--font-tech)', fontSize: '0.72rem', color: '#8b98aa', textAlign: 'right' }}>ACTIONS</th>
            </tr>
          </thead>
          <tbody>
            {sessions.length === 0 ? (
              <tr>
                <td colSpan={9} style={{ padding: '30px', textAlign: 'center', color: '#566477', fontFamily: 'var(--font-tech)' }}>
                  No historical simulation runs recorded yet. Start an attack simulation to populate forensics.
                </td>
              </tr>
            ) : (
              sessions.map((s) => (
                <tr key={s.id} style={{ borderBottom: '1px solid rgba(90, 140, 190, 0.08)' }}>
                  <td style={{ padding: '12px 16px', fontFamily: 'var(--font-display)', fontSize: '0.78rem', fontWeight: 700, color: '#36c7ff' }}>
                    {s.id}
                  </td>
                  <td style={{ padding: '12px 16px', fontFamily: 'var(--font-tech)', fontSize: '0.76rem', color: '#f3f7fa' }}>
                    {s.preset}
                  </td>
                  <td style={{ padding: '12px 16px', fontFamily: 'var(--font-tech)', fontSize: '0.74rem', color: '#8b98aa' }}>
                    {s.duration}s
                  </td>
                  <td style={{ padding: '12px 16px', fontFamily: 'var(--font-tech)', fontSize: '0.76rem', color: '#f3f7fa', fontWeight: 600 }}>
                    {s.total_requests}
                  </td>
                  <td style={{ padding: '12px 16px', fontFamily: 'var(--font-tech)', fontSize: '0.76rem', color: s.blocked_requests > 0 ? '#ffd23f' : '#8b98aa' }}>
                    {s.blocked_requests}
                  </td>
                  <td style={{ padding: '12px 16px', fontFamily: 'var(--font-tech)', fontSize: '0.76rem', color: s.avg_risk_score > 60 ? '#ff454a' : '#22d3a2', fontWeight: 700 }}>
                    {s.avg_risk_score} / 100
                  </td>
                  <td style={{ padding: '12px 16px', fontFamily: 'var(--font-tech)', fontSize: '0.76rem', color: '#22d3a2', fontWeight: 700 }}>
                    {s.defense_capacity}%
                  </td>
                  <td style={{ padding: '12px 16px' }}>
                    <span style={{ backgroundColor: 'rgba(34, 211, 162, 0.12)', color: '#22d3a2', padding: '3px 8px', borderRadius: '4px', fontSize: '0.68rem', fontWeight: 700 }}>
                      {s.status}
                    </span>
                  </td>
                  <td style={{ padding: '12px 16px', textAlign: 'right' }}>
                    <div style={{ display: 'inline-flex', gap: '8px' }}>
                      <button
                        onClick={() => onViewReport(s.id)}
                        style={{
                          background: 'rgba(54, 199, 255, 0.12)',
                          border: '1px solid rgba(54, 199, 255, 0.3)',
                          color: '#36c7ff',
                          borderRadius: '6px',
                          padding: '4px 8px',
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '4px',
                          fontSize: '0.70rem',
                          fontFamily: 'var(--font-tech)',
                        }}
                      >
                        <Eye size={12} />
                        <span>Report</span>
                      </button>

                      <button
                        onClick={() => handleExport(s)}
                        style={{
                          background: 'transparent',
                          border: '1px solid var(--border-subtle)',
                          color: '#8b98aa',
                          borderRadius: '6px',
                          padding: '4px 6px',
                          cursor: 'pointer',
                        }}
                        title="Download JSON"
                      >
                        <Download size={12} />
                      </button>

                      <button
                        onClick={() => handleDelete(s.id)}
                        style={{
                          background: 'transparent',
                          border: '1px solid rgba(255, 69, 74, 0.25)',
                          color: '#ff454a',
                          borderRadius: '6px',
                          padding: '4px 6px',
                          cursor: 'pointer',
                        }}
                        title="Delete Session"
                      >
                        <Trash2 size={12} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
