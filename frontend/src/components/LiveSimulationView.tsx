import React, { Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { 
  Square, 
  ShieldAlert, 
  Activity, 
  Cpu, 
  AlertTriangle, 
  CheckCircle2, 
  Ban, 
  Radio, 
  Clock, 
  Zap,
  Globe2
} from 'lucide-react';
import { DefensePipeline } from './DefensePipeline';
import { LiveConsole, type ConsoleEvent } from './LiveConsole';
import { CyberGlobe } from './CyberGlobe';

interface LiveSimulationViewProps {
  sessionId: string;
  isSimulating: boolean;
  metrics: {
    total_requests: number;
    successful_requests: number;
    blocked_requests: number;
    error_requests: number;
    active_clients: number;
    peak_rate: number;
    average_rate: number;
    defense_capacity: number;
    average_latency_ms: number;
  };
  defense: {
    defense_level: string;
    current_rate_limit: number;
    burst_allowance: number;
    rate_limit_action: string;
  };
  ml: {
    current_risk_score: number;
    risk_level: string;
    is_anomaly: boolean;
  };
  telemetryFeatures?: {
    request_rate: number;
    request_interval: number;
    request_burstiness: number;
    response_latency: number;
    client_frequency: number;
    request_size: number;
    error_rate: number;
  };
  activeIncident?: any;
  events: ConsoleEvent[];
  onClearEvents?: () => void;
  onStopSimulation: () => void;
}

export const LiveSimulationView: React.FC<LiveSimulationViewProps> = ({
  sessionId,
  isSimulating,
  metrics,
  defense,
  ml,
  telemetryFeatures,
  activeIncident,
  events,
  onClearEvents,
  onStopSimulation,
}) => {
  const riskScore = ml.current_risk_score || 0;
  const isHighRisk = riskScore >= 60;
  const total = Math.max(1, metrics.total_requests);
  const successPct = Math.round((metrics.successful_requests / total) * 100);
  const blockedPct = Math.round((metrics.blocked_requests / total) * 100);

  // Format numbers nicely
  const fmt = (n: number) => n.toLocaleString();

  return (
    <div
      style={{
        padding: '16px 24px',
        minHeight: '100%',
        display: 'flex',
        flexDirection: 'column',
        gap: '14px',
        backgroundColor: '#050810',
        position: 'relative',
        zIndex: 20,
      }}
    >
      {/* ======================================================== */}
      {/* 1. TOP BAR: PIPELINE & ACTION CONTROLS (STICKY)          */}
      {/* ======================================================== */}
      <div
        style={{
          position: 'sticky',
          top: 0,
          zIndex: 60,
          backgroundColor: '#050810',
          paddingTop: '6px',
          paddingBottom: '12px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '16px',
          flexWrap: 'wrap',
          boxShadow: '0 6px 20px rgba(5, 8, 16, 0.95)',
          borderBottom: '1px solid rgba(90, 140, 190, 0.15)',
        }}
      >
        {/* 7-Stage Defensive Pipeline (Reference 1) */}
        <DefensePipeline
          isRunning={isSimulating}
          riskScore={riskScore}
          defenseLevel={defense.defense_level}
          rateLimitAction={defense.rate_limit_action}
          has429={metrics.blocked_requests > 0}
        />

        {/* Right Status Badge & Prominent STOP SIMULATION Button */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div
            style={{
              padding: '6px 14px',
              borderRadius: '8px',
              backgroundColor: 'rgba(239, 68, 68, 0.15)',
              border: '1px solid rgba(239, 68, 68, 0.5)',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              fontFamily: 'var(--font-tech)',
              fontSize: '0.74rem',
              fontWeight: 700,
              color: '#ef4444',
            }}
          >
            <Radio size={13} className="pulse" />
            <span>SESSION: {sessionId || 'ACTIVE'}</span>
          </div>

          <button
            onClick={onStopSimulation}
            style={{
              padding: '10px 22px',
              borderRadius: '10px',
              border: '1px solid rgba(255, 69, 74, 0.8)',
              backgroundColor: '#ef4444',
              color: '#ffffff',
              fontFamily: 'var(--font-display)',
              fontSize: '0.80rem',
              fontWeight: 800,
              letterSpacing: '0.08em',
              textTransform: 'uppercase',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              boxShadow: '0 0 25px rgba(239, 68, 68, 0.7)',
              transition: 'all 0.2s ease',
            }}
          >
            <Square size={14} fill="#ffffff" />
            <span>STOP SIMULATION</span>
          </button>
        </div>
      </div>

      {/* ======================================================== */}
      {/* 2. TOP METRICS STRIP: 5 Core Telemetry Counters          */}
      {/* ======================================================== */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '12px' }}>
        {/* ML Risk Score */}
        <div style={{ backgroundColor: '#101927', padding: '12px 14px', borderRadius: '12px', border: '1px solid var(--border-subtle)' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontFamily: 'var(--font-tech)', fontSize: '0.68rem', color: '#8b98aa' }}>ML RISK SCORE</span>
            <AlertTriangle size={14} color={isHighRisk ? '#ef4444' : '#ffd83d'} />
          </div>
          <div style={{ fontFamily: 'var(--font-display)', fontSize: '1.45rem', fontWeight: 800, color: isHighRisk ? '#ef4444' : '#ffd83d', marginTop: '4px' }}>
            {riskScore.toFixed(1)} <span style={{ fontSize: '0.75rem', color: '#8b98aa' }}>/ 100</span>
          </div>
          <div style={{ fontFamily: 'var(--font-tech)', fontSize: '0.68rem', color: isHighRisk ? '#ef4444' : '#36c7ff', marginTop: '2px', fontWeight: 600 }}>
            {ml.risk_level} &bull; {ml.is_anomaly ? 'ANOMALY DETECTED' : 'NORMAL PATTERN'}
          </div>
        </div>

        {/* Real-time Ingress Rate */}
        <div style={{ backgroundColor: '#101927', padding: '12px 14px', borderRadius: '12px', border: '1px solid var(--border-subtle)' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontFamily: 'var(--font-tech)', fontSize: '0.68rem', color: '#8b98aa' }}>TRAFFIC RATE</span>
            <Activity size={14} color="#36c7ff" />
          </div>
          <div style={{ fontFamily: 'var(--font-display)', fontSize: '1.45rem', fontWeight: 800, color: '#f3f7fa', marginTop: '4px' }}>
            {metrics.peak_rate.toFixed(1)} <span style={{ fontSize: '0.75rem', color: '#8b98aa' }}>req/s</span>
          </div>
          <div style={{ fontFamily: 'var(--font-tech)', fontSize: '0.68rem', color: '#8b98aa', marginTop: '2px' }}>
            Avg: {metrics.average_rate.toFixed(1)} req/s &bull; {metrics.active_clients} Workers
          </div>
        </div>

        {/* Requests & HTTP 429 Blocks */}
        <div style={{ backgroundColor: '#101927', padding: '12px 14px', borderRadius: '12px', border: '1px solid var(--border-subtle)' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontFamily: 'var(--font-tech)', fontSize: '0.68rem', color: '#8b98aa' }}>HTTP 429 THROTTLED</span>
            <Ban size={14} color={metrics.blocked_requests > 0 ? '#ffd83d' : '#8b98aa'} />
          </div>
          <div style={{ fontFamily: 'var(--font-display)', fontSize: '1.45rem', fontWeight: 800, color: metrics.blocked_requests > 0 ? '#ffd83d' : '#f3f7fa', marginTop: '4px' }}>
            {fmt(metrics.blocked_requests)} <span style={{ fontSize: '0.75rem', color: '#8b98aa' }}>/ {fmt(metrics.total_requests)}</span>
          </div>
          <div style={{ fontFamily: 'var(--font-tech)', fontSize: '0.68rem', color: '#ffd83d', marginTop: '2px' }}>
            {blockedPct}% traffic rate-limited
          </div>
        </div>

        {/* Latency */}
        <div style={{ backgroundColor: '#101927', padding: '12px 14px', borderRadius: '12px', border: '1px solid var(--border-subtle)' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontFamily: 'var(--font-tech)', fontSize: '0.68rem', color: '#8b98aa' }}>AVG LATENCY</span>
            <Clock size={14} color="#22d3a2" />
          </div>
          <div style={{ fontFamily: 'var(--font-display)', fontSize: '1.45rem', fontWeight: 800, color: '#f3f7fa', marginTop: '4px' }}>
            {metrics.average_latency_ms.toFixed(1)} <span style={{ fontSize: '0.75rem', color: '#8b98aa' }}>ms</span>
          </div>
          <div style={{ fontFamily: 'var(--font-tech)', fontSize: '0.68rem', color: '#22d3a2', marginTop: '2px' }}>
            Target: 127.0.0.1:5000
          </div>
        </div>

        {/* Defense Capacity */}
        <div style={{ backgroundColor: '#101927', padding: '12px 14px', borderRadius: '12px', border: '1px solid var(--border-subtle)' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontFamily: 'var(--font-tech)', fontSize: '0.68rem', color: '#8b98aa' }}>DEFENSE CAPACITY</span>
            <CheckCircle2 size={14} color="#22d3a2" />
          </div>
          <div style={{ fontFamily: 'var(--font-display)', fontSize: '1.45rem', fontWeight: 800, color: '#22d3a2', marginTop: '4px' }}>
            {metrics.defense_capacity.toFixed(0)}%
          </div>
          <div style={{ fontFamily: 'var(--font-tech)', fontSize: '0.68rem', color: '#8b98aa', marginTop: '2px' }}>
            Defense Tier: {defense.defense_level}
          </div>
        </div>
      </div>

      {/* ======================================================== */}
      {/* 3. MAIN AREA: LARGE 3D GLOBE (LEFT) & METRICS (RIGHT)    */}
      {/* ======================================================== */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '14px', minHeight: '380px' }}>
        {/* LEFT / CENTER: LARGE 3D ACTIVE GLOBE (RED THREAT VISUALIZATION) */}
        <div
          style={{
            backgroundColor: '#0a111c',
            borderRadius: '16px',
            border: isHighRisk ? '1px solid rgba(239, 68, 68, 0.4)' : '1px solid var(--border-subtle)',
            boxShadow: isHighRisk ? '0 0 35px rgba(239, 68, 68, 0.15)' : 'none',
            position: 'relative',
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          {/* Top Stage Header Overlay */}
          <div
            style={{
              padding: '12px 16px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              borderBottom: '1px solid rgba(255, 255, 255, 0.06)',
              zIndex: 10,
              backgroundColor: 'rgba(10, 17, 28, 0.75)',
              backdropFilter: 'blur(8px)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Globe2 size={16} color={isHighRisk ? '#ef4444' : '#36c7ff'} />
              <span style={{ fontFamily: 'var(--font-display)', fontSize: '0.78rem', fontWeight: 800, color: '#f3f7fa', letterSpacing: '0.05em' }}>
                CYBER THREAT TOPOLOGY GLOBE
              </span>
            </div>

            {/* Dynamic Status Badge */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '4px 10px',
                borderRadius: '6px',
                backgroundColor: isHighRisk ? 'rgba(239, 68, 68, 0.2)' : 'rgba(34, 211, 162, 0.15)',
                border: isHighRisk ? '1px solid rgba(239, 68, 68, 0.5)' : '1px solid rgba(34, 211, 162, 0.4)',
                fontFamily: 'var(--font-tech)',
                fontSize: '0.68rem',
                fontWeight: 700,
                color: isHighRisk ? '#ff454a' : '#22d3a2',
              }}
            >
              <div
                style={{
                  width: '6px',
                  height: '6px',
                  borderRadius: '50%',
                  backgroundColor: isHighRisk ? '#ff454a' : '#22d3a2',
                  boxShadow: isHighRisk ? '0 0 8px #ff454a' : '0 0 8px #22d3a2',
                }}
              />
              <span>{isHighRisk ? '🔴 ACTIVE THREAT DETECTED' : '🟢 MITIGATION ACTIVE'}</span>
            </div>
          </div>

          {/* Dedicated 3D Cyber Globe Canvas Container (pointerEvents: none allows seamless mouse wheel scrolling) */}
          <div style={{ flex: 1, position: 'relative', width: '100%', minHeight: '300px', pointerEvents: 'none' }}>
            <Canvas
              camera={{ position: [0, 0.6, 6.4], fov: 44 }}
              gl={{
                antialias: true,
                alpha: true,
                powerPreference: 'high-performance',
              }}
              dpr={[1, 2]}
            >
              <Suspense fallback={null}>
                {/* Lighting tailored for red threat atmosphere */}
                <ambientLight intensity={0.9} color="#07101d" />
                <directionalLight
                  position={[6, 8, 5]}
                  intensity={2.4}
                  color={isHighRisk ? '#ef4444' : '#168bff'}
                />
                <directionalLight
                  position={[-6, -4, -4]}
                  intensity={1.6}
                  color={isHighRisk ? '#ff6b6b' : '#36c7ff'}
                />

                {/* Upgraded Active Attack Cyber Threat Globe */}
                <CyberGlobe
                  simulationState={isHighRisk ? 'HIGH_RISK' : 'RUNNING'}
                  riskScore={riskScore}
                  requestRate={metrics.peak_rate}
                  blockedRequests={metrics.blocked_requests}
                  successfulRequests={metrics.successful_requests}
                  activeClients={metrics.active_clients}
                />
              </Suspense>
            </Canvas>

            {/* Overlaid HUD Metrics Strip */}
            <div
              style={{
                position: 'absolute',
                bottom: '12px',
                left: '14px',
                right: '14px',
                display: 'flex',
                justifyContent: 'space-between',
                padding: '8px 12px',
                backgroundColor: 'rgba(7, 16, 29, 0.85)',
                borderRadius: '8px',
                border: '1px solid rgba(255, 255, 255, 0.08)',
                backdropFilter: 'blur(6px)',
                fontFamily: 'var(--font-tech)',
                fontSize: '0.68rem',
                color: '#8b98aa',
                pointerEvents: 'none',
              }}
            >
              <div>
                STREAM: <span style={{ color: '#f3f7fa', fontWeight: 700 }}>{metrics.peak_rate.toFixed(1)} req/s</span>
              </div>
              <div>
                INTERCEPTIONS: <span style={{ color: '#ffd83d', fontWeight: 700 }}>{metrics.blocked_requests} (429)</span>
              </div>
              <div>
                DEFENSE: <span style={{ color: '#22d3a2', fontWeight: 700 }}>{defense.defense_level}</span>
              </div>
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN: REQUEST OUTCOME MAP & 7-FEATURE TELEMETRY */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {/* Live Request Flow Map & Outcome Bar */}
          <div
            style={{
              backgroundColor: '#0a111c',
              borderRadius: '14px',
              border: '1px solid var(--border-subtle)',
              padding: '16px 18px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Zap size={15} color="#36c7ff" />
                <span style={{ fontFamily: 'var(--font-display)', fontSize: '0.78rem', fontWeight: 700, color: '#f3f7fa' }}>
                  LIVE REQUEST OUTCOME & DEFENSE FLOW
                </span>
              </div>
              <span style={{ fontFamily: 'var(--font-tech)', fontSize: '0.70rem', color: '#8b98aa' }}>
                Sliding Window
              </span>
            </div>

            {/* Flow Metrics */}
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(3, 1fr)',
                gap: '8px',
                padding: '12px',
                backgroundColor: '#07101d',
                borderRadius: '10px',
                border: '1px solid rgba(255, 255, 255, 0.05)',
                marginBottom: '12px',
              }}
            >
              {/* Total Ingress */}
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontFamily: 'var(--font-tech)', fontSize: '0.64rem', color: '#8b98aa' }}>TOTAL</div>
                <div style={{ fontFamily: 'var(--font-display)', fontSize: '1.10rem', fontWeight: 800, color: '#f3f7fa', marginTop: '2px' }}>
                  {fmt(metrics.total_requests)}
                </div>
                <div style={{ fontFamily: 'var(--font-tech)', fontSize: '0.60rem', color: '#36c7ff' }}>Packets</div>
              </div>

              {/* Passed 200 */}
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontFamily: 'var(--font-tech)', fontSize: '0.64rem', color: '#8b98aa' }}>SUCCESS (200)</div>
                <div style={{ fontFamily: 'var(--font-display)', fontSize: '1.10rem', fontWeight: 800, color: '#22d3a2', marginTop: '2px' }}>
                  {fmt(metrics.successful_requests)}
                </div>
                <div style={{ fontFamily: 'var(--font-tech)', fontSize: '0.60rem', color: '#22d3a2' }}>{successPct}% Benign</div>
              </div>

              {/* Blocked 429 */}
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontFamily: 'var(--font-tech)', fontSize: '0.64rem', color: '#8b98aa' }}>BLOCKED (429)</div>
                <div style={{ fontFamily: 'var(--font-display)', fontSize: '1.10rem', fontWeight: 800, color: '#ffd83d', marginTop: '2px' }}>
                  {fmt(metrics.blocked_requests)}
                </div>
                <div style={{ fontFamily: 'var(--font-tech)', fontSize: '0.60rem', color: '#ffd83d' }}>{blockedPct}% Defended</div>
              </div>
            </div>

            {/* Proportion Bar */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontFamily: 'var(--font-tech)', fontSize: '0.68rem', color: '#8b98aa', marginBottom: '6px' }}>
                <span>Passed: {successPct}% &bull; Rate Limited: {blockedPct}%</span>
                <span>Action: {defense.rate_limit_action}</span>
              </div>
              <div style={{ height: '8px', width: '100%', backgroundColor: '#141f30', borderRadius: '4px', overflow: 'hidden', display: 'flex' }}>
                <div style={{ width: `${successPct}%`, backgroundColor: '#22d3a2', transition: 'width 0.3s' }} />
                <div style={{ width: `${blockedPct}%`, backgroundColor: '#ef4444', transition: 'width 0.3s' }} />
              </div>
            </div>
          </div>

          {/* 7-Feature Telemetry Extraction Matrix */}
          <div
            style={{
              backgroundColor: '#0a111c',
              borderRadius: '14px',
              border: '1px solid var(--border-subtle)',
              padding: '14px 18px',
              flex: 1,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
              <Cpu size={15} color="#36c7ff" />
              <span style={{ fontFamily: 'var(--font-display)', fontSize: '0.78rem', fontWeight: 700, color: '#f3f7fa' }}>
                ISOLATION FOREST 7-FEATURE TELEMETRY
              </span>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '8px' }}>
              <div style={{ backgroundColor: '#101927', padding: '7px 10px', borderRadius: '8px' }}>
                <div style={{ fontFamily: 'var(--font-tech)', fontSize: '0.62rem', color: '#8b98aa' }}>1. Request Rate</div>
                <div style={{ fontFamily: 'var(--font-tech)', fontSize: '0.84rem', fontWeight: 700, color: '#f3f7fa' }}>
                  {(telemetryFeatures?.request_rate || metrics.peak_rate).toFixed(1)} req/s
                </div>
              </div>

              <div style={{ backgroundColor: '#101927', padding: '7px 10px', borderRadius: '8px' }}>
                <div style={{ fontFamily: 'var(--font-tech)', fontSize: '0.62rem', color: '#8b98aa' }}>2. Inter-Arrival Interval</div>
                <div style={{ fontFamily: 'var(--font-tech)', fontSize: '0.84rem', fontWeight: 700, color: '#36c7ff' }}>
                  {(telemetryFeatures?.request_interval || 0.04).toFixed(3)} s
                </div>
              </div>

              <div style={{ backgroundColor: '#101927', padding: '7px 10px', borderRadius: '8px' }}>
                <div style={{ fontFamily: 'var(--font-tech)', fontSize: '0.62rem', color: '#8b98aa' }}>3. Arrival Burstiness</div>
                <div style={{ fontFamily: 'var(--font-tech)', fontSize: '0.84rem', fontWeight: 700, color: isHighRisk ? '#ef4444' : '#22d3a2' }}>
                  {(telemetryFeatures?.request_burstiness || 1.0).toFixed(2)}
                </div>
              </div>

              <div style={{ backgroundColor: '#101927', padding: '7px 10px', borderRadius: '8px' }}>
                <div style={{ fontFamily: 'var(--font-tech)', fontSize: '0.62rem', color: '#8b98aa' }}>4. Response Latency</div>
                <div style={{ fontFamily: 'var(--font-tech)', fontSize: '0.84rem', fontWeight: 700, color: '#f3f7fa' }}>
                  {(telemetryFeatures?.response_latency || metrics.average_latency_ms).toFixed(1)} ms
                </div>
              </div>

              <div style={{ backgroundColor: '#101927', padding: '7px 10px', borderRadius: '8px' }}>
                <div style={{ fontFamily: 'var(--font-tech)', fontSize: '0.62rem', color: '#8b98aa' }}>5. Client Frequency</div>
                <div style={{ fontFamily: 'var(--font-tech)', fontSize: '0.84rem', fontWeight: 700, color: '#36c7ff' }}>
                  {metrics.active_clients} clients
                </div>
              </div>

              <div style={{ backgroundColor: '#101927', padding: '7px 10px', borderRadius: '8px' }}>
                <div style={{ fontFamily: 'var(--font-tech)', fontSize: '0.62rem', color: '#8b98aa' }}>6. Error Rate</div>
                <div style={{ fontFamily: 'var(--font-tech)', fontSize: '0.84rem', fontWeight: 700, color: metrics.error_requests > 0 ? '#ef4444' : '#22d3a2' }}>
                  {metrics.error_requests === 0 ? '0.0%' : `${((metrics.error_requests / total) * 100).toFixed(1)}%`}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ======================================================== */}
      {/* 4. BOTTOM AREA: LIVE SOC EVENT CONSOLE & INCIDENTS       */}
      {/* ======================================================== */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '14px' }}>
        {/* Live SOC Event Console (Redis Stream) */}
        <LiveConsole
          events={events}
          onClear={onClearEvents}
        />

        {/* Active Incident Lifecycle Tracker & Adaptive Policy */}
        <div
          style={{
            backgroundColor: '#0a111c',
            borderRadius: '14px',
            border: '1px solid var(--border-subtle)',
            padding: '14px 18px',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <ShieldAlert size={15} color={isHighRisk ? '#ef4444' : '#22d3a2'} />
              <span style={{ fontFamily: 'var(--font-display)', fontSize: '0.76rem', fontWeight: 700, color: '#f3f7fa' }}>
                INCIDENT LIFECYCLE FORENSICS
              </span>
            </div>
            <span
              style={{
                fontFamily: 'var(--font-tech)',
                fontSize: '0.68rem',
                fontWeight: 700,
                color: isHighRisk ? '#ef4444' : '#22d3a2',
                backgroundColor: isHighRisk ? 'rgba(239, 68, 68, 0.15)' : 'rgba(34, 211, 162, 0.15)',
                padding: '2px 8px',
                borderRadius: '4px',
              }}
            >
              {activeIncident ? activeIncident.status : (isHighRisk ? 'DEFENSE ACTIVE' : 'MONITORING')}
            </span>
          </div>

          <div style={{ fontFamily: 'var(--font-tech)', fontSize: '0.72rem', color: '#8b98aa', lineHeight: 1.5, marginTop: '8px' }}>
            <div>
              <strong>Trigger:</strong> {activeIncident ? activeIncident.description : (isHighRisk ? 'Volumetric burst detected by Isolation Forest' : 'Continuous baseline monitoring')}
            </div>
            <div style={{ marginTop: '4px' }}>
              <strong>Adaptive Action:</strong> {defense.rate_limit_action} ({defense.current_rate_limit} req / 30s ceiling)
            </div>
          </div>

          {/* Incident State Stepper */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '10px' }}>
            {['OPEN', 'INVESTIGATING', 'DEFENSE ACTIVE', 'RECOVERED'].map((step, idx) => {
              const isPassed = idx <= (isHighRisk ? 2 : 0);
              return (
                <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <div
                    style={{
                      width: '8px',
                      height: '8px',
                      borderRadius: '50%',
                      backgroundColor: isPassed ? '#22d3a2' : '#1e293b',
                      boxShadow: isPassed ? '0 0 8px #22d3a2' : 'none',
                    }}
                  />
                  <span style={{ fontFamily: 'var(--font-tech)', fontSize: '0.60rem', color: isPassed ? '#f3f7fa' : '#475569' }}>
                    {step}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};
