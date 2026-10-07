import React, { Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { CyberGlobe } from './CyberGlobe';
import { DataCore } from './DataCore';
import { FloatingBlocks } from './FloatingBlocks';

interface Scene3DProps {
  viewMode?: 'home' | 'simulation';
  simulationState?: 'IDLE' | 'RUNNING' | 'DEFENDING' | 'HIGH_RISK' | 'STOPPING' | 'COMPLETED';
  riskScore?: number;
  requestRate?: number;
  blockedRequests?: number;
  successfulRequests?: number;
  activeClients?: number;
  mouseX?: number;
  mouseY?: number;
}

export const Scene3D: React.FC<Scene3DProps> = ({
  viewMode = 'home',
  simulationState = 'IDLE',
  riskScore = 0.0,
  requestRate = 0,
  blockedRequests = 0,
  successfulRequests = 0,
  activeClients = 0,
}) => {
  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        pointerEvents: 'auto',
        zIndex: 5,
        overflow: 'hidden',
      }}
    >
      <Canvas
        camera={{ position: [0, 0.7, 7.0], fov: 42 }}
        gl={{
          antialias: true,
          alpha: true,
          powerPreference: 'high-performance',
          depth: true,
        }}
        dpr={[1, 2]}
      >
        <Suspense fallback={null}>
          {viewMode === 'home' ? (
            <>
              {/* Deep Cyber Violet Ambient & Key Lighting */}
              <ambientLight intensity={1.1} color="#1e1035" />
              <directionalLight
                position={[6, 8, 5]}
                intensity={2.4}
                color="#c084fc"
              />
              <directionalLight
                position={[-6, -4, -4]}
                intensity={1.6}
                color="#38bdf8"
              />

              {/* 3D Black & Purple Isometric Core (Reference 3) */}
              <DataCore />
              <FloatingBlocks />
            </>
          ) : (
            <>
              {/* Tactical Red / Crimson & Electric Blue for Active Attack Simulation */}
              <ambientLight intensity={0.9} color="#07101d" />
              <directionalLight
                position={[6, 8, 5]}
                intensity={2.4}
                color={riskScore > 60 ? '#ef4444' : '#168bff'}
              />
              <directionalLight
                position={[-6, -4, -4]}
                intensity={1.6}
                color={riskScore > 60 ? '#f87171' : '#36c7ff'}
              />

              {/* Central Active Cyber Threat Globe */}
              <CyberGlobe
                simulationState={simulationState}
                riskScore={riskScore}
                requestRate={requestRate}
                blockedRequests={blockedRequests}
                successfulRequests={successfulRequests}
                activeClients={activeClients}
              />
            </>
          )}
        </Suspense>
      </Canvas>
    </div>
  );
};
