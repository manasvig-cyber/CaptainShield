import { useEffect, useState, useRef } from 'react';

export interface MouseParallaxState {
  x: number;          // -1 to 1 normalized
  y: number;          // -1 to 1 normalized
  targetX: number;
  targetY: number;
  rotateX: number;    // degrees for 3D container tilt (±4 deg)
  rotateY: number;    // degrees for 3D container tilt (±5 deg)
}

export function useMouseParallax(lerpFactor = 0.08) {
  const [coords, setCoords] = useState<MouseParallaxState>({
    x: 0,
    y: 0,
    targetX: 0,
    targetY: 0,
    rotateX: 0,
    rotateY: 0,
  });

  const stateRef = useRef({
    currentX: 0,
    currentY: 0,
    targetX: 0,
    targetY: 0,
  });

  const reqIdRef = useRef<number | null>(null);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      const { innerWidth, innerHeight } = window;
      // Normalize from -1 (left/top) to +1 (right/bottom)
      const nx = (e.clientX / innerWidth) * 2 - 1;
      const ny = (e.clientY / innerHeight) * 2 - 1;

      stateRef.current.targetX = Math.max(-1, Math.min(1, nx));
      stateRef.current.targetY = Math.max(-1, Math.min(1, ny));
    };

    const handleMouseLeave = () => {
      stateRef.current.targetX = 0;
      stateRef.current.targetY = 0;
    };

    window.addEventListener('mousemove', handleMouseMove, { passive: true });
    document.addEventListener('mouseleave', handleMouseLeave);

    const animate = () => {
      const state = stateRef.current;
      // Smooth lerp interpolation
      state.currentX += (state.targetX - state.currentX) * lerpFactor;
      state.currentY += (state.targetY - state.currentY) * lerpFactor;

      // Tilts:
      // Mouse down -> tilts downward (rotateX negative/positive according to perspective)
      // Cursor left -> panel rotates slightly left (rotateY negative)
      // Cursor right -> panel rotates slightly right (rotateY positive)
      const rotX = -state.currentY * 3.8;  // max ~±3.8 deg
      const rotY = state.currentX * 4.8;   // max ~±4.8 deg

      setCoords({
        x: state.currentX,
        y: state.currentY,
        targetX: state.targetX,
        targetY: state.targetY,
        rotateX: rotX,
        rotateY: rotY,
      });

      reqIdRef.current = requestAnimationFrame(animate);
    };

    reqIdRef.current = requestAnimationFrame(animate);

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseleave', handleMouseLeave);
      if (reqIdRef.current) cancelAnimationFrame(reqIdRef.current);
    };
  }, [lerpFactor]);

  return coords;
}
