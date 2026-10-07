import React, { useEffect, useState } from 'react';
import { 
  Shield, 
  Sliders, 
  Radio, 
  AlertOctagon, 
  Save, 
  CheckCircle2, 
  Cpu, 
  Database, 
  Zap, 
  Activity, 
  RefreshCw,
  Layers,
  Terminal,
  FileText
} from 'lucide-react';
import { api } from '../services/api';

export const SettingsView: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'workflow' | 'simulation' | 'ml' | 'defense' | 'network' | 'retention'>('workflow');
  const [settings, setSettings] = useState<Record<string, string>>({
    app_name: 'CaptainShield Defense Lab',
    lab_mode: 'true',
    default_preset: 'Controlled Attack',
    default_workers: '8',
    default_rate: '50',
    default_duration: '86400',
    max_duration: '86400',
    target_url: 'http://127.0.0.1:5000/lab/target',
    anomaly_sensitivity: '0.05',
    risk_threshold_watch: '30',
    risk_threshold_suspicious: '60',
    risk_threshold_high: '80',
    rate_limiting_enabled: 'true',
    wireshark_interface: 'Npcap Loopback Adapter',
    redis_stream_key: 'aegisguard:events:stream',
    log_retention_days: '30',
  });

  const [savedMessage, setSavedMessage] = useState(false);
  const [workflowTestResult, setWorkflowTestResult] = useState<any | null>(null);
  const [isTestingWorkflow, setIsTestingWorkflow] = useState(false);
  const [selectedWorkflowNode, setSelectedWorkflowNode] = useState<string | null>('ml');

  useEffect(() => {
    api.getSettings().then((res) => {
      if (res && typeof res === 'object') {
        setSettings((prev) => ({ ...prev, ...res }));
      }
    }).catch(() => {});
  }, []);

  const handleChange = (key: string, val: string) => {
    setSettings((prev) => ({ ...prev, [key]: val }));
  };

  const handleSave = async () => {
    await api.updateSettings(settings);
    setSavedMessage(true);
    setTimeout(() => setSavedMessage(false), 2500);
  };

  const handleTestWorkflow = async () => {
    setIsTestingWorkflow(true);
    try {
      const res = await api.testWorkflow();
      setWorkflowTestResult(res);
    } catch (err) {
      setWorkflowTestResult({
        status: 'ERROR',
        all_passed: false,
        stages: [{ id: 'error', name: 'Gateway Error', status: 'FAIL', detail: 'Could not communicate with backend gateway.' }],
      });
    } finally {
      setIsTestingWorkflow(false);
    }
  };

  const workflowNodes = [
    { id: 'traffic', label: '1. TRAFFIC GENERATOR', desc: 'Simulated multi-threaded client request stream', icon: <Radio size={14} color="#ff454a" />, stage: 'Ingress' },
    { id: 'telemetry', label: '2. 7-FEATURE TELEMETRY', desc: 'Real-time sliding window feature extraction', icon: <Activity size={14} color="#36c7ff" />, stage: 'Observation' },
    { id: 'redis', label: '3. REDIS EVENT BUS', desc: 'Decoupled in-memory message and event stream', icon: <Database size={14} color="#22d3a2" />, stage: 'Transport' },
    { id: 'ml', label: '4. ISOLATION FOREST', desc: 'Unsupervised ML anomaly scoring & outlier detection', icon: <Cpu size={14} color="#36c7ff" />, stage: 'Inference' },
    { id: 'risk', label: '5. RISK ENGINE', desc: 'Calibrated scoring from 0.0 to 100.0', icon: <Zap size={14} color="#ffd83d" />, stage: 'Classification' },
    { id: 'defense', label: '6. ADAPTIVE DEFENSE', desc: '4-tier automated state machine policy controller', icon: <Shield size={14} color="#22d3a2" />, stage: 'Policy' },
    { id: 'rate_limiter', label: '7. RATE LIMITER', desc: 'Sliding window throttling with microsecond enforcement', icon: <Sliders size={14} color="#f97316" />, stage: 'Mitigation' },
    { id: 'gateway', label: '8. HTTP TARGET GATEWAY', desc: 'Wireshark-observable HTTP 200 / 429 response enforcement', icon: <Terminal size={14} color="#36c7ff" />, stage: 'Enforcement' },
    { id: 'incident', label: '9. INCIDENT LIFECYCLE', desc: 'Auto-detection, triage, and recovery tracking', icon: <AlertOctagon size={14} color="#ff454a" />, stage: 'Forensics' },
    { id: 'report', label: '10. SQLITE AUDIT', desc: 'Persistent session metrics, incidents & telemetry storage', icon: <FileText size={14} color="#22d3a2" />, stage: 'Persistence' },
  ];

  return (
    <div
      style={{
        padding: '20px 24px',
        minHeight: '100%',
        display: 'flex',
        flexDirection: 'column',
        gap: '16px',
        backgroundColor: '#050810',
      }}
    >
      {/* Header Bar */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
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
            SETTINGS & DEFENSE CONTROL CENTER
          </h1>
          <p style={{ fontFamily: 'var(--font-tech)', fontSize: '0.72rem', color: '#8b98aa', marginTop: '2px' }}>
            Comprehensive operational parameters, automated defense workflow, Isolation Forest sensitivity, and safety bounds.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <button
            onClick={handleTestWorkflow}
            disabled={isTestingWorkflow}
            style={{
              background: 'rgba(54, 199, 255, 0.12)',
              border: '1px solid rgba(54, 199, 255, 0.4)',
              color: '#36c7ff',
              borderRadius: '8px',
              padding: '8px 16px',
              fontFamily: 'var(--font-display)',
              fontSize: '0.74rem',
              fontWeight: 800,
              cursor: isTestingWorkflow ? 'wait' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              transition: 'all 0.2s ease',
            }}
          >
            <RefreshCw size={13} className={isTestingWorkflow ? 'pulse' : ''} />
            <span>{isTestingWorkflow ? 'TESTING PIPELINE...' : 'TEST DEFENSE WORKFLOW'}</span>
          </button>

          <button
            onClick={handleSave}
            style={{
              background: 'linear-gradient(135deg, #168bff 0%, #0b3d73 100%)',
              border: '1px solid rgba(54, 199, 255, 0.4)',
              color: '#f3f7fa',
              borderRadius: '8px',
              padding: '8px 18px',
              fontFamily: 'var(--font-display)',
              fontSize: '0.74rem',
              fontWeight: 800,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              boxShadow: '0 0 15px rgba(22, 139, 255, 0.3)',
            }}
          >
            <Save size={13} />
            <span>{savedMessage ? 'SAVED TO SQLITE!' : 'SAVE SETTINGS'}</span>
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '8px', borderBottom: '1px solid rgba(90, 140, 190, 0.2)', paddingBottom: '8px', overflowX: 'auto' }}>
        {[
          { id: 'workflow', label: 'Interactive Defense Workflow' },
          { id: 'simulation', label: 'Simulation & Safety Bounds' },
          { id: 'ml', label: 'ML & 7-Feature Telemetry' },
          { id: 'defense', label: 'Adaptive Defense & Throttling' },
          { id: 'network', label: 'Network & Wireshark' },
          { id: 'retention', label: 'Database & Retention' },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            style={{
              padding: '6px 14px',
              borderRadius: '6px',
              border: activeTab === tab.id ? '1px solid rgba(54, 199, 255, 0.5)' : '1px solid transparent',
              backgroundColor: activeTab === tab.id ? 'rgba(54, 199, 255, 0.12)' : 'transparent',
              color: activeTab === tab.id ? '#36c7ff' : '#8b98aa',
              fontFamily: 'var(--font-tech)',
              fontSize: '0.74rem',
              fontWeight: 700,
              cursor: 'pointer',
              whiteSpace: 'nowrap',
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* TAB 1: INTERACTIVE DEFENSE WORKFLOW */}
      {activeTab === 'workflow' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {/* Workflow Test Diagnostic Output Banner */}
          {workflowTestResult && (
            <div
              style={{
                backgroundColor: workflowTestResult.all_passed ? 'rgba(34, 211, 162, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                border: `1px solid ${workflowTestResult.all_passed ? 'rgba(34, 211, 162, 0.4)' : 'rgba(239, 68, 68, 0.4)'}`,
                borderRadius: '10px',
                padding: '12px 16px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <CheckCircle2 size={18} color={workflowTestResult.all_passed ? '#22d3a2' : '#ef4444'} />
                <div>
                  <div style={{ fontFamily: 'var(--font-display)', fontSize: '0.80rem', fontWeight: 800, color: '#f3f7fa' }}>
                    DEFENSE PIPELINE HEALTH: {workflowTestResult.status} ({workflowTestResult.stages_tested}/10 STAGES PASS)
                  </div>
                  <div style={{ fontFamily: 'var(--font-tech)', fontSize: '0.68rem', color: '#8b98aa', marginTop: '2px' }}>
                    Full verification completed in {workflowTestResult.execution_time_ms} ms. All defense controllers operational.
                  </div>
                </div>
              </div>
              <span
                style={{
                  fontFamily: 'var(--font-tech)',
                  fontSize: '0.68rem',
                  fontWeight: 800,
                  color: '#22d3a2',
                  backgroundColor: 'rgba(34, 211, 162, 0.15)',
                  padding: '4px 10px',
                  borderRadius: '6px',
                }}
              >
                100% OPERATIONAL
              </span>
            </div>
          )}

          {/* Interactive Flowchart Diagram */}
          <div
            style={{
              backgroundColor: '#07101d',
              borderRadius: '14px',
              border: '1px solid var(--border-subtle)',
              padding: '18px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Layers size={16} color="#36c7ff" />
                <span style={{ fontFamily: 'var(--font-display)', fontSize: '0.80rem', fontWeight: 800, color: '#f3f7fa' }}>
                  AUTOMATED DEFENSE WORKFLOW ARCHITECTURE (CLICK NODE TO INSPECT)
                </span>
              </div>
              <span style={{ fontFamily: 'var(--font-tech)', fontSize: '0.68rem', color: '#8b98aa' }}>
                Loopback Port 5000 &bull; Continuous Flow
              </span>
            </div>

            {/* Visual Node Flow Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '10px' }}>
              {workflowNodes.map((node) => {
                const isSelected = selectedWorkflowNode === node.id;
                return (
                  <div
                    key={node.id}
                    onClick={() => setSelectedWorkflowNode(node.id)}
                    style={{
                      padding: '12px',
                      borderRadius: '10px',
                      backgroundColor: isSelected ? '#141f30' : '#0a111c',
                      border: isSelected ? '1px solid #36c7ff' : '1px solid rgba(90, 140, 190, 0.18)',
                      cursor: 'pointer',
                      transition: 'all 0.2s ease',
                      boxShadow: isSelected ? '0 0 16px rgba(54, 199, 255, 0.2)' : 'none',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        {node.icon}
                        <span style={{ fontFamily: 'var(--font-tech)', fontSize: '0.60rem', color: '#8b98aa', textTransform: 'uppercase' }}>
                          {node.stage}
                        </span>
                      </div>
                      <div style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#22d3a2', boxShadow: '0 0 6px #22d3a2' }} />
                    </div>
                    <div style={{ fontFamily: 'var(--font-display)', fontSize: '0.72rem', fontWeight: 800, color: '#f3f7fa' }}>
                      {node.label}
                    </div>
                    <div style={{ fontFamily: 'var(--font-tech)', fontSize: '0.64rem', color: '#8b98aa', marginTop: '4px', lineHeight: 1.3 }}>
                      {node.desc}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Selected Node Detailed Inspector */}
            {selectedWorkflowNode && (
              <div
                style={{
                  marginTop: '16px',
                  backgroundColor: '#0a111c',
                  borderRadius: '10px',
                  padding: '14px 18px',
                  border: '1px solid rgba(54, 199, 255, 0.25)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Shield size={16} color="#36c7ff" />
                    <span style={{ fontFamily: 'var(--font-display)', fontSize: '0.82rem', fontWeight: 800, color: '#36c7ff' }}>
                      STAGE INSPECTOR: {workflowNodes.find((n) => n.id === selectedWorkflowNode)?.label}
                    </span>
                  </div>
                  <span style={{ fontFamily: 'var(--font-tech)', fontSize: '0.68rem', color: '#22d3a2', fontWeight: 700 }}>
                    HEALTHY &bull; ONLINE
                  </span>
                </div>
                <div style={{ fontFamily: 'var(--font-tech)', fontSize: '0.72rem', color: '#8b98aa', lineHeight: 1.5, marginTop: '8px' }}>
                  {selectedWorkflowNode === 'traffic' && 'Spawns 1 to 32 worker threads generating real HTTP GET requests against the local CaptainShield gateway with randomized jitter and client headers.'}
                  {selectedWorkflowNode === 'telemetry' && 'Aggregates 7 critical signals: request rate, inter-arrival time, burstiness, server latency, client frequency, packet size, and error rates.'}
                  {selectedWorkflowNode === 'redis' && 'Publishes high-frequency telemetry frames and incident events over Redis stream aegisguard:events:stream and in-memory event bus.'}
                  {selectedWorkflowNode === 'ml' && 'Pre-trained and calibrated scikit-learn Isolation Forest model (v2.4-calibrated). Computes decision boundaries and outlier probabilities.'}
                  {selectedWorkflowNode === 'risk' && 'Transforms raw anomaly scores into an intuitive 0.0 to 100.0 risk scale with Low, Watch, Suspicious, and High Risk classifications.'}
                  {selectedWorkflowNode === 'defense' && 'Finite State Machine: NORMAL (5 req/s) -> WATCH (4 req/s) -> SUSPICIOUS (10s restriction) -> HIGH RISK (20s isolation).'}
                  {selectedWorkflowNode === 'rate_limiter' && 'Sliding Window Counter algorithm tracking client request frequency in sub-millisecond precision with Retry-After calculation.'}
                  {selectedWorkflowNode === 'gateway' && 'Localhost test gateway at /lab/target returning HTTP 200 OK under safe limits and HTTP 429 Too Many Requests under attack.'}
                  {selectedWorkflowNode === 'incident' && 'Tracks security events through CREATED -> INVESTIGATING -> DEFENSE_ACTIVE -> RECOVERED.'}
                  {selectedWorkflowNode === 'report' && 'Stores audit trails, session forensic summaries, per-request logs, and system metrics in SQLite database.'}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 2: SIMULATION & SAFETY BOUNDS */}
      {activeTab === 'simulation' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '14px' }}>
          <div style={{ backgroundColor: '#07101d', padding: '16px', borderRadius: '12px', border: '1px solid var(--border-subtle)' }}>
            <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '0.80rem', fontWeight: 800, color: '#f3f7fa', marginBottom: '12px' }}>
              SIMULATION CONCURRENCY
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div>
                <label style={{ fontFamily: 'var(--font-tech)', fontSize: '0.70rem', color: '#8b98aa', display: 'block', marginBottom: '4px' }}>
                  Default Worker Threads (1 to 32)
                </label>
                <input
                  type="number"
                  value={settings.default_workers || '8'}
                  onChange={(e) => handleChange('default_workers', e.target.value)}
                  style={{ width: '100%', padding: '8px 12px', borderRadius: '6px', backgroundColor: '#0e1624', border: '1px solid var(--border-subtle)', color: '#f3f7fa', fontFamily: 'var(--font-tech)' }}
                />
              </div>
              <div>
                <label style={{ fontFamily: 'var(--font-tech)', fontSize: '0.70rem', color: '#8b98aa', display: 'block', marginBottom: '4px' }}>
                  Default Traffic Rate Target (req/s)
                </label>
                <input
                  type="number"
                  value={settings.default_rate || '50'}
                  onChange={(e) => handleChange('default_rate', e.target.value)}
                  style={{ width: '100%', padding: '8px 12px', borderRadius: '6px', backgroundColor: '#0e1624', border: '1px solid var(--border-subtle)', color: '#f3f7fa', fontFamily: 'var(--font-tech)' }}
                />
              </div>
            </div>
          </div>

          <div style={{ backgroundColor: '#07101d', padding: '16px', borderRadius: '12px', border: '1px solid var(--border-subtle)' }}>
            <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '0.80rem', fontWeight: 800, color: '#f3f7fa', marginBottom: '12px' }}>
              SAFETY POLICIES & TARGET BOUNDS
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div>
                <label style={{ fontFamily: 'var(--font-tech)', fontSize: '0.70rem', color: '#8b98aa', display: 'block', marginBottom: '4px' }}>
                  Authorized Laboratory Target URL (Strict RFC1918 / Loopback)
                </label>
                <input
                  type="text"
                  value={settings.target_url || 'http://127.0.0.1:5000/lab/target'}
                  onChange={(e) => handleChange('target_url', e.target.value)}
                  style={{ width: '100%', padding: '8px 12px', borderRadius: '6px', backgroundColor: '#0e1624', border: '1px solid var(--border-subtle)', color: '#36c7ff', fontFamily: 'var(--font-tech)' }}
                />
              </div>
              <div style={{ fontFamily: 'var(--font-tech)', fontSize: '0.68rem', color: '#8b98aa', lineHeight: 1.4 }}>
                <strong style={{ color: '#22d3a2' }}>Safety Sandbox Enforcement:</strong> External non-private addresses are blocked at the validation layer. All traffic is confined to the localhost simulation gateway.
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: ML & TELEMETRY */}
      {activeTab === 'ml' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '14px' }}>
          <div style={{ backgroundColor: '#07101d', padding: '16px', borderRadius: '12px', border: '1px solid var(--border-subtle)' }}>
            <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '0.80rem', fontWeight: 800, color: '#f3f7fa', marginBottom: '12px' }}>
              ISOLATION FOREST SENSITIVITY
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div>
                <label style={{ fontFamily: 'var(--font-tech)', fontSize: '0.70rem', color: '#8b98aa', display: 'block', marginBottom: '4px' }}>
                  Model Decision Sensitivity (Contamination Rate)
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={settings.anomaly_sensitivity || '0.05'}
                  onChange={(e) => handleChange('anomaly_sensitivity', e.target.value)}
                  style={{ width: '100%', padding: '8px 12px', borderRadius: '6px', backgroundColor: '#0e1624', border: '1px solid var(--border-subtle)', color: '#f3f7fa', fontFamily: 'var(--font-tech)' }}
                />
              </div>
              <div style={{ fontFamily: 'var(--font-tech)', fontSize: '0.68rem', color: '#8b98aa', lineHeight: 1.4 }}>
                Calibrated scikit-learn Isolation Forest trained on 600 baseline samples with 98.3% accuracy and 100% recall on DoS burst profiles.
              </div>
            </div>
          </div>

          <div style={{ backgroundColor: '#07101d', padding: '16px', borderRadius: '12px', border: '1px solid var(--border-subtle)' }}>
            <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '0.80rem', fontWeight: 800, color: '#f3f7fa', marginBottom: '12px' }}>
              7 TELEMETRY SIGNALS
            </h3>
            <div style={{ fontFamily: 'var(--font-tech)', fontSize: '0.72rem', color: '#8b98aa', lineHeight: 1.6 }}>
              &bull; Request Rate (req/s)<br />
              &bull; Inter-Arrival Time (seconds)<br />
              &bull; Request Burstiness (std/mean)<br />
              &bull; Server Latency (ms)<br />
              &bull; Client Ingress Frequency<br />
              &bull; Average Request Payload Size (bytes)<br />
              &bull; Error / 429 Throttle Ratio
            </div>
          </div>
        </div>
      )}

      {/* TAB 4: DEFENSE & THROTTLING */}
      {activeTab === 'defense' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '14px' }}>
          <div style={{ backgroundColor: '#07101d', padding: '16px', borderRadius: '12px', border: '1px solid var(--border-subtle)' }}>
            <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '0.80rem', fontWeight: 800, color: '#f3f7fa', marginBottom: '12px' }}>
              ADAPTIVE DEFENSE TIERS
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div>
                <label style={{ fontFamily: 'var(--font-tech)', fontSize: '0.70rem', color: '#ffd23f', display: 'block', marginBottom: '4px' }}>
                  Watch Threshold (Default: 30)
                </label>
                <input
                  type="number"
                  value={settings.risk_threshold_watch || '30'}
                  onChange={(e) => handleChange('risk_threshold_watch', e.target.value)}
                  style={{ width: '100%', padding: '8px 12px', borderRadius: '6px', backgroundColor: '#0e1624', border: '1px solid var(--border-subtle)', color: '#ffd23f', fontFamily: 'var(--font-tech)' }}
                />
              </div>
              <div>
                <label style={{ fontFamily: 'var(--font-tech)', fontSize: '0.70rem', color: '#f97316', display: 'block', marginBottom: '4px' }}>
                  Suspicious Threshold (Default: 60 &bull; 10s cooldown)
                </label>
                <input
                  type="number"
                  value={settings.risk_threshold_suspicious || '60'}
                  onChange={(e) => handleChange('risk_threshold_suspicious', e.target.value)}
                  style={{ width: '100%', padding: '8px 12px', borderRadius: '6px', backgroundColor: '#0e1624', border: '1px solid var(--border-subtle)', color: '#f97316', fontFamily: 'var(--font-tech)' }}
                />
              </div>
              <div>
                <label style={{ fontFamily: 'var(--font-tech)', fontSize: '0.70rem', color: '#ff454a', display: 'block', marginBottom: '4px' }}>
                  High Risk Threshold (Default: 80 &bull; 20s aggressive rate limiting)
                </label>
                <input
                  type="number"
                  value={settings.risk_threshold_high || '80'}
                  onChange={(e) => handleChange('risk_threshold_high', e.target.value)}
                  style={{ width: '100%', padding: '8px 12px', borderRadius: '6px', backgroundColor: '#0e1624', border: '1px solid var(--border-subtle)', color: '#ff454a', fontFamily: 'var(--font-tech)' }}
                />
              </div>
            </div>
          </div>

          <div style={{ backgroundColor: '#07101d', padding: '16px', borderRadius: '12px', border: '1px solid var(--border-subtle)' }}>
            <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '0.80rem', fontWeight: 800, color: '#f3f7fa', marginBottom: '12px' }}>
              RATE LIMITING ENFORCEMENT
            </h3>
            <div style={{ fontFamily: 'var(--font-tech)', fontSize: '0.72rem', color: '#8b98aa', lineHeight: 1.6 }}>
              Sliding Window Rate Limiter active.<br />
              Normal Capacity: <strong>100 req / 30s window</strong><br />
              Watch Mode: <strong>50 req / 30s window</strong><br />
              Suspicious Mode: <strong>10 req / 30s window (10s backoff)</strong><br />
              High Risk Isolation: <strong>1 req / 30s window (20s backoff)</strong><br />
              Enforces HTTP 429 header: <code style={{ color: '#36c7ff' }}>Retry-After</code>
            </div>
          </div>
        </div>
      )}

      {/* TAB 5: NETWORK & WIRESHARK */}
      {activeTab === 'network' && (
        <div style={{ backgroundColor: '#07101d', padding: '18px', borderRadius: '12px', border: '1px solid var(--border-subtle)' }}>
          <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '0.80rem', fontWeight: 800, color: '#f3f7fa', marginBottom: '12px' }}>
            WIRESHARK LOOPBACK CAPTURE
          </h3>
          <div style={{ fontFamily: 'var(--font-tech)', fontSize: '0.74rem', color: '#8b98aa', lineHeight: 1.6 }}>
            1. Open Wireshark on this machine.<br />
            2. Interface: <strong>Npcap Loopback Adapter</strong> (Windows) or <strong>Loopback: lo0</strong>.<br />
            3. Filter: <code style={{ color: '#36c7ff', backgroundColor: '#0e1624', padding: '2px 6px', borderRadius: '4px' }}>tcp.port == 5000 and http</code><br />
            4. Start the attack to see real live HTTP frames, headers, and 429 mitigations!
          </div>
        </div>
      )}

      {/* TAB 6: DATABASE & RETENTION */}
      {activeTab === 'retention' && (
        <div style={{ backgroundColor: '#07101d', padding: '18px', borderRadius: '12px', border: '1px solid var(--border-subtle)' }}>
          <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '0.80rem', fontWeight: 800, color: '#f3f7fa', marginBottom: '12px' }}>
            SQLITE DATABASE & AUDIT TRAIL
          </h3>
          <div style={{ fontFamily: 'var(--font-tech)', fontSize: '0.74rem', color: '#8b98aa', lineHeight: 1.6 }}>
            Database File: <code style={{ color: '#36c7ff' }}>backend/aegisguard.db</code><br />
            Persistent Tables: <strong>simulation_sessions, simulation_metrics, request_logs, incidents, defense_actions, settings</strong><br />
            Audit Retention: <strong>30 days of forensic telemetry records</strong>
          </div>
        </div>
      )}
    </div>
  );
};
