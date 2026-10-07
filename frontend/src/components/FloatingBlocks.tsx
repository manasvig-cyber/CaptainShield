import React, { useRef, useState, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

interface InteractiveFloatingItemProps {
  id: string;
  position: [number, number, number];
  scale: [number, number, number];
  color: string;
  emissive: string;
  isTransparent?: boolean;
  hoveredId: string | null;
  onHover: (id: string | null) => void;
}

const InteractiveFloatingItem: React.FC<InteractiveFloatingItemProps> = ({
  id,
  position,
  scale,
  color,
  emissive,
  isTransparent = false,
  hoveredId,
  onHover,
}) => {
  const meshRef = useRef<THREE.Mesh>(null);
  const isHovered = hoveredId === id;
  const [clickSpin, setClickSpin] = useState<{ active: boolean; start: number }>({
    active: false,
    start: 0,
  });

  const handleClick = (e: any) => {
    e.stopPropagation();
    setClickSpin({ active: true, start: performance.now() / 1000 });
  };

  useFrame((state) => {
    if (!meshRef.current) return;
    const time = state.clock.getElapsedTime();

    // Hover scale interpolation
    const targetScale = isHovered ? 1.12 : 1.0;
    meshRef.current.scale.lerp(
      new THREE.Vector3(scale[0] * targetScale, scale[1] * targetScale, scale[2] * targetScale),
      0.15
    );

    // Click spin animation
    if (clickSpin.active) {
      const elapsed = time - clickSpin.start;
      if (elapsed < 1.0) {
        const p = elapsed / 1.0;
        meshRef.current.rotation.y = Math.sin(p * Math.PI) * Math.PI * 2;
        meshRef.current.rotation.x = Math.sin(p * Math.PI) * 0.5;
      } else {
        meshRef.current.rotation.set(0, 0, 0);
        setClickSpin({ active: false, start: 0 });
      }
    }
  });

  return (
    <mesh
      ref={meshRef}
      position={position}
      onPointerOver={(e) => {
        e.stopPropagation();
        onHover(id);
      }}
      onPointerOut={(e) => {
        e.stopPropagation();
        onHover(null);
      }}
      onClick={handleClick}
      castShadow
    >
      <boxGeometry args={[1, 1, 1]} />
      <meshStandardMaterial
        color={color}
        emissive={emissive}
        emissiveIntensity={isHovered || clickSpin.active ? 2.5 : 1.2}
        metalness={0.7}
        roughness={0.2}
        transparent={isTransparent}
        opacity={isTransparent ? 0.85 : 1.0}
        depthWrite={!isTransparent}
        side={THREE.FrontSide}
      />
    </mesh>
  );
};

interface FloatingBlocksProps {
  mouseX?: number;
  mouseY?: number;
}

export const FloatingBlocks: React.FC<FloatingBlocksProps> = () => {
  const groupRef = useRef<THREE.Group>(null);
  const floatingCubesRef = useRef<THREE.Group>(null);
  const beamRef = useRef<THREE.Mesh>(null);
  const [hoveredId, setHoveredId] = useState<string | null>(null);

  // Satellite Server Blocks
  const satellites = useMemo(() => [
    { id: 'sat-1', position: [-2.6, -1.8, 1.0] as [number, number, number], scale: [1.1, 1.4, 1.1] as [number, number, number] },
    { id: 'sat-2', position: [2.5, -1.9, 1.6] as [number, number, number], scale: [1.0, 1.3, 1.0] as [number, number, number] },
    { id: 'sat-3', position: [-1.8, -2.0, -2.2] as [number, number, number], scale: [0.95, 1.15, 0.95] as [number, number, number] },
  ], []);

  // Stacked Electric Yellow Data Packets
  const yellowPackets = useMemo(() => [
    { id: 'yp-1', position: [-0.95, -1.62, 1.9] as [number, number, number], scale: [0.6, 0.12, 0.6] as [number, number, number] },
    { id: 'yp-2', position: [-0.95, -1.48, 1.9] as [number, number, number], scale: [0.6, 0.12, 0.6] as [number, number, number] },
    { id: 'yp-3', position: [-0.95, -1.34, 1.9] as [number, number, number], scale: [0.6, 0.12, 0.6] as [number, number, number] },
  ], []);

  // Ambient floating tech cubes
  const floatingCubes = useMemo(() => {
    return Array.from({ length: 12 }).map((_, i) => ({
      id: `ambient-cube-${i}`,
      basePos: [
        (Math.sin(i * 1.5) * 3.2) + (i % 2 === 0 ? 0.8 : -0.8),
        (Math.cos(i * 2.1) * 2.0) + 0.1,
        (Math.sin(i * 3.1) * 2.8),
      ] as [number, number, number],
      size: 0.2 + (i % 3) * 0.08,
      speed: 0.7 + (i % 3) * 0.3,
      phase: i * 0.8,
      isYellow: i % 4 === 0,
      isCyan: i % 4 === 1,
    }));
  }, []);

  useFrame((state) => {
    const time = state.clock.getElapsedTime();

    // Constant slow smooth background orbit ONLY (No mouse drag, no scene tilt)
    if (groupRef.current) {
      groupRef.current.rotation.y = time * 0.06;
    }

    // Volumetric subtle beam breathing
    if (beamRef.current) {
      const mat = beamRef.current.material as THREE.MeshBasicMaterial;
      if (mat) {
        mat.opacity = 0.15 + Math.sin(time * 2.0) * 0.05;
      }
    }

    // Floating cubes motion
    if (floatingCubesRef.current) {
      floatingCubesRef.current.children.forEach((child, idx) => {
        const item = floatingCubes[idx];
        if (item) {
          child.position.y = item.basePos[1] + Math.sin(time * item.speed + item.phase) * 0.25;
          child.rotation.x = time * 0.4 + item.phase;
          child.rotation.y = time * 0.5 + item.phase;
        }
      });
    }
  });

  return (
    <group ref={groupRef}>
      {/* Ground Cyber Platform (Non-occluding) */}
      <mesh position={[0, -2.4, 0]} rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
        <planeGeometry args={[10, 10]} />
        <meshStandardMaterial
          color="#080b12"
          roughness={0.9}
          metalness={0.4}
        />
      </mesh>

      {/* Cyber Grid Traces */}
      <gridHelper
        args={[8, 14, '#7928ca', '#1e1b4b']}
        position={[0, -2.38, 0]}
      />

      {/* Vertical Volumetric Violet Light Column (depthWrite=false prevents black occlusion) */}
      <mesh ref={beamRef} position={[0, 0.4, 0]}>
        <cylinderGeometry args={[0.25, 0.75, 5.5, 16, 1, true]} />
        <meshBasicMaterial
          color="#9333ea"
          transparent
          opacity={0.18}
          side={THREE.DoubleSide}
          depthWrite={false}
          blending={THREE.AdditiveBlending}
        />
      </mesh>

      {/* Satellite Server Blocks */}
      {satellites.map((sat) => (
        <InteractiveFloatingItem
          key={sat.id}
          id={sat.id}
          position={sat.position}
          scale={sat.scale}
          color="#121622"
          emissive="#7928ca"
          hoveredId={hoveredId}
          onHover={setHoveredId}
        />
      ))}

      {/* Stacked Electric Yellow Data Packets */}
      {yellowPackets.map((yp) => (
        <InteractiveFloatingItem
          key={yp.id}
          id={yp.id}
          position={yp.position}
          scale={yp.scale}
          color="#ffd83d"
          emissive="#ffd83d"
          hoveredId={hoveredId}
          onHover={setHoveredId}
        />
      ))}

      {/* Ambient Floating Tech Cubes */}
      <group ref={floatingCubesRef}>
        {floatingCubes.map((item) => {
          const col = item.isYellow ? '#ffd83d' : item.isCyan ? '#36c7ff' : '#c084fc';
          const emissive = item.isYellow ? '#ffd83d' : item.isCyan ? '#168bff' : '#9333ea';
          return (
            <InteractiveFloatingItem
              key={item.id}
              id={item.id}
              position={item.basePos}
              scale={[item.size, item.size, item.size]}
              color={col}
              emissive={emissive}
              isTransparent={!item.isYellow}
              hoveredId={hoveredId}
              onHover={setHoveredId}
            />
          );
        })}
      </group>
    </group>
  );
};
