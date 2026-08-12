import { useState, useEffect, useRef, useCallback } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polygon, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { useArkanaChat } from '../hooks/useArkanaChat';

// ── Fix default leaflet marker icon URLs for Vite ──────────────────────────
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

// ── Custom heritage pin SVG ─────────────────────────────────────────────────
function makeIcon(color = '#8b6914', size = 28) {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 44" width="${size}" height="${size * 1.375}">
    <defs>
      <filter id="ds"><feDropShadow dx="0" dy="2" stdDeviation="2" flood-color="${color}" flood-opacity="0.45"/></filter>
    </defs>
    <path d="M16 1C8.82 1 3 6.82 3 14c0 9.5 13 29 13 29S29 23.5 29 14C29 6.82 23.18 1 16 1z"
      fill="${color}" filter="url(#ds)"/>
    <circle cx="16" cy="14" r="6.5" fill="white" opacity="0.92"/>
    <circle cx="16" cy="14" r="3.5" fill="${color}"/>
  </svg>`;
  return L.divIcon({
    html: svg,
    className: '',
    iconSize: [size, size * 1.375],
    iconAnchor: [size / 2, size * 1.375],
    popupAnchor: [0, -(size * 1.375)],
  });
}

// ── Fly-to controller component ─────────────────────────────────────────────
function FlyController({ target }) {
  const map = useMap();
  const prevRef = useRef(null);
  useEffect(() => {
    if (!target) return;
    const key = JSON.stringify(target);
    if (prevRef.current === key) return;
    prevRef.current = key;
    if (target.center && target.zoom) {
      map.flyTo(target.center, target.zoom, { duration: 1.4 });
    } else if (target.lat !== undefined) {
      map.flyTo([target.lat, target.lng], target.zoom || 12, { duration: 1.4 });
    }
  }, [target, map]);
  return null;
}

// ── Suggestion chips ─────────────────────────────────────────────────────────
const SUGGESTIONS = [
  { label: '🕌 Taj Mahal',          query: 'Tell me about the Taj Mahal' },
  { label: '🏺 Chola Bronzes',      query: 'Tell me about Chola dynasty bronzes and Nataraja' },
  { label: '🌿 Harappan Civilisation', query: 'Tell me about the Indus Valley Civilisation' },
  { label: '🎨 Warli Art',          query: 'What is Warli art from Maharashtra?' },
  { label: '👑 Mughal Empire',      query: 'Tell me about the Mughal Empire and its cities' },
  { label: '🏰 Hampi',              query: 'Tell me about Hampi and the Vijayanagara Empire' },
];

// ── Popup content for map markers ────────────────────────────────────────────
function MarkerPopup({ label, color }) {
  return (
    <div style={{ fontFamily: 'Inter, sans-serif', minWidth: 160, padding: '2px 0' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <span style={{ width: 10, height: 10, borderRadius: '50%', background: color || '#8b6914', flexShrink: 0, display: 'inline-block' }} />
        <p style={{ fontWeight: 600, fontSize: 13, color: '#1b1c1a', margin: 0, lineHeight: 1.4 }}>{label}</p>
      </div>
    </div>
  );
}

// ── Main component ───────────────────────────────────────────────────────────
export default function AskArkana() {
  const [geoData, setGeoData]   = useState(null);   // current map state from AI
  const [flyTarget, setFlyTarget] = useState(null);  // triggers FlyController
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // When AI response fires a geo event, update the map
  const handleMapEvent = useCallback(({ pinId }) => {
    // The geoData is set directly via the message — handled below
    void pinId; // kept for explore-page compatibility
  }, []);

  // We intercept the AI response to extract geoData BEFORE the hook consumes it.
  // We wrap sendMessage to also capture geoData from the response.
  const {
    messages, isTyping, inputVal, setInputVal, sendMessage: _sendMessage,
  } = useArkanaChat(handleMapEvent, (response) => {
    if (response?.geoData) {
      setGeoData(response.geoData);
      const g = response.geoData;
      if (g.type === 'marker') {
        setFlyTarget({ lat: g.lat, lng: g.lng, zoom: g.zoom || 12 });
      } else if (g.center) {
        setFlyTarget({ center: g.center, zoom: g.zoom || 6 });
      }
    }
  });

  // Auto-scroll chat
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  const handleSend = () => { if (inputVal.trim()) _sendMessage(inputVal); };
  const handleKey  = (e) => { if (e.key === 'Enter') handleSend(); };

  // ── Render current map layer based on geoData type ─────────────────────
  const renderMapLayers = () => {
    if (!geoData) return null;

    if (geoData.type === 'marker') {
      return (
        <Marker position={[geoData.lat, geoData.lng]} icon={makeIcon('#8b6914', 32)}>
          <Popup closeButton={false} className="arkana-map-popup">
            <MarkerPopup label={geoData.label} color="#8b6914" />
          </Popup>
        </Marker>
      );
    }

    if (geoData.type === 'markers') {
      return geoData.points.map((pt, i) => (
        <Marker key={i} position={[pt.lat, pt.lng]} icon={makeIcon(pt.color || '#8b6914', 26)}>
          <Popup closeButton={false} className="arkana-map-popup">
            <MarkerPopup label={pt.label} color={pt.color} />
          </Popup>
        </Marker>
      ));
    }

    if (geoData.type === 'region') {
      return (
        <>
          <Polygon
            positions={geoData.polygon}
            pathOptions={{
              color: geoData.color || '#d97706',
              fillColor: geoData.color || '#d97706',
              fillOpacity: 0.18,
              weight: 2,
              dashArray: '6 4',
            }}
          />
          {geoData.markers?.map((m, i) => (
            <Marker key={i} position={[m.lat, m.lng]} icon={makeIcon(m.color || geoData.color, 24)}>
              <Popup closeButton={false} className="arkana-map-popup">
                <MarkerPopup label={m.label} color={m.color || geoData.color} />
              </Popup>
            </Marker>
          ))}
        </>
      );
    }
    return null;
  };

  // ── Legend items ──────────────────────────────────────────────────────────
  const renderLegend = () => {
    if (!geoData) return null;
    const items = [];
    if (geoData.type === 'marker') items.push({ label: geoData.label, color: '#8b6914' });
    if (geoData.type === 'markers') geoData.points.forEach((p) => items.push({ label: p.label, color: p.color }));
    if (geoData.type === 'region') {
      items.push({ label: geoData.label, color: geoData.color, isRegion: true });
      geoData.markers?.forEach((m) => items.push({ label: m.label, color: m.color || geoData.color }));
    }
    return (
      <div style={{
        position: 'absolute', bottom: 16, left: 16, right: 16, zIndex: 1000,
        background: 'rgba(251,249,245,0.96)',
        border: '1px solid rgba(209,197,178,0.5)',
        borderRadius: 12,
        padding: '12px 16px',
        backdropFilter: 'blur(12px)',
        boxShadow: '0 4px 24px rgba(0,0,0,0.10)',
        maxHeight: 200,
        overflowY: 'auto',
      }}>
        <p style={{
          fontFamily: 'Inter, sans-serif', fontSize: 10, color: '#807665',
          textTransform: 'uppercase', letterSpacing: '0.1em', fontWeight: 600, margin: '0 0 8px'
        }}>
          📍 Locations on map
        </p>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
          {items.map((item, i) => (
            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              {item.isRegion ? (
                <span style={{
                  width: 14, height: 10, borderRadius: 2, background: item.color,
                  opacity: 0.6, border: `1.5px dashed ${item.color}`, flexShrink: 0
                }} />
              ) : (
                <span style={{ width: 8, height: 8, borderRadius: '50%', background: item.color, flexShrink: 0 }} />
              )}
              <span style={{ fontFamily: 'Inter, sans-serif', fontSize: 11, color: '#1b1c1a', lineHeight: 1.4 }}>{item.label}</span>
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <main
      style={{ display: 'flex', flexDirection: 'row', height: '100vh', paddingTop: 80, overflow: 'hidden' }}
      aria-label="Ask Arkana — AI Heritage Guide with Interactive Map"
    >
      {/* ══════════════ LEFT — Leaflet Map ══════════════════════════════════ */}
      <section
        style={{ width: '55%', position: 'relative', flexShrink: 0, height: 'calc(100vh - 80px)' }}
        aria-label="Interactive Heritage Map"
      >
        {/* Map badge */}
        <div style={{
          position: 'absolute', top: 14, left: 14, zIndex: 1000,
          display: 'flex', alignItems: 'center', gap: 7,
          background: 'rgba(251,249,245,0.95)',
          border: '1px solid rgba(209,197,178,0.55)',
          borderRadius: 9, padding: '7px 13px',
          backdropFilter: 'blur(10px)',
          boxShadow: '0 2px 10px rgba(139,105,20,0.10)',
        }}>
          <span className="material-symbols-outlined" style={{ fontSize: 15, color: '#8b6914' }}>explore</span>
          <span style={{ fontFamily: 'Inter, sans-serif', fontSize: 11, fontWeight: 700, color: '#4e4637', letterSpacing: '0.09em', textTransform: 'uppercase' }}>
            Heritage Map
          </span>
        </div>

        {/* Idle state overlay */}
        {!geoData && (
          <div style={{
            position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)',
            zIndex: 1000, textAlign: 'center', pointerEvents: 'none',
          }}>
            <div style={{
              background: 'rgba(251,249,245,0.90)',
              border: '1px solid rgba(209,197,178,0.45)',
              borderRadius: 16, padding: '20px 28px',
              backdropFilter: 'blur(12px)',
              boxShadow: '0 4px 20px rgba(0,0,0,0.08)',
            }}>
              <span className="material-symbols-outlined" style={{ fontSize: 36, color: '#8b6914', display: 'block', marginBottom: 8 }}>
                travel_explore
              </span>
              <p style={{ fontFamily: 'Playfair Display, serif', fontSize: 15, color: '#1b1c1a', fontWeight: 600, margin: 0 }}>
                Ask about any heritage site
              </p>
              <p style={{ fontFamily: 'Inter, sans-serif', fontSize: 12, color: '#807665', margin: '6px 0 0' }}>
                The map will respond to your query
              </p>
            </div>
          </div>
        )}

        {/* Leaflet map */}
        <MapContainer
          center={[22.0, 78.0]}
          zoom={5}
          style={{ width: '100%', height: '100%' }}
          zoomControl={true}
          attributionControl={false}
        >
          <TileLayer
            url="https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png"
            attribution="© CARTO"
          />
          <TileLayer
            url="https://{s}.basemaps.cartocdn.com/light_only_labels/{z}/{x}/{y}{r}.png"
            attribution="© CARTO"
            pane="shadowPane"
          />

          {renderMapLayers()}
          {flyTarget && <FlyController target={flyTarget} key={JSON.stringify(flyTarget)} />}
        </MapContainer>

        {/* Legend */}
        {renderLegend()}

        {/* Popup style override */}
        <style>{`
          .arkana-map-popup .leaflet-popup-content-wrapper {
            border-radius: 10px;
            box-shadow: 0 6px 24px rgba(0,0,0,0.13);
            border: 1px solid rgba(209,197,178,0.45);
            padding: 0;
          }
          .arkana-map-popup .leaflet-popup-content { margin: 10px 14px; }
          .arkana-map-popup .leaflet-popup-tip { background: #fff; }
          .leaflet-control-zoom { border: 1px solid rgba(209,197,178,0.5) !important; border-radius: 8px !important; overflow: hidden; }
          .leaflet-control-zoom a { color: #4e4637 !important; font-size: 16px !important; }
        `}</style>
      </section>

      {/* ══════════════ RIGHT — Chat Panel ═══════════════════════════════════ */}
      <section
        style={{
          width: '45%', height: 'calc(100vh - 80px)',
          display: 'flex', flexDirection: 'column',
          background: '#faf8f4',
          borderLeft: '1px solid rgba(209,197,178,0.4)',
        }}
        aria-label="Ask Arkana AI Chat"
      >
        {/* Header */}
        <div style={{
          padding: '18px 26px 16px',
          borderBottom: '1px solid rgba(209,197,178,0.35)',
          flexShrink: 0, background: '#faf8f4',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 13 }}>
            <div style={{
              width: 38, height: 38, borderRadius: 11,
              background: 'linear-gradient(135deg, #8b6914 0%, #c9960a 100%)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              boxShadow: '0 3px 10px rgba(139,105,20,0.30)', flexShrink: 0,
            }}>
              <span className="material-symbols-outlined" style={{ color: '#fff', fontSize: 19 }}>auto_awesome</span>
            </div>
            <div style={{ flex: 1 }}>
              <h1 style={{ fontFamily: 'Playfair Display, serif', fontSize: 19, color: '#1b1c1a', margin: 0, fontWeight: 700, letterSpacing: '-0.01em' }}>
                Ask Arkana
              </h1>
              <p style={{ fontFamily: 'Inter, sans-serif', fontSize: 11, color: '#807665', margin: 0 }}>
                AI heritage guide · map updates with every answer
              </p>
            </div>
            <div style={{
              display: 'flex', alignItems: 'center', gap: 5,
              padding: '4px 11px', borderRadius: 20,
              background: 'rgba(139,105,20,0.07)',
              border: '1px solid rgba(139,105,20,0.18)',
            }}>
              <span style={{ width: 7, height: 7, borderRadius: '50%', background: '#22c55e', display: 'inline-block', animation: 'arkPulse 2s ease-in-out infinite' }} />
              <span style={{ fontFamily: 'Inter, sans-serif', fontSize: 11, color: '#4e4637', fontWeight: 600 }}>Live</span>
            </div>
          </div>
        </div>

        {/* Messages */}
        <div id="ark-messages" style={{ flex: 1, overflowY: 'auto', padding: '22px 24px', display: 'flex', flexDirection: 'column', gap: 18 }}>

          {/* Welcome bubble */}
          <AiBubble>
            <p style={{ margin: 0, lineHeight: 1.65 }}>
              Namaste! 🙏 I'm <strong>Arkana</strong>, your AI guide to India's cultural heritage.
            </p>
            <p style={{ margin: '8px 0 0', lineHeight: 1.65 }}>
              Ask me about any monument, dynasty, art form or civilisation — and watch the{' '}
              <strong style={{ color: '#8b6914' }}>map on the left light up</strong> with exact locations, regions and routes.
            </p>
          </AiBubble>

          {/* Suggestion chips — only at start */}
          {messages.length <= 1 && !isTyping && (
            <div style={{ paddingLeft: 44 }}>
              <p style={{ fontFamily: 'Inter, sans-serif', fontSize: 10, color: '#807665', textTransform: 'uppercase', letterSpacing: '0.1em', margin: '0 0 9px' }}>Try asking about</p>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 7 }}>
                {SUGGESTIONS.map((s) => (
                  <ChipBtn key={s.label} onClick={() => _sendMessage(s.query)}>{s.label}</ChipBtn>
                ))}
              </div>
            </div>
          )}

          {/* Rendered messages */}
          {messages.map((msg) => (
            <div key={msg.id}>
              {msg.sender === 'user' ? (
                <UserBubble>{msg.text}</UserBubble>
              ) : (
                <AiBubble streaming={msg.isStreaming}>
                  <div style={{ margin: 0, lineHeight: 1.65, whiteSpace: 'pre-line' }}>
                    {msg.text}
                    {msg.isStreaming && <Cursor />}
                    {!msg.isStreaming && msg.citation && (
                      <sup style={{ color: '#8b6914', fontSize: 9, marginLeft: 2, cursor: 'pointer', fontWeight: 700 }} title={msg.source}>
                        [{msg.citation}]
                      </sup>
                    )}
                  </div>
                  {!msg.isStreaming && msg.source && (
                    <p style={{ fontFamily: 'Inter, sans-serif', fontSize: 11, color: '#807665', fontStyle: 'italic', borderLeft: '2px solid rgba(209,197,178,0.7)', paddingLeft: 8, margin: '10px 0 0' }}>
                      Source: {msg.source}
                    </p>
                  )}
                  {msg.cardVisible && msg.insightCard && <InsightCard card={msg.insightCard} />}
                </AiBubble>
              )}
            </div>
          ))}

          {/* Typing dots */}
          {isTyping && (
            <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
              <AvatarIcon />
              <div style={{
                background: '#fff', border: '1px solid rgba(209,197,178,0.4)',
                borderRadius: '4px 14px 14px 14px',
                padding: '13px 16px', display: 'flex', gap: 5, alignItems: 'center',
              }}>
                {[0, 130, 260].map((d) => (
                  <span key={d} style={{
                    width: 7, height: 7, borderRadius: '50%', background: '#8b6914',
                    display: 'inline-block',
                    animation: `arkBounce 1.1s ease-in-out ${d}ms infinite`,
                  }} />
                ))}
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div style={{
          padding: '14px 22px 18px',
          borderTop: '1px solid rgba(209,197,178,0.35)',
          background: '#faf8f4', flexShrink: 0,
        }}>
          <div
            style={{
              display: 'flex', alignItems: 'center', gap: 10,
              background: '#fff',
              border: '1.5px solid rgba(209,197,178,0.55)',
              borderRadius: 13, padding: '10px 12px 10px 16px',
              boxShadow: '0 2px 10px rgba(0,0,0,0.04)',
              transition: 'border-color 0.2s, box-shadow 0.2s',
            }}
            onFocusCapture={(e) => {
              e.currentTarget.style.borderColor = '#8b6914';
              e.currentTarget.style.boxShadow = '0 0 0 3px rgba(139,105,20,0.09)';
            }}
            onBlurCapture={(e) => {
              e.currentTarget.style.borderColor = 'rgba(209,197,178,0.55)';
              e.currentTarget.style.boxShadow = '0 2px 10px rgba(0,0,0,0.04)';
            }}
          >
            <input
              ref={inputRef}
              id="arkana-ask-input"
              type="text"
              value={inputVal}
              onChange={(e) => setInputVal(e.target.value)}
              onKeyDown={handleKey}
              placeholder="Ask about any monument, dynasty, or art form…"
              disabled={isTyping}
              aria-label="Ask Arkana about Indian cultural heritage"
              style={{
                flex: 1, border: 'none', outline: 'none',
                background: 'transparent',
                fontFamily: 'Inter, sans-serif', fontSize: 14, color: '#1b1c1a',
              }}
            />
            <button
              id="arkana-ask-send"
              onClick={handleSend}
              disabled={isTyping || !inputVal.trim()}
              aria-label="Send"
              style={{
                width: 34, height: 34, borderRadius: 9, border: 'none',
                background: (inputVal.trim() && !isTyping)
                  ? 'linear-gradient(135deg,#8b6914,#c9960a)'
                  : 'rgba(209,197,178,0.3)',
                cursor: (inputVal.trim() && !isTyping) ? 'pointer' : 'default',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                flexShrink: 0, transition: 'background 0.2s',
              }}
            >
              <span className="material-symbols-outlined" style={{ color: (inputVal.trim() && !isTyping) ? '#fff' : '#aaa', fontSize: 17 }}>
                arrow_upward
              </span>
            </button>
          </div>
          <p style={{ fontFamily: 'Inter, sans-serif', fontSize: 10, color: '#aaa', textAlign: 'center', margin: '8px 0 0' }}>
            Responses include interactive map locations
          </p>
        </div>

        {/* Keyframes */}
        <style>{`
          @keyframes arkPulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:.5;transform:scale(1.35)} }
          @keyframes arkBounce { 0%,80%,100%{transform:translateY(0)} 40%{transform:translateY(-7px)} }
          @keyframes arkBlink { 0%,100%{opacity:1} 50%{opacity:0} }
          #ark-messages::-webkit-scrollbar { width: 4px }
          #ark-messages::-webkit-scrollbar-thumb { background: rgba(139,105,20,.18); border-radius: 2px }
        `}</style>
      </section>
    </main>
  );
}

/* ── Sub-components ──────────────────────────────────────────────────────── */
function AvatarIcon({ size = 30 }) {
  return (
    <div style={{
      width: size, height: size, borderRadius: size * 0.33,
      background: 'linear-gradient(135deg,#8b6914,#c9960a)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
    }}>
      <span className="material-symbols-outlined" style={{ color: '#fff', fontSize: size * 0.55 }}>auto_awesome</span>
    </div>
  );
}

function AiBubble({ children }) {
  return (
    <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
      <AvatarIcon />
      <div style={{ maxWidth: '86%' }}>
        <div style={{
          background: '#fff',
          border: '1px solid rgba(209,197,178,0.4)',
          borderRadius: '4px 14px 14px 14px',
          padding: '13px 16px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.04)',
          fontFamily: 'Inter, sans-serif', fontSize: 14, color: '#1b1c1a',
        }}>
          {children}
        </div>
      </div>
    </div>
  );
}

function UserBubble({ children }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
      <div style={{
        maxWidth: '78%',
        background: 'linear-gradient(135deg,#8b6914,#a67c18)',
        color: '#fff',
        borderRadius: '14px 4px 14px 14px',
        padding: '12px 16px',
        fontFamily: 'Inter, sans-serif', fontSize: 14, lineHeight: 1.6,
        boxShadow: '0 4px 12px rgba(139,105,20,0.22)',
      }}>
        {children}
      </div>
    </div>
  );
}

function ChipBtn({ children, onClick }) {
  const [hov, setHov] = useState(false);
  return (
    <button
      onClick={onClick}
      onMouseEnter={() => setHov(true)}
      onMouseLeave={() => setHov(false)}
      style={{
        fontFamily: 'Inter, sans-serif', fontSize: 12, fontWeight: 500,
        color: hov ? '#fff' : '#8b6914',
        border: '1px solid rgba(139,105,20,0.35)',
        borderRadius: 20, padding: '6px 13px',
        background: hov ? '#8b6914' : '#fff',
        cursor: 'pointer', transition: 'all 0.18s',
      }}
    >
      {children}
    </button>
  );
}

function Cursor() {
  return (
    <span style={{
      display: 'inline-block', width: 2, height: 14,
      background: '#8b6914', marginLeft: 2,
      verticalAlign: 'middle', animation: 'arkBlink 0.85s step-end infinite',
    }} />
  );
}

function InsightCard({ card }) {
  return (
    <div style={{
      marginTop: 13,
      background: '#faf8f4',
      border: '1px solid rgba(209,197,178,0.5)',
      borderRadius: 11, padding: '12px 14px',
      display: 'flex', gap: 12, cursor: 'pointer',
    }}>
      <img
        src={card.image} alt={card.title}
        style={{ width: 58, height: 58, objectFit: 'cover', borderRadius: 7, flexShrink: 0, background: '#eae8e4' }}
        onError={(e) => { e.target.style.display = 'none'; }}
      />
      <div style={{ flex: 1, minWidth: 0 }}>
        <p style={{ fontFamily: 'Inter, sans-serif', fontSize: 9, color: '#8b6914', textTransform: 'uppercase', letterSpacing: '0.12em', fontWeight: 700, margin: 0 }}>Insight Card</p>
        <h4 style={{ fontFamily: 'Playfair Display, serif', fontSize: 14, fontWeight: 700, color: '#1b1c1a', margin: '3px 0 2px', lineHeight: 1.3 }}>{card.title}</h4>
        <p style={{ fontFamily: 'Inter, sans-serif', fontSize: 11, color: '#807665', margin: 0 }}>{card.period}</p>
        <a href={card.link || '/artifact'} style={{ fontFamily: 'Inter, sans-serif', fontSize: 11, color: '#8b6914', textDecoration: 'none', fontWeight: 600, marginTop: 5, display: 'inline-block' }}>
          View in Archive →
        </a>
      </div>
    </div>
  );
}
