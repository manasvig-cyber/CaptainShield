import React from 'react';
import {
  Home,
  Shield,
  Clock,
  Settings,
  HelpCircle,
  Hexagon,
  Radio,
} from 'lucide-react';

interface SidebarProps {
  activeTab?: string;
  onSelectTab?: (tab: string) => void;
  ingressMbps?: number;
  mitigationMbps?: number;
  isSimulating?: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab = 'home',
  onSelectTab,
  ingressMbps = 94.74,
  mitigationMbps = 95.42,
  isSimulating = false,
}) => {
  const navItems = [
    { id: 'home', label: 'Home', icon: <Home size={17} /> },
    ...(isSimulating || activeTab === 'simulation'
      ? [{ id: 'simulation', label: 'Live Attack', icon: <Radio size={17} color="#ff454a" className="pulse" />, isLive: true }]
      : []),
    { id: 'matrix', label: 'Threat Matrix', icon: <Shield size={17} /> },
    { id: 'recent', label: 'Recent', icon: <Clock size={17} /> },
  ];

  const bottomNavItems = [
    { id: 'settings', label: 'Settings', icon: <Settings size={17} /> },
    { id: 'help', label: 'Wireshark Lab', icon: <HelpCircle size={17} /> },
  ];

  return (
    <div
      style={{
        width: '185px',
        height: '100%',
        backgroundColor: '#07101d',
        borderRight: '1px solid var(--border-subtle)',
        display: 'flex',
        flexDirection: 'column',
        padding: '24px 14px 20px 18px',
        zIndex: 25,
      }}
    >
      {/* Brand Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '32px' }}>
        <div
          style={{
            width: '28px',
            height: '28px',
            borderRadius: '6px',
            backgroundColor: 'rgba(22, 139, 255, 0.12)',
            border: '1px solid rgba(54, 199, 255, 0.35)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <Hexagon size={16} color="#36c7ff" />
        </div>
        <div>
          <div
            style={{
              fontFamily: 'var(--font-display)',
              fontSize: '0.84rem',
              fontWeight: 800,
              letterSpacing: '0.06em',
              color: '#f3f7fa',
              lineHeight: 1,
            }}
          >
            CaptainShield
          </div>
        </div>
      </div>

      {/* Main Navigation Items */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
        {navItems.map((item) => {
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSelectTab && onSelectTab(item.id)}
              style={{
                position: 'relative',
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                padding: '10px 12px',
                borderRadius: '10px',
                border: 'none',
                background: isActive ? 'rgba(22, 139, 255, 0.14)' : 'transparent',
                color: isActive ? '#f3f7fa' : '#8b98aa',
                fontFamily: 'var(--font-tech)',
                fontSize: '0.80rem',
                fontWeight: isActive ? 600 : 500,
                cursor: 'pointer',
                transition: 'all 0.18s ease',
                textAlign: 'left',
                width: '100%',
                outline: 'none',
              }}
              onMouseEnter={(e) => {
                if (!isActive) e.currentTarget.style.color = '#f3f7fa';
              }}
              onMouseLeave={(e) => {
                if (!isActive) e.currentTarget.style.color = '#8b98aa';
              }}
            >
              <span style={{ color: (item as any).isLive ? '#ff454a' : isActive ? '#36c7ff' : 'inherit' }}>
                {item.icon}
              </span>
              <span style={{ color: (item as any).isLive ? '#ff6b6b' : 'inherit' }}>{item.label}</span>
              {(item as any).isLive && (
                <span
                  style={{
                    marginLeft: 'auto',
                    backgroundColor: 'rgba(239, 68, 68, 0.2)',
                    color: '#ff454a',
                    border: '1px solid rgba(239, 68, 68, 0.6)',
                    fontSize: '0.58rem',
                    fontWeight: 800,
                    padding: '2px 5px',
                    borderRadius: '4px',
                    letterSpacing: '0.04em',
                  }}
                >
                  LIVE
                </span>
              )}
              {isActive && (
                <div
                  style={{
                    position: 'absolute',
                    right: '-14px',
                    width: '3px',
                    height: '18px',
                    backgroundColor: '#36c7ff',
                    borderRadius: '2px 0 0 2px',
                    boxShadow: '0 0 10px #36c7ff',
                  }}
                />
              )}
            </button>
          );
        })}
      </div>

      {/* Secondary Bottom Navigation */}
      <div
        style={{
          marginTop: '28px',
          display: 'flex',
          flexDirection: 'column',
          gap: '6px',
        }}
      >
        {bottomNavItems.map((item) => {
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSelectTab && onSelectTab(item.id)}
              style={{
                position: 'relative',
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                padding: '8px 12px',
                borderRadius: '10px',
                border: 'none',
                background: isActive ? 'rgba(22, 139, 255, 0.14)' : 'transparent',
                color: isActive ? '#f3f7fa' : '#8b98aa',
                fontFamily: 'var(--font-tech)',
                fontSize: '0.80rem',
                fontWeight: isActive ? 600 : 500,
                cursor: 'pointer',
                transition: 'all 0.18s ease',
                textAlign: 'left',
                width: '100%',
                outline: 'none',
              }}
            >
              <span style={{ color: isActive ? '#36c7ff' : 'inherit' }}>
                {item.icon}
              </span>
              <span>{item.label}</span>
            </button>
          );
        })}
      </div>

      {/* Bottom Network Bandwidth Sparklines */}
      <div
        style={{
          marginTop: 'auto',
          paddingTop: '16px',
          display: 'flex',
          flexDirection: 'column',
          gap: '14px',
          borderTop: '1px solid var(--border-subtle)',
        }}
      >
        {/* Ingress */}
        <div>
          <svg width="100%" height="16" viewBox="0 0 100 16" fill="none">
            <path
              d="M0 8 Q 25 0, 50 8 T 100 8"
              stroke="#36c7ff"
              strokeWidth="2"
              fill="none"
              strokeLinecap="round"
            />
          </svg>
          <div style={{ marginTop: '2px' }}>
            <span
              style={{
                fontFamily: 'var(--font-tech)',
                fontSize: '0.64rem',
                color: '#8b98aa',
                display: 'block',
              }}
            >
              Upload
            </span>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '3px' }}>
              <span
                style={{
                  fontFamily: 'var(--font-tech)',
                  fontSize: '0.86rem',
                  fontWeight: 700,
                  color: '#f3f7fa',
                }}
              >
                {ingressMbps.toFixed(2)}
              </span>
              <span
                style={{
                  fontFamily: 'var(--font-tech)',
                  fontSize: '0.62rem',
                  color: '#8b98aa',
                }}
              >
                Mbps
              </span>
            </div>
          </div>
        </div>

        {/* Download / Mitigation */}
        <div>
          <svg width="100%" height="16" viewBox="0 0 100 16" fill="none">
            <path
              d="M0 8 Q 25 16, 50 8 T 100 8"
              stroke="#22d3a2"
              strokeWidth="2"
              fill="none"
              strokeLinecap="round"
            />
          </svg>
          <div style={{ marginTop: '2px' }}>
            <span
              style={{
                fontFamily: 'var(--font-tech)',
                fontSize: '0.64rem',
                color: '#8b98aa',
                display: 'block',
              }}
            >
              Download
            </span>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '3px' }}>
              <span
                style={{
                  fontFamily: 'var(--font-tech)',
                  fontSize: '0.86rem',
                  fontWeight: 700,
                  color: '#f3f7fa',
                }}
              >
                {mitigationMbps.toFixed(2)}
              </span>
              <span
                style={{
                  fontFamily: 'var(--font-tech)',
                  fontSize: '0.62rem',
                  color: '#8b98aa',
                }}
              >
                Mbps
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
