import React, { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

interface CyberGlobeProps {
  simulationState?: 'IDLE' | 'RUNNING' | 'DEFENDING' | 'HIGH_RISK' | 'STOPPING' | 'COMPLETED';
  riskScore?: number;
  requestRate?: number;
  blockedRequests?: number;
  successfulRequests?: number;
  activeClients?: number;
}

export const CyberGlobe: React.FC<CyberGlobeProps> = ({
  simulationState = 'IDLE',
  riskScore = 0.0,
  requestRate = 0,
  blockedRequests = 0,
  successfulRequests: _successfulRequests = 0,
  activeClients: _activeClients = 0,
}) => {
  const globeGroupRef = useRef<THREE.Group>(null);
  const coreMeshRef = useRef<THREE.Mesh>(null);
  const ring1Ref = useRef<THREE.Mesh>(null);
  const ring2Ref = useRef<THREE.Mesh>(null);
  const defenseRingRef = useRef<THREE.Mesh>(null);
  const attackPacketsRef = useRef<THREE.Points>(null);
  const defensePacketsRef = useRef<THREE.Points>(null);
  const boxesGroupRef = useRef<THREE.Group>(null);

  // Determine state transitions: BLUE -> CYAN -> AMBER -> RED ACTIVE THREAT
  const isRunning = simulationState === 'RUNNING' || simulationState === 'DEFENDING' || simulationState === 'HIGH_RISK';
  const isHighRisk = riskScore >= 60 || simulationState === 'HIGH_RISK';
  const isDefending = blockedRequests > 0 || riskScore >= 40;

  // Active attack color palette: Deep Red & Crimson with dark blue base and cyan defense accents
  const primaryThreatColor = isHighRisk ? '#ef4444' : isRunning ? '#ff3344' : '#168bff';
  const secondaryThreatColor = isHighRisk ? '#b91c1c' : isRunning ? '#dc2626' : '#0b3d73';
  const emissiveThreatColor = isHighRisk ? '#ff2233' : isRunning ? '#ef4444' : '#0055aa';
  const defenseColor = '#22d3a2';
  const warningColor = '#ffd83d';

  // 48 Fibonacci sphere surface nodes
  const nodes = useMemo(() => {
    const list: { pos: [number, number, number]; size: number; role: 'threat' | 'defense' | 'warning' | 'normal' }[] = [];
    const count = 48;
    for (let i = 0; i < count; i++) {
      const phi = Math.acos(-1 + (2 * i) / count);
      const theta = Math.sqrt(count * Math.PI) * phi;
      const radius = 2.05;
      const x = radius * Math.cos(theta) * Math.sin(phi);
      const y = radius * Math.sin(theta) * Math.sin(phi);
      const z = radius * Math.cos(phi);

      let role: 'threat' | 'defense' | 'warning' | 'normal' = 'normal';
      if (i % 3 === 0) role = 'threat';
      else if (i % 5 === 0) role = 'defense';
      else if (i % 7 === 0) role = 'warning';

      list.push({
        pos: [x, y, z],
        size: 0.055 + (i % 3) * 0.02,
        role,
      });
    }
    return list;
  }, []);

  // Dynamic Attack Packets: count scales with real request rate (from 60 up to 260)
  const attackPacketCount = useMemo(() => {
    if (!isRunning) return 40;
    return Math.min(260, Math.max(80, Math.floor(requestRate * 4 + 80)));
  }, [isRunning, requestRate]);

  const [attackPositions] = useMemo(() => {
    const pos = new Float32Array(attackPacketCount * 3);
    for (let i = 0; i < attackPacketCount; i++) {
      const angle = (i / attackPacketCount) * Math.PI * 2;
      const r = 2.15 + (i % 5) * 0.12;
      pos[i * 3] = Math.cos(angle) * r;
      pos[i * 3 + 1] = Math.sin(i * 3.7) * 1.35;
      pos[i * 3 + 2] = Math.sin(angle) * r;
    }
    return [pos];
  }, [attackPacketCount]);

  // Defensive Interception Packets (Cyan / Emerald streams circling equator)
  const defensePacketCount = isDefending ? 50 : 15;
  const [defensePositions] = useMemo(() => {
    const pos = new Float32Array(defensePacketCount * 3);
    for (let i = 0; i < defensePacketCount; i++) {
      const angle = (i / defensePacketCount) * Math.PI * 2;
      const r = 2.45 + (i % 3) * 0.08;
      pos[i * 3] = Math.cos(angle) * r;
      pos[i * 3 + 1] = Math.sin(i * 2.2) * 0.45;
      pos[i * 3 + 2] = Math.sin(angle) * r;
    }
    return [pos];
  }, [defensePacketCount]);

  // Floating Cyber Orbit Nodes
  const floatingBoxes = useMemo(() => {
    const items = [
      { label: 'THREAT_VECTOR', isThreat: true },
      { label: 'ADAPTIVE_DEFENSE', isDefense: true },
      { label: 'ISOLATION_FOREST', isThreat: false },
      { label: 'RATE_LIMITER', isDefense: true },
      { label: 'VOLUMETRIC_INGRESS', isThreat: true },
      { label: 'TELEMETRY_STREAM', isWarning: true },
    ];
    return items.map((item, idx) => {
      const angle = (idx / items.length) * Math.PI * 2;
      const dist = 3.2;
      const y = ((idx % 3) - 1) * 0.85;
      return {
        ...item,
        initialPos: [Math.cos(angle) * dist, y, Math.sin(angle) * dist] as [number, number, number],
        speed: 0.15 + (idx % 2) * 0.08,
        size: 0.22,
      };
    });
  }, []);

  useFrame((state) => {
    const time = state.clock.getElapsedTime();
    // Speed up rotation during volumetric attack
    const speedMult = isHighRisk ? 1.8 : isRunning ? 1.2 : 0.6;

    if (globeGroupRef.current) {
      globeGroupRef.current.rotation.y = time * 0.1 * speedMult;
    }

    if (ring1Ref.current) {
      ring1Ref.current.rotation.z = time * 0.15;
      ring1Ref.current.rotation.x = 1.05 + Math.sin(time * 0.4) * 0.08;
    }

    if (ring2Ref.current) {
      ring2Ref.current.rotation.y = -time * 0.18;
      ring2Ref.current.rotation.z = 0.75 + Math.cos(time * 0.3) * 0.08;
    }

    if (defenseRingRef.current) {
      defenseRingRef.current.rotation.y = time * 0.25;
      defenseRingRef.current.rotation.x = -0.35;
    }

    if (attackPacketsRef.current) {
      attackPacketsRef.current.rotation.y = time * 0.4 * speedMult;
      attackPacketsRef.current.rotation.x = time * 0.12;
    }

    if (defensePacketsRef.current) {
      defensePacketsRef.current.rotation.y = -time * 0.3;
      defensePacketsRef.current.rotation.z = time * 0.08;
    }

    if (boxesGroupRef.current) {
      boxesGroupRef.current.children.forEach((child, i) => {
        const item = floatingBoxes[i];
        if (item) {
          const orbitAngle = time * item.speed + (i * Math.PI) / 3.0;
          const dist = 3.1 + Math.sin(time + i) * 0.15;
          child.position.x = Math.cos(orbitAngle) * dist;
          child.position.z = Math.sin(orbitAngle) * dist;
          child.position.y = item.initialPos[1] + Math.sin(time * 1.4 + i) * 0.1;
          child.rotation.x = time * 0.5 + i;
          child.rotation.y = time * 0.6 + i;
        }
      });
    }
  });

  return (
    <group position={[0, 0, 0]}>
      {/* Central 3D Cyber Threat Globe */}
      <group ref={globeGroupRef}>
        {/* Core Sphere (Dark Navy base with red inner glow during attack) */}
        <mesh ref={coreMeshRef}>
          <sphereGeometry args={[1.98, 36, 36]} />
          <meshStandardMaterial
            color="#060a12"
            roughness={0.7}
            metalness={0.8}
            emissive={emissiveThreatColor}
            emissiveIntensity={isRunning ? (isHighRisk ? 0.9 : 0.5) : 0.1}
          />
        </mesh>

        {/* Primary Tactical Wireframe (Deep Red Crimson in Attack, Cyber Blue in Calm) */}
        <mesh>
          <sphereGeometry args={[2.01, 28, 24]} />
          <meshBasicMaterial
            color={isRunning ? primaryThreatColor : '#168bff'}
            wireframe
            transparent
            opacity={isRunning ? 0.65 : 0.35}
            depthWrite={false}
          />
        </mesh>

        {/* Latitude / Longitude Accent Grid */}
        <mesh>
          <sphereGeometry args={[2.03, 14, 12]} />
          <meshBasicMaterial
            color={isRunning ? secondaryThreatColor : '#36c7ff'}
            wireframe
            transparent
            opacity={isRunning ? 0.45 : 0.2}
            depthWrite={false}
          />
        </mesh>

        {/* Glowing Network Threat / Defense Nodes */}
        {nodes.map((node, i) => {
          let nodeColor = primaryThreatColor;
          let nodeEmissive = emissiveThreatColor;

          if (node.role === 'threat') {
            nodeColor = isRunning ? '#ff2e34' : '#168bff';
            nodeEmissive = isRunning ? '#ff0022' : '#0066cc';
          } else if (node.role === 'defense') {
            nodeColor = defenseColor;
            nodeEmissive = '#10b981';
          } else if (node.role === 'warning') {
            nodeColor = warningColor;
            nodeEmissive = '#d97706';
          }

          return (
            <mesh key={i} position={node.pos}>
              <sphereGeometry args={[node.size, 8, 8]} />
              <meshStandardMaterial
                color={nodeColor}
                emissive={nodeEmissive}
                emissiveIntensity={isRunning ? 2.6 : 1.2}
                roughness={0.2}
              />
            </mesh>
          );
        })}
      </group>

      {/* Orbiting Tech Ring 1 (Crimson Threat Track) */}
      <mesh ref={ring1Ref}>
        <ringGeometry args={[2.55, 2.6, 64]} />
        <meshBasicMaterial
          color={isRunning ? '#ff3344' : '#36c7ff'}
          side={THREE.DoubleSide}
          transparent
          opacity={isRunning ? 0.55 : 0.25}
          depthWrite={false}
        />
      </mesh>

      {/* Orbiting Tech Ring 2 (Outer Defense Ring) */}
      <mesh ref={ring2Ref}>
        <ringGeometry args={[2.85, 2.88, 64]} />
        <meshBasicMaterial
          color={isDefending ? '#22d3a2' : '#168bff'}
          side={THREE.DoubleSide}
          transparent
          opacity={isDefending ? 0.45 : 0.2}
          depthWrite={false}
        />
      </mesh>

      {/* Equatorial Interception Shield Ring */}
      <mesh ref={defenseRingRef}>
        <ringGeometry args={[2.35, 2.38, 64]} />
        <meshBasicMaterial
          color={isDefending ? '#22d3a2' : '#38bdf8'}
          side={THREE.DoubleSide}
          transparent
          opacity={isDefending ? 0.6 : 0.15}
          depthWrite={false}
        />
      </mesh>

      {/* Flowing Attack Packets (Red Crimson) */}
      <points ref={attackPacketsRef}>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            args={[attackPositions, 3]}
          />
        </bufferGeometry>
        <pointsMaterial
          size={0.075}
          color={isRunning ? '#ff2e34' : '#36c7ff'}
          transparent
          opacity={0.85}
          blending={THREE.AdditiveBlending}
          depthWrite={false}
        />
      </points>

      {/* Flowing Defense Interception Packets (Cyan / Emerald) */}
      <points ref={defensePacketsRef}>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            args={[defensePositions, 3]}
          />
        </bufferGeometry>
        <pointsMaterial
          size={0.07}
          color={isDefending ? '#22d3a2' : '#38bdf8'}
          transparent
          opacity={0.8}
          blending={THREE.AdditiveBlending}
          depthWrite={false}
        />
      </points>

      {/* Orbiting Satellite Security Nodes */}
      <group ref={boxesGroupRef}>
        {floatingBoxes.map((box, i) => {
          const boxColor = box.isThreat
            ? (isRunning ? '#ff3344' : '#168bff')
            : box.isDefense
            ? defenseColor
            : warningColor;

          return (
            <mesh key={i} position={box.initialPos}>
              <boxGeometry args={[box.size, box.size, box.size]} />
              <meshStandardMaterial
                color={boxColor}
                emissive={boxColor}
                emissiveIntensity={isRunning ? 2.2 : 1.0}
                metalness={0.8}
                roughness={0.2}
              />
            </mesh>
          );
        })}
      </group>
    </group>
  );
};
