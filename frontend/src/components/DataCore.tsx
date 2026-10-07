import React, { useRef, useState, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

// Individual interactive 3D box component
interface InteractiveVoxelProps {
  id: string;
  position: [number, number, number];
  scale: [number, number, number];
  type: 'frame' | 'glow' | 'accent' | 'crystal' | 'cyan';
  hoveredId: string | null;
  selectedId: string | null;
  onHover: (id: string | null) => void;
  onSelect: (id: string) => void;
}

const InteractiveVoxel: React.FC<InteractiveVoxelProps> = ({
  id,
  position,
  scale,
  type,
  hoveredId,
  selectedId,
  onHover,
  onSelect,
}) => {
  const meshRef = useRef<THREE.Mesh>(null);
  const isHovered = hoveredId === id;
  const isSelected = selectedId === id;
  
  // Animation state for individual box
  const [clickAnim, setClickAnim] = useState<{ active: boolean; startTime: number }>({
    active: false,
    startTime: 0,
  });

  // Trigger click animation
  const handleClick = (e: any) => {
    e.stopPropagation();
    onSelect(id);
    setClickAnim({ active: true, startTime: performance.now() / 1000 });
  };

  useFrame((state) => {
    if (!meshRef.current) return;
    const time = state.clock.getElapsedTime();

    // 1. Hover & selection subtle scale & glow interpolation
    const targetScale = isHovered || isSelected ? 1.08 : 1.0;
    meshRef.current.scale.lerp(
      new THREE.Vector3(scale[0] * targetScale, scale[1] * targetScale, scale[2] * targetScale),
      0.15
    );

    // 2. Click 360-degree rotation animation
    if (clickAnim.active) {
      const elapsed = time - clickAnim.startTime;
      const duration = 1.0;
      if (elapsed < duration) {
        const progress = elapsed / duration;
        // Smooth sine ease-out spin
        meshRef.current.rotation.y = Math.sin(progress * Math.PI) * Math.PI * 2;
        meshRef.current.rotation.x = Math.sin(progress * Math.PI) * 0.4;
      } else {
        meshRef.current.rotation.set(0, 0, 0);
        setClickAnim({ active: false, startTime: 0 });
      }
    } else if (isHovered) {
      // Subtle gentle oscillation on hover
      meshRef.current.rotation.y = THREE.MathUtils.lerp(meshRef.current.rotation.y, 0.15, 0.1);
      meshRef.current.rotation.x = THREE.MathUtils.lerp(meshRef.current.rotation.x, 0.1, 0.1);
    } else {
      meshRef.current.rotation.y = THREE.MathUtils.lerp(meshRef.current.rotation.y, 0, 0.1);
      meshRef.current.rotation.x = THREE.MathUtils.lerp(meshRef.current.rotation.x, 0, 0.1);
    }
  });

  // Base materials with STRICT depth settings to prevent any black occlusions or z-fighting
  if (type === 'frame') {
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
        receiveShadow
      >
        <boxGeometry args={[1, 1, 1]} />
        <meshStandardMaterial
          color={isHovered ? '#2a324b' : '#141824'}
          metalness={0.9}
          roughness={0.2}
          emissive={isHovered ? '#7928ca' : '#000000'}
          emissiveIntensity={isHovered ? 0.4 : 0}
        />
      </mesh>
    );
  }

  if (type === 'accent') {
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
      >
        <boxGeometry args={[1, 1, 1]} />
        <meshStandardMaterial
          color="#ffd83d"
          emissive="#ffd83d"
          emissiveIntensity={isHovered || clickAnim.active ? 3.0 : 1.8}
          roughness={0.15}
          metalness={0.2}
        />
      </mesh>
    );
  }

  if (type === 'cyan') {
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
      >
        <boxGeometry args={[1, 1, 1]} />
        <meshStandardMaterial
          color="#36c7ff"
          emissive="#168bff"
          emissiveIntensity={isHovered || clickAnim.active ? 2.8 : 1.6}
          roughness={0.1}
          metalness={0.3}
          transparent
          opacity={0.88}
          depthWrite={false}
        />
      </mesh>
    );
  }

  if (type === 'crystal') {
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
      >
        <boxGeometry args={[1, 1, 1]} />
        <meshStandardMaterial
          color="#c084fc"
          emissive="#9333ea"
          emissiveIntensity={isHovered || clickAnim.active ? 2.4 : 1.2}
          roughness={0.08}
          metalness={0.1}
          transparent
          opacity={0.82}
          depthWrite={false}
          side={THREE.FrontSide}
        />
      </mesh>
    );
  }

  // Default 'glow' violet box
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
    >
      <boxGeometry args={[1, 1, 1]} />
      <meshStandardMaterial
        color="#a855f7"
        emissive="#7928ca"
        emissiveIntensity={isHovered || clickAnim.active ? 2.6 : 1.5}
        roughness={0.12}
        metalness={0.15}
        transparent
        opacity={0.86}
        depthWrite={false}
        side={THREE.FrontSide}
      />
    </mesh>
  );
};

interface DataCoreProps {
  mouseX?: number;
  mouseY?: number;
}

export const DataCore: React.FC<DataCoreProps> = () => {
  const groupRef = useRef<THREE.Group>(null);
  const coreRef = useRef<THREE.Group>(null);
  const [hoveredObjectId, setHoveredObjectId] = useState<string | null>(null);
  const [selectedObjectId, setSelectedObjectId] = useState<string | null>(null);

  // Pre-generate voxel coordinates with non-overlapping positions to eliminate z-fighting
  const voxels = useMemo(() => {
    const list: {
      id: string;
      position: [number, number, number];
      scale: [number, number, number];
      type: 'frame' | 'glow' | 'accent' | 'crystal' | 'cyan';
    }[] = [];

    // Outer corner pillars (dark metallic cyber frame)
    const halfW = 1.35;
    let idx = 0;

    for (let y = -1.8; y <= 2.0; y += 0.45) {
      list.push({ id: `frame-c1-${idx++}`, position: [-halfW, y, -halfW], scale: [0.3, 0.38, 0.3], type: 'frame' });
      list.push({ id: `frame-c2-${idx++}`, position: [halfW, y, -halfW], scale: [0.3, 0.38, 0.3], type: 'frame' });
      list.push({ id: `frame-c3-${idx++}`, position: [-halfW, y, halfW], scale: [0.3, 0.38, 0.3], type: 'frame' });
      list.push({ id: `frame-c4-${idx++}`, position: [halfW, y, halfW], scale: [0.3, 0.38, 0.3], type: 'frame' });

      // Horizontal support braces
      if (Math.abs(y % 0.9) < 0.2) {
        list.push({ id: `strut-f1-${idx++}`, position: [0, y, -halfW], scale: [2.2, 0.12, 0.16], type: 'frame' });
        list.push({ id: `strut-f2-${idx++}`, position: [0, y, halfW], scale: [2.2, 0.12, 0.16], type: 'frame' });
        list.push({ id: `strut-s1-${idx++}`, position: [-halfW, y, 0], scale: [0.16, 0.12, 2.2], type: 'frame' });
        list.push({ id: `strut-s2-${idx++}`, position: [halfW, y, 0], scale: [0.16, 0.12, 2.2], type: 'frame' });
      }
    }

    // Top cap & Bottom pedestal
    list.push({ id: `cap-top`, position: [0, 2.28, 0], scale: [2.95, 0.22, 2.95], type: 'frame' });
    list.push({ id: `base-bot`, position: [0, -2.1, 0], scale: [3.15, 0.28, 3.15], type: 'frame' });

    // Inner glowing translucent cubic voxels (independent floating data blocks)
    const gridSize = 3;
    const step = 0.62;
    const offset = (gridSize - 1) * step * 0.5;

    for (let x = 0; x < gridSize; x++) {
      for (let y = 0; y < 5; y++) {
        for (let z = 0; z < gridSize; z++) {
          const seed = Math.sin(x * 12.9898 + y * 78.233 + z * 37.719);
          if (seed > -0.3) {
            let vType: 'glow' | 'accent' | 'crystal' | 'cyan' = 'glow';
            if (seed > 0.55) vType = 'accent';
            else if (seed > 0.2) vType = 'crystal';
            else if (seed < -0.1) vType = 'cyan';

            list.push({
              id: `voxel-${x}-${y}-${z}`,
              position: [
                x * step - offset,
                y * 0.65 - 1.3,
                z * step - offset,
              ],
              scale: [0.48, 0.48, 0.48],
              type: vType,
            });
          }
        }
      }
    }

    return list;
  }, []);

  // Frame animation: Constant smooth majestic rotation ONLY (No dragging, no camera jumping, no mouse distortion)
  useFrame((state) => {
    const time = state.clock.getElapsedTime();

    if (groupRef.current) {
      // Gentle, constant, majestic ambient idle spin
      groupRef.current.rotation.y = time * 0.14;
      // Fixed isometric tilt for ideal perspective (no mouse drag)
      groupRef.current.rotation.x = 0.22;
      // Subtle vertical floating breath
      groupRef.current.position.y = 0.2 + Math.sin(time * 1.2) * 0.05;
    }
  });

  return (
    <group ref={groupRef} position={[0.2, 0.2, 0]}>
      {/* Central Pulsing Point Lights for ambient internal illumination */}
      <pointLight
        color="#c084fc"
        intensity={3.5}
        distance={8}
        decay={2}
        position={[0, 0, 0]}
      />
      <pointLight
        color="#ffd83d"
        intensity={2.2}
        distance={6}
        decay={2}
        position={[1.8, -1.0, 1.2]}
      />
      <pointLight
        color="#36c7ff"
        intensity={2.0}
        distance={6}
        decay={2}
        position={[-1.8, 1.0, -1.2]}
      />

      {/* Main Core Voxel Elements */}
      <group ref={coreRef}>
        {voxels.map((v) => (
          <InteractiveVoxel
            key={v.id}
            id={v.id}
            position={v.position}
            scale={v.scale}
            type={v.type}
            hoveredId={hoveredObjectId}
            selectedId={selectedObjectId}
            onHover={setHoveredObjectId}
            onSelect={setSelectedObjectId}
          />
        ))}
      </group>

      {/* Central Holographic Octahedron Core */}
      <mesh position={[0, 0, 0]}>
        <octahedronGeometry args={[0.75, 0]} />
        <meshBasicMaterial
          color="#e879f9"
          wireframe
          transparent
          opacity={0.55}
          depthWrite={false}
        />
      </mesh>
    </group>
  );
};
