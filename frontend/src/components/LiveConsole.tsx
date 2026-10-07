import React, { useRef, useEffect } from 'react';
import { Terminal, Trash2 } from 'lucide-react';

export interface ConsoleEvent {
  timestamp?: number;
  type?: string;
  message?: string;
  level?: 'INFO' | 'WARNING' | 'DANGER' | string;
}

interface LiveConsoleProps {
  events: ConsoleEvent[];
  onClear?: () => void;
}

export const LiveConsole: React.FC<LiveConsoleProps> = ({ events, onClear }) => {
  const logContainerRef = useRef<HTMLDivElement>(null);
  const [isPaused, setIsPaused] = React.useState(false);
  const isUserScrolledUp = useRef(false);

  // Track if user manually scrolled up
  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const { scrollTop, scrollHeight, clientHeight } = e.currentTarget;
    // If distance from bottom is greater than 20px, user intentionally scrolled up
    const scrolledUp = (scrollHeight - scrollTop - clientHeight) > 20;
    isUserScrolledUp.current = scrolledUp;
    setIsPaused(scrolledUp);
  };

  // Only auto-scroll the INTERNAL container if user hasn't scrolled up
  useEffect(() => {
    if (logContainerRef.current && !isUserScrolledUp.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [events]);

  const resumeScroll = () => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
      isUserScrolledUp.current = false;
      setIsPaused(false);
    }
  };

  const formatTime = (ts?: number) => {
    if (!ts) return new Date().toLocaleTimeString();
    return new Date(ts * 1000).toLocaleTimeString();
  };

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '155px',
        backgroundColor: '#07101d',
        borderRadius: '12px',
        border: '1px solid var(--border-subtle)',
        padding: '8px 12px',
        overflow: 'hidden',
      }}
    >
      {/* Console Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          paddingBottom: '6px',
          borderBottom: '1px solid rgba(90, 140, 190, 0.1)',
          marginBottom: '6px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Terminal size={13} color="#36c7ff" />
          <span
            style={{
              fontFamily: 'var(--font-display)',
              fontSize: '0.68rem',
              fontWeight: 700,
              color: '#f3f7fa',
              letterSpacing: '0.04em',
            }}
          >
            LIVE SOC EVENT CONSOLE (REDIS STREAM)
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {isPaused && (
            <button
              onClick={resumeScroll}
              style={{
                background: 'rgba(255, 210, 63, 0.15)',
                border: '1px solid rgba(255, 210, 63, 0.4)',
                color: '#ffd23f',
                padding: '1px 7px',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '0.62rem',
                fontFamily: 'var(--font-tech)',
                fontWeight: 600,
              }}
              title="Click to resume auto-scrolling"
            >
              &darr; Auto-scroll paused (Resume)
            </button>
          )}
          {onClear && (
            <button
              onClick={onClear}
              style={{
                background: 'transparent',
                border: 'none',
                color: '#8b98aa',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                fontSize: '0.66rem',
                fontFamily: 'var(--font-tech)',
              }}
              title="Clear Event Log"
            >
              <Trash2 size={11} />
              <span>Clear</span>
            </button>
          )}
        </div>
      </div>

      {/* Internal Log Stream Container (isolated scroll) */}
      <div
        ref={logContainerRef}
        onScroll={handleScroll}
        style={{
          flex: 1,
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column',
          gap: '4px',
          fontFamily: 'Consolas, monospace',
          fontSize: '0.72rem',
        }}
      >
        {events.length === 0 ? (
          <div style={{ color: '#566477', fontStyle: 'italic', padding: '4px 0' }}>
            [STREAM STANDBY] Awaiting live telemetry & Redis events...
          </div>
        ) : (
          events.map((ev, i) => {
            const isDanger = ev.level === 'DANGER';
            const isWarn = ev.level === 'WARNING';
            const color = isDanger ? '#ff454a' : isWarn ? '#ffd23f' : '#8b98aa';
            const badgeBg = isDanger ? 'rgba(255, 69, 74, 0.15)' : isWarn ? 'rgba(255, 210, 63, 0.15)' : 'rgba(54, 199, 255, 0.1)';
            const badgeColor = isDanger ? '#ff454a' : isWarn ? '#ffd23f' : '#36c7ff';

            return (
              <div key={i} style={{ display: 'flex', alignItems: 'baseline', gap: '8px', lineHeight: 1.3 }}>
                <span style={{ color: '#566477', fontSize: '0.66rem' }}>[{formatTime(ev.timestamp)}]</span>
                <span
                  style={{
                    backgroundColor: badgeBg,
                    color: badgeColor,
                    padding: '1px 5px',
                    borderRadius: '3px',
                    fontSize: '0.62rem',
                    fontWeight: 700,
                  }}
                >
                  {ev.type || 'SYSTEM'}
                </span>
                <span style={{ color }}>{ev.message}</span>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
