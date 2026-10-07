import React, { useState } from 'react';
import { Radio, ArrowLeft, Terminal, Play } from 'lucide-react';

interface WiresharkLabViewProps {
  onBack: () => void;
}

export const WiresharkLabView: React.FC<WiresharkLabViewProps> = ({ onBack }) => {
  const [probeResult, setProbeResult] = useState<any>(null);
  const [probing, setProbing] = useState(false);

  const testSinglePacket = async () => {
    setProbing(true);
    try {
      const res = await fetch('http://127.0.0.1:5000/lab/target', {
        headers: {
          'X-AegisGuard-Client': 'wireshark-test-probe',
          'User-Agent': 'AegisGuard-Wireshark-Probe/1.0',
        },
      });
      const data = await res.json();
      setProbeResult({
        status: res.status,
        statusText: res.statusText,
        headers: {
          'content-type': res.headers.get('content-type'),
          'x-defense-level': res.headers.get('x-defense-level'),
          'x-risk-score': res.headers.get('x-risk-score'),
          'retry-after': res.headers.get('retry-after'),
        },
        body: data,
      });
    } catch (err: any) {
      setProbeResult({ error: err.message });
    } finally {
      setProbing(false);
    }
  };

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
      {/* Header */}
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
            <h1
              style={{
                fontFamily: 'var(--font-display)',
                fontSize: '1.25rem',
                fontWeight: 800,
                color: '#f3f7fa',
                letterSpacing: '0.04em',
              }}
            >
              WIRESHARK OBSERVABILITY & PACKET ANALYSIS
            </h1>
            <p style={{ fontFamily: 'var(--font-tech)', fontSize: '0.72rem', color: '#8b98aa', marginTop: '3px' }}>
              Real packet capture verification on loopback adapter (Port 5000).
            </p>
          </div>
        </div>

        <button
          onClick={testSinglePacket}
          disabled={probing}
          style={{
            background: 'linear-gradient(135deg, #168bff 0%, #0b3d73 100%)',
            border: '1px solid rgba(54, 199, 255, 0.4)',
            color: '#f3f7fa',
            borderRadius: '8px',
            padding: '8px 18px',
            fontFamily: 'var(--font-tech)',
            fontSize: '0.74rem',
            fontWeight: 700,
            cursor: probing ? 'not-allowed' : 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}
        >
          <Play size={13} />
          <span>{probing ? 'TRANSMITTING PROBE...' : 'SEND TEST PROBE PACKET'}</span>
        </button>
      </div>

      {/* 3 Step Tutorial */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '14px' }}>
        <div style={{ backgroundColor: '#101927', padding: '18px', borderRadius: '12px', border: '1px solid var(--border-subtle)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
            <div style={{ width: '22px', height: '22px', borderRadius: '50%', backgroundColor: 'rgba(54, 199, 255, 0.2)', color: '#36c7ff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: 'var(--font-display)', fontSize: '0.75rem', fontWeight: 800 }}>1</div>
            <span style={{ fontFamily: 'var(--font-display)', fontSize: '0.78rem', fontWeight: 700, color: '#f3f7fa' }}>SELECT INTERFACE</span>
          </div>
          <div style={{ fontFamily: 'var(--font-tech)', fontSize: '0.74rem', color: '#8b98aa', lineHeight: 1.5 }}>
            Open Wireshark and choose:
            <div style={{ marginTop: '6px', padding: '8px', backgroundColor: '#0a111c', borderRadius: '6px', color: '#36c7ff', fontWeight: 600 }}>
              Npcap Loopback Adapter
            </div>
            (or "Adapter for loopback traffic capture" on Windows).
          </div>
        </div>

        <div style={{ backgroundColor: '#101927', padding: '18px', borderRadius: '12px', border: '1px solid var(--border-subtle)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
            <div style={{ width: '22px', height: '22px', borderRadius: '50%', backgroundColor: 'rgba(54, 199, 255, 0.2)', color: '#36c7ff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: 'var(--font-display)', fontSize: '0.75rem', fontWeight: 800 }}>2</div>
            <span style={{ fontFamily: 'var(--font-display)', fontSize: '0.78rem', fontWeight: 700, color: '#f3f7fa' }}>APPLY DISPLAY FILTER</span>
          </div>
          <div style={{ fontFamily: 'var(--font-tech)', fontSize: '0.74rem', color: '#8b98aa', lineHeight: 1.5 }}>
            Paste this filter in the green Wireshark bar:
            <div style={{ marginTop: '6px', padding: '8px', backgroundColor: '#0a111c', borderRadius: '6px', color: '#ffd23f', fontFamily: 'Consolas, monospace', fontSize: '0.72rem' }}>
              tcp.port == 5000 and http
            </div>
            This isolates all laboratory traffic hitting the Python target.
          </div>
        </div>

        <div style={{ backgroundColor: '#101927', padding: '18px', borderRadius: '12px', border: '1px solid var(--border-subtle)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
            <div style={{ width: '22px', height: '22px', borderRadius: '50%', backgroundColor: 'rgba(54, 199, 255, 0.2)', color: '#36c7ff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: 'var(--font-display)', fontSize: '0.75rem', fontWeight: 800 }}>3</div>
            <span style={{ fontFamily: 'var(--font-display)', fontSize: '0.78rem', fontWeight: 700, color: '#f3f7fa' }}>INSPECT SIGNATURES</span>
          </div>
          <div style={{ fontFamily: 'var(--font-tech)', fontSize: '0.74rem', color: '#8b98aa', lineHeight: 1.5 }}>
            Look for custom protocol headers:
            <div style={{ marginTop: '6px', color: '#22d3a2', fontFamily: 'Consolas, monospace', fontSize: '0.70rem' }}>
              &bull; X-Defense-Level: NORMAL / WATCH / HIGH_RISK<br />
              &bull; X-Risk-Score: 0.0 - 100.0<br />
              &bull; HTTP/1.1 429 Too Many Requests
            </div>
          </div>
        </div>
      </div>

      {/* Live Probe Packet Inspector */}
      {probeResult && (
        <div style={{ backgroundColor: '#0a111c', borderRadius: '14px', border: '1px solid var(--border-subtle)', padding: '18px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
            <Terminal size={16} color="#36c7ff" />
            <span style={{ fontFamily: 'var(--font-display)', fontSize: '0.80rem', fontWeight: 700, color: '#f3f7fa' }}>
              TEST PROBE WIRESHARK TRANSMISSION RESULT
            </span>
          </div>
          <pre
            style={{
              backgroundColor: '#07101d',
              padding: '14px',
              borderRadius: '8px',
              fontFamily: 'Consolas, monospace',
              fontSize: '0.74rem',
              color: '#36c7ff',
              overflowX: 'auto',
              border: '1px solid rgba(54, 199, 255, 0.2)',
            }}
          >
            {JSON.stringify(probeResult, null, 2)}
          </pre>
        </div>
      )}

      {/* Protocol Frame Anatomy */}
      <div style={{ backgroundColor: '#101927', padding: '18px', borderRadius: '12px', border: '1px solid var(--border-subtle)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
          <Radio size={16} color="#ffd23f" />
          <span style={{ fontFamily: 'var(--font-display)', fontSize: '0.80rem', fontWeight: 700, color: '#f3f7fa' }}>
            CAPTAINSHIELD LABORATORY HTTP PACKET SIGNATURE
          </span>
        </div>
        <div style={{ fontFamily: 'var(--font-tech)', fontSize: '0.74rem', color: '#8b98aa', lineHeight: 1.6 }}>
          All traffic sent by CaptainShield generator includes forensic fingerprint headers:
          <pre style={{ backgroundColor: '#0a111c', padding: '12px', borderRadius: '8px', color: '#f3f7fa', marginTop: '8px', fontFamily: 'Consolas, monospace', fontSize: '0.72rem' }}>
{`GET /lab/target HTTP/1.1
Host: 127.0.0.1:5000
User-Agent: CaptainShield-TrafficGen/1.0
X-CaptainShield-Client: client-14
X-Simulation-Session: session-7c64a39f
Accept: */*`}
          </pre>
          When the adaptive rate limiter throttles a client, the target returns:
          <pre style={{ backgroundColor: '#0a111c', padding: '12px', borderRadius: '8px', color: '#ffd23f', marginTop: '8px', fontFamily: 'Consolas, monospace', fontSize: '0.72rem' }}>
{`HTTP/1.1 429 TOO MANY REQUESTS
Content-Type: application/json
Retry-After: 20
X-Defense-Level: HIGH_RISK
X-Risk-Score: 84.6
{"status": "blocked", "message": "Rate limit exceeded (adaptive defense)", "defense_level": "HIGH_RISK"}`}
          </pre>
        </div>
      </div>
    </div>
  );
};
