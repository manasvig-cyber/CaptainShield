import React, { useState, useEffect } from 'react';
import { Sidebar } from './Sidebar';
import { TopBar } from './TopBar';
import { HeroSection } from './HeroSection';
import { Scene3D } from './Scene3D';
import { MetricsPanel } from './MetricsPanel';
import { LabModal } from './LabModal';
import { LiveSimulationView } from './LiveSimulationView';
import { ThreatMatrixView } from './ThreatMatrixView';
import { RecentView } from './RecentView';
import { SettingsView } from './SettingsView';
import { WiresharkLabView } from './WiresharkLabView';
import { type ConsoleEvent } from './LiveConsole';
import { api } from '../services/api';

export const Dashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'home' | 'simulation' | 'matrix' | 'recent' | 'settings' | 'wireshark'>('home');
  const [isLabModalOpen, setIsLabModalOpen] = useState(false);
  const [isSimulating, setIsSimulating] = useState(false);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [matrixSessionId, setMatrixSessionId] = useState<string | null>(null);

  // System Health
  const [health, setHealth] = useState({
    redis_connected: false,
    ml_detector_loaded: true,
    traffic_generator_active: false,
  });

  // Live Simulation Telemetry State
  const [currentSim, setCurrentSim] = useState<any>({
    status: 'IDLE',
    session_id: null,
    metrics: {
      total_requests: 0,
      successful_requests: 0,
      blocked_requests: 0,
      error_requests: 0,
      active_clients: 0,
      peak_rate: 0,
      average_rate: 0,
      defense_capacity: 100.0,
      average_latency_ms: 0,
    },
    defense: {
      defense_level: 'NORMAL',
      current_rate_limit: 100,
      burst_allowance: 20,
      rate_limit_action: 'NORMAL_RATE_LIMIT',
    },
    ml: {
      current_risk_score: 0.0,
      risk_level: 'LOW',
      is_anomaly: false,
    },
    telemetry_features: {
      request_rate: 0,
      request_interval: 0.05,
      request_burstiness: 1.0,
      response_latency: 2.5,
      client_frequency: 0,
      request_size: 256,
      error_rate: 0,
    },
    active_incident: null,
  });

  // Redis Stream Events for LiveConsole
  const [events, setEvents] = useState<ConsoleEvent[]>([]);

  // Poll Health status every 3.5 seconds
  useEffect(() => {
    let isMounted = true;
    const checkHealth = async () => {
      try {
        const res = await api.getHealth();
        if (isMounted && res) {
          setHealth({
            redis_connected: !!res.redis_connected,
            ml_detector_loaded: !!res.ml_detector_loaded,
            traffic_generator_active: !!res.traffic_generator_active,
          });
        }
      } catch (err) {
        // Fallback when backend is initializing
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 3500);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  // Poll live simulation metrics & Redis events continuously across all pages
  useEffect(() => {
    let isMounted = true;
    let pollInterval: any = null;

    const poll = async () => {
      try {
        const simData = await api.getCurrentSimulation();
        if (!isMounted) return;

        if (simData) {
          setCurrentSim(simData);
          if (simData.is_running) {
            setIsSimulating(true);
          } else if (isSimulating && simData.status === 'COMPLETED') {
            setIsSimulating(false);
          }

          if (simData.session_id) {
            setActiveSessionId(simData.session_id);
          }

          // Fetch recent events from Redis Stream if session exists
          const sid = simData?.session_id || activeSessionId;
          if (sid) {
            const evData = await api.getEvents(sid, 30);
            if (isMounted && evData?.events) {
              const formatted = evData.events.map((e: any) => ({
                timestamp: e.timestamp,
                type: e.type,
                message: e.message,
                level: e.level,
              }));
              setEvents(formatted);
            }
          }
        }
      } catch (err) {
        // Keep resilient
      }
    };

    poll();
    pollInterval = setInterval(poll, 750);

    return () => {
      isMounted = false;
      if (pollInterval) clearInterval(pollInterval);
    };
  }, [activeSessionId, isSimulating]);

  // START ATTACK: Continuous packet generation + Transition to Page 2 (Live Simulation)
  const handleStartAttack = async () => {
    try {
      const res = await api.startSimulation({
        preset: 'Controlled Attack',
        workers: 8,
        request_interval: 0.04,
        jitter: 0.015,
        duration: 86400, // Continuous packet transmission until user stops
        target_url: 'http://127.0.0.1:5000/lab/target',
      });

      if (res && res.session_id) {
        setActiveSessionId(res.session_id);
        setIsSimulating(true);
        // Switch to Page 2 (Live Attack / SOC Monitoring)
        setActiveTab('simulation');
        setEvents([
          {
            timestamp: Date.now() / 1000,
            type: 'TRAFFIC_INIT',
            message: `Continuous traffic generator dispatched against http://127.0.0.1:5000/lab/target (8 workers)`,
            level: 'INFO',
          },
        ]);
      }
    } catch (err: any) {
      console.error('Failed to start simulation:', err);
    }
  };

  // STOP SIMULATION: Terminate generator + Finalize + Redirect to Page 3 (Threat Matrix)
  const handleStopSimulation = async () => {
    try {
      const res = await api.stopSimulation('User halted simulation');
      setIsSimulating(false);

      const stoppedId = res?.session_id || activeSessionId;
      if (stoppedId) {
        setMatrixSessionId(stoppedId);
        // Navigate immediately to Threat Matrix forensic dashboard
        setActiveTab('matrix');
      }
    } catch (err) {
      console.error('Failed to stop simulation:', err);
      setIsSimulating(false);
      setActiveTab('matrix');
    }
  };

  // Sidebar navigation handler
  const handleSelectTab = (tab: string) => {
    if (tab === 'home') setActiveTab('home');
    else if (tab === 'simulation') setActiveTab('simulation');
    else if (tab === 'matrix') setActiveTab('matrix');
    else if (tab === 'recent') setActiveTab('recent');
    else if (tab === 'settings') setActiveTab('settings');
    else if (tab === 'help') setActiveTab('wireshark');
  };

  const simulationActive = isSimulating || health.traffic_generator_active || !!currentSim.is_running;

  return (
    <div
      style={{
        display: 'flex',
        width: '100%',
        height: '100%',
        position: 'relative',
        overflow: 'hidden',
        backgroundColor: '#03060b',
      }}
    >
      {/* 1. Left Fixed Sidebar */}
      <Sidebar
        activeTab={activeTab === 'wireshark' ? 'help' : activeTab}
        onSelectTab={handleSelectTab}
        ingressMbps={simulationActive ? +(currentSim.metrics.peak_rate * 0.08 + 12.4).toFixed(2) : 94.74}
        mitigationMbps={simulationActive ? +(currentSim.metrics.blocked_requests > 0 ? (currentSim.metrics.peak_rate * 0.07 + 8.1) : 4.2).toFixed(2) : 95.42}
        isSimulating={simulationActive}
      />

      {/* 2. Main Content Viewport */}
      <div
        style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          position: 'relative',
          height: '100%',
          minHeight: 0,
          overflow: 'hidden',
        }}
      >
        {/* Top Header Bar */}
        <TopBar
          onSearch={(q) => console.log('Searching telemetry:', q)}
          redisConnected={health.redis_connected}
          mlLoaded={health.ml_detector_loaded}
          trafficActive={simulationActive}
          onOpenSimulation={() => setActiveTab('simulation')}
        />

        {/* View Switcher Container with proper flex scrolling */}
        <div
          style={{
            flex: 1,
            position: 'relative',
            width: '100%',
            height: 'calc(100% - 56px)',
            minHeight: 0,
            overflowY: 'auto',
            overflowX: 'hidden',
          }}
        >
          {/* ======================================================== */}
          {/* PAGE 1: HOME / LANDING (Clean, Minimal, 3D Voxel Core)  */}
          {/* ======================================================== */}
          {activeTab === 'home' && (
            <>
              {/* Left Headline & Tech Info Badge */}
              <HeroSection onLearnMore={() => setIsLabModalOpen(true)} />

              {/* Central 3D Black & Purple Voxel Core with Floating Cubes */}
              <Scene3D viewMode="home" />

              {/* Right Defense Capacity Card & START ATTACK CTA */}
              <MetricsPanel
                isSimulating={simulationActive}
                capacity={currentSim.defense_capacity || currentSim.metrics?.defense_capacity || 100.0}
                requestsSent={currentSim.metrics?.total_requests || currentSim.total_requests || 0}
                successfulRequests={currentSim.metrics?.successful_requests || currentSim.successful_requests || 0}
                blockedRequests={currentSim.metrics?.blocked_requests || currentSim.blocked_requests || 0}
                activeClients={currentSim.metrics?.active_clients || currentSim.active_clients || 0}
                telemetryCount={currentSim.metrics?.total_requests || 0}
                incidentCount={currentSim.metrics?.incident_count || 0}
                onStartAttack={handleStartAttack}
                onStopSimulation={handleStopSimulation}
                onOpenLiveSOC={() => setActiveTab('simulation')}
              />
            </>
          )}

          {/* ======================================================== */}
          {/* PAGE 2: LIVE ATTACK / SOC MONITORING (Information Dense) */}
          {/* ======================================================== */}
          {activeTab === 'simulation' && (
            <LiveSimulationView
              sessionId={activeSessionId || currentSim.session_id || 'SIM-ACTIVE'}
              isSimulating={isSimulating}
              metrics={currentSim.metrics}
              defense={currentSim.defense}
              ml={currentSim.ml}
              telemetryFeatures={currentSim.telemetry_features}
              activeIncident={currentSim.active_incident}
              events={events}
              onClearEvents={() => setEvents([])}
              onStopSimulation={handleStopSimulation}
            />
          )}

          {/* ======================================================== */}
          {/* PAGE 3: THREAT MATRIX FORENSIC REPORT                    */}
          {/* ======================================================== */}
          {activeTab === 'matrix' && (
            <ThreatMatrixView
              sessionId={matrixSessionId || ''}
              onBack={() => setActiveTab('home')}
            />
          )}

          {/* ======================================================== */}
          {/* PAGE 4: RECENT SIMULATION HISTORY & AUDIT TRAIL          */}
          {/* ======================================================== */}
          {activeTab === 'recent' && (
            <RecentView
              onViewReport={(id) => {
                setMatrixSessionId(id);
                setActiveTab('matrix');
              }}
            />
          )}


          {/* ======================================================== */}
          {/* PAGE 6: LABORATORY SETTINGS & SAFETY POLICIES           */}
          {/* ======================================================== */}
          {activeTab === 'settings' && <SettingsView />}

          {/* ======================================================== */}
          {/* WIRESHARK LOOPBACK LAB WALKTHROUGH & TEST PROBE         */}
          {/* ======================================================== */}
          {activeTab === 'wireshark' && (
            <WiresharkLabView onBack={() => setActiveTab('home')} />
          )}
        </div>
      </div>

      {/* Interactive Cyber Defense Simulation Modal */}
      <LabModal
        isOpen={isLabModalOpen}
        onClose={() => setIsLabModalOpen(false)}
        isSimulating={isSimulating}
        setIsSimulating={setIsSimulating}
      />
    </div>
  );
};
