import React, { useEffect, useState } from 'react';

interface CircularProgressProps {
  percentage?: number; // 0 to 100 (default 75% for 375 of 500)
  value?: string;      // e.g. "375 GB" or "375 MB/s"
  subtext?: string;    // e.g. "of 500 GB" or "of 500 MB/s"
  size?: number;
  strokeWidth?: number;
}

export const CircularProgress: React.FC<CircularProgressProps> = ({
  percentage = 75,
  value = "375 GB",
  subtext = "of 500 GB",
  size = 175,
  strokeWidth = 10,
}) => {
  const [animatedPercent, setAnimatedPercent] = useState(0);

  useEffect(() => {
    const timer = setTimeout(() => {
      setAnimatedPercent(percentage);
    }, 250);
    return () => clearTimeout(timer);
  }, [percentage]);

  const radius = (size - strokeWidth * 2) / 2;
  const circumference = 2 * Math.PI * radius;
  // Arc spans ~260 degrees like the reference image
  const arcLength = circumference * 0.72;
  const strokeDashoffset = arcLength - (arcLength * (animatedPercent / 100));

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        position: 'relative',
        width: size,
        height: size,
        margin: '0 auto',
      }}
    >
      <svg
        width={size}
        height={size}
        style={{
          transform: 'rotate(140deg)',
          overflow: 'visible',
        }}
      >
        {/* Background Track Ring */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="#1e2230"
          strokeWidth={strokeWidth}
          strokeDasharray={`${arcLength} ${circumference}`}
          strokeLinecap="round"
        />

        {/* Foreground Electric Yellow Active Arc */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="#ffd83d"
          strokeWidth={strokeWidth}
          strokeDasharray={`${arcLength} ${circumference}`}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          style={{
            transition: 'stroke-dashoffset 1.4s cubic-bezier(0.16, 1, 0.3, 1)',
            filter: 'drop-shadow(0 0 10px rgba(255, 216, 61, 0.45))',
          }}
        />
      </svg>

      {/* Center Label Values */}
      <div
        style={{
          position: 'absolute',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          pointerEvents: 'none',
          textAlign: 'center',
        }}
      >
        <span
          style={{
            fontFamily: 'var(--font-display)',
            fontSize: '1.45rem',
            fontWeight: 800,
            color: '#f4f4f4',
            letterSpacing: '0.04em',
          }}
        >
          {value}
        </span>
        <span
          style={{
            fontFamily: 'var(--font-tech)',
            fontSize: '0.72rem',
            color: '#6f717a',
            marginTop: '2px',
            fontWeight: 500,
          }}
        >
          {subtext}
        </span>
      </div>
    </div>
  );
};
