import React, { useState, useEffect, useRef } from 'react';
import { 
  Search, 
  Activity, 
  Database, 
  Cpu, 
  Radio, 
  X, 
  RefreshCw,
} from 'lucide-react';
import { api } from '../services/api';

interface TopBarProps {
  onSearch?: (query: string) => void;
  redisConnected?: boolean;
  mlLoaded?: boolean;
  trafficActive?: boolean;
  onOpenSimulation?: () => void;
}

export const TopBar: React.FC<TopBarProps> = ({
  onSearch,
  redisConnected = true,
  mlLoaded = true,
  trafficActive = false,
  onOpenSimulation,
}) => {
  const [query, setQuery] = useState('');
  const [isFocused, setIsFocused] = useState(false);
  const [suggestions, setSuggestions] = useState<any[]>([]);
  const [searchResult, setSearchResult] = useState<any | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Load suggestions on mount
  useEffect(() => {
    const fetchSuggestions = async () => {
      try {
        const res = await api.getSearchSuggestions();
        if (res?.suggestions) {
          setSuggestions(res.suggestions);
        }
      } catch (err) {
        // Fallback default suggestions
        setSuggestions([
          { query: '192.168.1.25', type: 'IP Address', desc: 'Simulated worker client IP' },
          { query: '10.0.0.15', type: 'IP Address', desc: 'Secondary client IP' },
          { query: '127.0.0.1', type: 'Localhost', desc: 'Target gateway IP' },
          { query: '429', type: 'HTTP Status', desc: 'Throttled requests' },
        ]);
      }
    };
    fetchSuggestions();
  }, []);

  // Handle outside click to close dropdown
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsFocused(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const executeSearch = async (searchQuery: string) => {
    const targetQuery = searchQuery.trim();
    if (!targetQuery) return;
    setIsLoading(true);
    setQuery(targetQuery);
    setIsFocused(false);
    if (onSearch) onSearch(targetQuery);

    try {
      const res = await api.search(targetQuery);
      setSearchResult(res);
    } catch (err) {
      setSearchResult({
        found: false,
        query: targetQuery,
        message: 'Search query could not be completed. Check backend connectivity.',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      executeSearch(query);
    } else if (e.key === 'Escape') {
      setIsFocused(false);
      setSearchResult(null);
    }
  };

  return (
    <div
      style={{
        minHeight: '56px',
        padding: '8px 20px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        backgroundColor: '#07101d',
        borderBottom: '1px solid var(--border-subtle)',
        zIndex: 30,
        position: 'relative',
        flexWrap: 'wrap',
        gap: '10px',
      }}
    >
      {/* Left: Search Input Box + Suggestions & Result Dropdown */}
      <div ref={dropdownRef} style={{ position: 'relative', flex: '1 1 260px', maxWidth: '380px' }}>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            width: '100%',
            height: '36px',
            padding: '0 12px',
            borderRadius: '10px',
            backgroundColor: isFocused || searchResult ? '#141f30' : '#0e1624',
            border: isFocused || searchResult ? '1px solid #36c7ff' : '1px solid var(--border-subtle)',
            boxShadow: isFocused ? '0 0 12px rgba(54, 199, 255, 0.25)' : 'none',
            transition: 'all 0.2s ease',
          }}
        >
          {isLoading ? (
            <RefreshCw size={14} color="#36c7ff" className="pulse" />
          ) : (
            <Search size={14} color="#8b98aa" />
          )}
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onFocus={() => setIsFocused(true)}
            onKeyDown={handleKeyDown}
            placeholder="Search IP (e.g. 192.168.1.25), session, status..."
            style={{
              background: 'transparent',
              border: 'none',
              color: '#f3f7fa',
              fontFamily: 'var(--font-tech)',
              fontSize: '0.78rem',
              width: '100%',
              outline: 'none',
            }}
          />
          {(query || searchResult) && (
            <button
              onClick={() => {
                setQuery('');
                setSearchResult(null);
              }}
              style={{
                background: 'transparent',
                border: 'none',
                color: '#8b98aa',
                cursor: 'pointer',
                padding: '2px',
              }}
              title="Clear Search"
            >
              <X size={13} />
            </button>
          )}
        </div>

        {/* Suggestions Dropdown on Focus */}
        {isFocused && !searchResult && (
          <div
            style={{
              position: 'absolute',
              top: '42px',
              left: 0,
              width: '100%',
              backgroundColor: '#0a111c',
              border: '1px solid rgba(54, 199, 255, 0.3)',
              borderRadius: '10px',
              padding: '8px',
              boxShadow: '0 10px 30px rgba(0, 0, 0, 0.8)',
              zIndex: 99,
            }}
          >
            <div
              style={{
                fontFamily: 'var(--font-tech)',
                fontSize: '0.64rem',
                color: '#8b98aa',
                padding: '4px 8px',
                fontWeight: 700,
                textTransform: 'uppercase',
                letterSpacing: '0.04em',
              }}
            >
              Suggested Network Queries
            </div>
            {suggestions.map((item, idx) => (
              <div
                key={idx}
                onClick={() => executeSearch(item.query)}
                style={{
                  padding: '7px 10px',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  transition: 'background-color 0.15s ease',
                  backgroundColor: 'transparent',
                }}
                onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = 'rgba(54, 199, 255, 0.1)')}
                onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}
              >
                <div>
                  <span style={{ fontFamily: 'var(--font-display)', fontSize: '0.74rem', color: '#f3f7fa', fontWeight: 600 }}>
                    {item.query}
                  </span>
                  <span style={{ fontFamily: 'var(--font-tech)', fontSize: '0.66rem', color: '#8b98aa', marginLeft: '8px' }}>
                    {item.desc}
                  </span>
                </div>
                <span
                  style={{
                    fontFamily: 'var(--font-tech)',
                    fontSize: '0.60rem',
                    color: '#36c7ff',
                    backgroundColor: 'rgba(54, 199, 255, 0.12)',
                    padding: '2px 6px',
                    borderRadius: '4px',
                  }}
                >
                  {item.type}
                </span>
              </div>
            ))}
          </div>
        )}

        {/* Search Results Card Panel */}
        {searchResult && (
          <div
            style={{
              position: 'absolute',
              top: '42px',
              left: 0,
              width: '420px',
              maxWidth: '90vw',
              backgroundColor: '#0a111c',
              border: searchResult.found ? '1px solid rgba(54, 199, 255, 0.4)' : '1px solid rgba(239, 68, 68, 0.4)',
              borderRadius: '12px',
              padding: '14px',
              boxShadow: '0 15px 40px rgba(0, 0, 0, 0.9)',
              zIndex: 100,
            }}
          >
            {/* Header */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Activity size={15} color={searchResult.found ? '#36c7ff' : '#ffd83d'} />
                <span style={{ fontFamily: 'var(--font-display)', fontSize: '0.76rem', fontWeight: 800, color: '#f3f7fa' }}>
                  {searchResult.matched_type === 'IP_ADDRESS' ? 'NETWORK IP FORENSICS' : 'SEARCH RESULT'}
                </span>
              </div>
              <button
                onClick={() => setSearchResult(null)}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: '#8b98aa',
                  cursor: 'pointer',
                }}
              >
                <X size={14} />
              </button>
            </div>

            {/* Found IP Result Card */}
            {searchResult.found && searchResult.matched_type === 'IP_ADDRESS' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div>
                    <span style={{ fontFamily: 'var(--font-display)', fontSize: '1.05rem', fontWeight: 800, color: '#36c7ff' }}>
                      {searchResult.ip}
                    </span>
                    <span style={{ fontFamily: 'var(--font-tech)', fontSize: '0.68rem', color: '#8b98aa', marginLeft: '6px' }}>
                      ({searchResult.ip_version})
                    </span>
                  </div>
                  <span
                    style={{
                      fontFamily: 'var(--font-tech)',
                      fontSize: '0.68rem',
                      fontWeight: 800,
                      color: searchResult.status_color || '#22d3a2',
                      backgroundColor: 'rgba(255, 255, 255, 0.05)',
                      border: `1px solid ${searchResult.status_color || '#22d3a2'}`,
                      padding: '2px 8px',
                      borderRadius: '4px',
                    }}
                  >
                    {searchResult.security_status}
                  </span>
                </div>

                {/* Metrics Grid */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '8px', backgroundColor: '#07101d', padding: '10px', borderRadius: '8px' }}>
                  <div>
                    <div style={{ fontFamily: 'var(--font-tech)', fontSize: '0.62rem', color: '#8b98aa' }}>REQUESTS</div>
                    <div style={{ fontFamily: 'var(--font-display)', fontSize: '0.90rem', fontWeight: 700, color: '#f3f7fa' }}>
                      {searchResult.total_requests}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontFamily: 'var(--font-tech)', fontSize: '0.62rem', color: '#22d3a2' }}>HTTP 200</div>
                    <div style={{ fontFamily: 'var(--font-display)', fontSize: '0.90rem', fontWeight: 700, color: '#22d3a2' }}>
                      {searchResult.successful_requests}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontFamily: 'var(--font-tech)', fontSize: '0.62rem', color: '#ffd83d' }}>HTTP 429</div>
                    <div style={{ fontFamily: 'var(--font-display)', fontSize: '0.90rem', fontWeight: 700, color: '#ffd83d' }}>
                      {searchResult.blocked_requests}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontFamily: 'var(--font-tech)', fontSize: '0.62rem', color: '#36c7ff' }}>RISK SCORE</div>
                    <div style={{ fontFamily: 'var(--font-display)', fontSize: '0.90rem', fontWeight: 700, color: '#36c7ff' }}>
                      {searchResult.risk_score}
                    </div>
                  </div>
                </div>

                <div style={{ fontFamily: 'var(--font-tech)', fontSize: '0.68rem', color: '#8b98aa', lineHeight: 1.4 }}>
                  <div>
                    <strong>Avg Latency:</strong> {searchResult.avg_latency_ms} ms &bull; <strong>Active in Stream:</strong> {searchResult.is_currently_active ? 'YES (Live Worker)' : 'Historical / Idle'}
                  </div>
                  {searchResult.sessions?.length > 0 && (
                    <div style={{ marginTop: '3px' }}>
                      <strong>Sessions:</strong> {searchResult.sessions.join(', ')}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Found Session Result Card */}
            {searchResult.found && searchResult.matched_type === 'SESSION' && (
              <div style={{ fontFamily: 'var(--font-tech)', fontSize: '0.74rem', color: '#f3f7fa', lineHeight: 1.5 }}>
                <div style={{ fontWeight: 800, color: '#36c7ff', fontSize: '0.85rem' }}>
                  SESSION: {searchResult.session_id}
                </div>
                <div>Preset: {searchResult.preset} &bull; Status: {searchResult.status}</div>
                <div>Total Requests: {searchResult.total_requests} &bull; Blocked: {searchResult.blocked_requests}</div>
                <div>Peak Rate: {searchResult.peak_rate} req/s &bull; Avg Latency: {searchResult.avg_latency_ms} ms</div>
              </div>
            )}

            {/* Found Status Code Result Card */}
            {searchResult.found && searchResult.matched_type === 'STATUS_CODE' && (
              <div style={{ fontFamily: 'var(--font-tech)', fontSize: '0.74rem', color: '#f3f7fa', lineHeight: 1.5 }}>
                <div style={{ fontWeight: 800, color: '#ffd83d', fontSize: '0.85rem' }}>
                  HTTP STATUS {searchResult.status_code}
                </div>
                <div style={{ color: '#8b98aa', marginTop: '2px' }}>{searchResult.meaning}</div>
                <div style={{ marginTop: '4px' }}>
                  Observed: <strong>{searchResult.total_occurrences}</strong> requests across <strong>{searchResult.unique_source_ips}</strong> unique source IPs.
                </div>
              </div>
            )}

            {/* Not Found Result */}
            {!searchResult.found && (
              <div style={{ fontFamily: 'var(--font-tech)', fontSize: '0.72rem', color: '#8b98aa', lineHeight: 1.4 }}>
                <div style={{ color: '#ffd83d', fontWeight: 700, marginBottom: '4px' }}>
                  {searchResult.is_valid_ip ? 'NO TRAFFIC RECORDED' : 'NO MATCH FOUND'}
                </div>
                <div>{searchResult.message}</div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Center Status Indicators */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
        {/* Lab Mode Pill */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '4px 10px',
            borderRadius: '6px',
            backgroundColor: 'rgba(22, 139, 255, 0.12)',
            border: '1px solid rgba(54, 199, 255, 0.3)',
            fontFamily: 'var(--font-tech)',
            fontSize: '0.70rem',
            fontWeight: 700,
            color: '#36c7ff',
            letterSpacing: '0.04em',
          }}
        >
          <Activity size={12} color="#36c7ff" />
          <span>LAB MODE</span>
        </div>

        {/* Redis Indicator */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '4px 10px',
            borderRadius: '6px',
            backgroundColor: redisConnected ? 'rgba(34, 211, 162, 0.12)' : 'rgba(255, 210, 63, 0.12)',
            border: redisConnected ? '1px solid rgba(34, 211, 162, 0.3)' : '1px solid rgba(255, 210, 63, 0.3)',
            fontFamily: 'var(--font-tech)',
            fontSize: '0.70rem',
            fontWeight: 700,
            color: redisConnected ? '#22d3a2' : '#ffd23f',
          }}
          title={redisConnected ? 'Redis Stream & PubSub Connected' : 'In-Memory Stream Active'}
        >
          <Database size={12} />
          <span>REDIS: {redisConnected ? 'ONLINE' : 'ACTIVE'}</span>
        </div>

        {/* ML Status */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '4px 10px',
            borderRadius: '6px',
            backgroundColor: 'rgba(22, 139, 255, 0.12)',
            border: '1px solid rgba(54, 199, 255, 0.3)',
            fontFamily: 'var(--font-tech)',
            fontSize: '0.70rem',
            fontWeight: 700,
            color: '#36c7ff',
          }}
        >
          <Cpu size={12} />
          <span>ML: {mlLoaded ? 'ISOLATION FOREST' : 'INITIALIZING'}</span>
        </div>

        {/* Packet Stream */}
        <div
          onClick={() => {
            if (trafficActive && onOpenSimulation) onOpenSimulation();
          }}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '4px 10px',
            borderRadius: '6px',
            backgroundColor: trafficActive ? 'rgba(255, 69, 74, 0.15)' : 'rgba(90, 140, 190, 0.12)',
            border: trafficActive ? '1px solid rgba(255, 69, 74, 0.5)' : '1px solid var(--border-subtle)',
            fontFamily: 'var(--font-tech)',
            fontSize: '0.70rem',
            fontWeight: 700,
            color: trafficActive ? '#ff454a' : '#8b98aa',
            cursor: trafficActive ? 'pointer' : 'default',
            boxShadow: trafficActive ? '0 0 12px rgba(255, 69, 74, 0.3)' : 'none',
            transition: 'all 0.2s ease',
          }}
          title={trafficActive ? 'Attack Active — Click to view Live SOC Monitoring' : 'Observable on Wireshark Loopback Adapter (Port 5000)'}
        >
          <Radio size={12} color={trafficActive ? '#ff454a' : '#8b98aa'} className={trafficActive ? 'pulse' : ''} />
          <span>PACKET STREAM: {trafficActive ? 'ACTIVE' : 'STOPPED'}</span>
        </div>
      </div>
    </div>
  );
};
