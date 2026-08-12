import { useState, useEffect, useRef } from 'react';
import { TransitionLink } from '../components/TransitionContext';
import { useArkanaChat } from '../hooks/useArkanaChat';

// Map pin data
const MAP_PINS = [
  { id: 'rajasthan', label: 'Rajasthan',       top: '28%', left: '38%', subtitle: 'Rajput miniatures' },
  { id: 'mp',        label: 'Madhya Pradesh',  top: '45%', left: '52%', subtitle: 'Gond Art' },
  { id: 'maharashtra', label: 'Maharashtra',   top: '62%', left: '35%', subtitle: 'Warli Art' },
  { id: 'tn',        label: 'Tamil Nadu',       top: '72%', left: '48%', subtitle: 'Chola Bronzes' },
  { id: 'delhi',     label: 'Delhi',            top: '20%', left: '50%', subtitle: 'Mughal Architecture' },
];

// Suggested prompts shown below input
const SUGGESTIONS = [
  'Tell me about Warli art',
  'What are Chola bronzes?',
  'Explain Mughal miniature painting',
  'History of Gond art',
];

export default function Explore() {
  const [sliderVal, setSliderVal] = useState(33);
  const [activePin, setActivePin] = useState(null);
  const messagesEndRef = useRef(null);

  // Handle map pin highlight events from NER
  const handleMapEvent = ({ pinId }) => {
    setActivePin(pinId);
    setTimeout(() => setActivePin(null), 3500);
  };

  const { messages, isTyping, inputVal, setInputVal, sendMessage } =
    useArkanaChat(handleMapEvent);

  const yearVal = Math.round(-1000 + (sliderVal / 100) * 3024);
  const formattedYear = yearVal < 0 ? `${Math.abs(yearVal)} BCE` : `${yearVal} CE`;

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  const handleSend = () => sendMessage(inputVal);
  const handleKeyDown = (e) => { if (e.key === 'Enter') handleSend(); };
  const selectPin = (label) => sendMessage(`Tell me about the art and heritage of ${label}.`);
  const selectSuggestion = (text) => sendMessage(text);

  return (
    <main
      className="flex flex-col md:flex-row h-screen pt-20 overflow-hidden bg-[#FAF8F4]"
      aria-label="Explorer page"
    >
      {/* ── LEFT: Map Panel ─────────────────────────────────────────────── */}
      <section
        className="w-full md:w-[60%] h-[50vh] md:h-full relative bg-[#efeeea] border-r border-[#d1c5b2]/50 flex-shrink-0"
        aria-label="Interactive map"
      >
        <div
          className="absolute inset-0"
          style={{ background: 'linear-gradient(135deg, #e6e2da 0%, #d8d2c8 100%)' }}
        >
          {/* Dot grid texture */}
          <div
            className="w-full h-full"
            style={{
              backgroundImage: 'radial-gradient(circle at 2px 2px, rgba(139,105,20,0.12) 1px, transparent 0)',
              backgroundSize: '24px 24px',
            }}
          />

          {/* Territory blobs */}
          <div className="absolute top-[35%] left-[40%] w-56 h-56 bg-[#8b6914]/10 rounded-[40%_60%_70%_30%] blur-2xl pointer-events-none" />
          <div className="absolute top-[55%] left-[55%] w-40 h-40 bg-[#8b6914]/8 rounded-[60%_40%_30%_70%] blur-xl pointer-events-none" />

          {/* INDIA watermark */}
          <div className="absolute top-[42%] left-[44%] font-['Playfair_Display'] text-[48px] text-[#1b1c1a]/10 select-none pointer-events-none font-bold tracking-widest">
            INDIA
          </div>

          {/* Map pins */}
          {MAP_PINS.map((pin) => {
            const isActive = activePin === pin.id;
            return (
              <button
                key={pin.id}
                className="absolute group z-10 cursor-pointer"
                style={{ top: pin.top, left: pin.left }}
                onClick={() => selectPin(pin.label)}
                aria-label={`${pin.label} — ${pin.subtitle}`}
                title={`${pin.label} — ${pin.subtitle}`}
              >
                {/* Pulse ring when NER fires */}
                {isActive && (
                  <span className="absolute inset-0 -m-2 rounded-full animate-ping bg-[#8b6914]/40" />
                )}
                <div
                  className={`w-4 h-4 rounded-full shadow-[0_0_12px_rgba(139,105,20,0.6)] transition-all duration-300
                    ${isActive
                      ? 'bg-[#c9960a] scale-150 shadow-[0_0_20px_rgba(139,105,20,0.9)]'
                      : 'bg-[#8b6914] group-hover:scale-150'
                    }`}
                />
                <div className="absolute -top-10 left-1/2 -translate-x-1/2 bg-white/95 backdrop-blur border border-[#d1c5b2] rounded px-2 py-1 whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none shadow-sm">
                  <p className="text-xs font-semibold text-[#1b1c1a]">{pin.label}</p>
                  <p className="text-[10px] text-[#4e4637]">{pin.subtitle}</p>
                </div>
              </button>
            );
          })}

          {/* NER Map Event Banner */}
          {activePin && (
            <div className="absolute top-4 left-1/2 -translate-x-1/2 z-20 bg-[#8b6914] text-white text-xs font-['Inter'] px-4 py-1.5 rounded-full shadow-lg animate-fade-in pointer-events-none">
              📍 Highlighting: {MAP_PINS.find((p) => p.id === activePin)?.label}
            </div>
          )}
        </div>

        {/* Timeline slider */}
        <div className="absolute bottom-0 w-full p-6 bg-gradient-to-t from-[#efeeea] to-transparent">
          <div className="max-w-xl mx-auto backdrop-blur-md bg-white/70 p-4 rounded-lg border border-[#d1c5b2]/30">
            <div className="flex justify-between font-['Playfair_Display'] text-[14px] text-[#4e4637] mb-3">
              <span>1000 BCE</span>
              <span className="text-[#8b6914] font-semibold">{formattedYear}</span>
              <span>2024 CE</span>
            </div>
            <input
              className="w-full"
              max="100"
              min="0"
              type="range"
              value={sliderVal}
              onChange={(e) => setSliderVal(parseInt(e.target.value))}
              aria-label="Timeline slider from 1000 BCE to 2024 CE"
            />
          </div>
        </div>
      </section>

      {/* ── RIGHT: Chat Panel ────────────────────────────────────────────── */}
      <section
        className="w-full md:w-[40%] h-[50vh] md:h-full bg-white flex flex-col"
        aria-label="Ask Arkana AI chat"
      >
        {/* Panel header */}
        <div className="flex items-center gap-4 px-8 py-6 border-b border-[#d1c5b2]/30 flex-shrink-0">
          <div className="flex-grow h-px bg-[#d1c5b2]" />
          <div className="flex items-center gap-2">
            {/* Live indicator dot */}
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#8b6914] opacity-60" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-[#8b6914]" />
            </span>
            <h2 className="font-['Playfair_Display'] text-[14px] text-[#8b6914] uppercase tracking-widest whitespace-nowrap">
              Ask Arkana
            </h2>
          </div>
          <div className="flex-grow h-px bg-[#d1c5b2]" />
        </div>

        {/* Messages list */}
        <div className="flex-grow overflow-y-auto p-8 space-y-6 flex flex-col chat-scroll">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`max-w-[88%] ${
                msg.sender === 'user'
                  ? 'self-end bg-[#f5f3ef] p-4 rounded-xl rounded-tr-none border border-[#d1c5b2]/20 text-[#1b1c1a]'
                  : 'self-start text-[#4e4637]'
              } font-['Inter'] text-[15px] leading-relaxed`}
            >
              {/* Message text with streaming cursor */}
              <p className="whitespace-pre-line">
                {msg.text}
                {msg.isStreaming && (
                  <span className="inline-block w-0.5 h-4 bg-[#8b6914] ml-0.5 align-middle animate-blink" />
                )}
                {/* Citation superscript */}
                {msg.sender === 'ai' && msg.citation && !msg.isStreaming && (
                  <sup
                    className="text-[#8b6914] text-[10px] cursor-pointer ml-0.5 font-medium"
                    title={msg.source || 'Source citation'}
                  >
                    [{msg.citation}]
                  </sup>
                )}
              </p>

              {/* Source label */}
              {msg.sender === 'ai' && msg.source && !msg.isStreaming && (
                <p className="mt-2 text-[11px] text-[#8b6914]/60 font-['Inter'] italic border-l-2 border-[#d1c5b2] pl-2">
                  Source: {msg.source}
                </p>
              )}

              {/* Insight card — slides in after streaming */}
              {msg.sender === 'ai' && msg.insightCard && msg.cardVisible && (
                <div
                  className="bg-[#faf8f4] border border-[#d1c5b2] p-4 rounded-lg flex gap-4 hover:shadow-[0_2px_12px_rgba(139,105,20,0.12)] transition-all duration-300 mt-4 cursor-pointer insight-card-appear"
                  role="article"
                >
                  <img
                    src={msg.insightCard.image}
                    alt={msg.insightCard.title}
                    className="w-20 h-20 object-cover rounded bg-[#eae8e4] flex-shrink-0"
                  />
                  <div className="flex flex-col justify-center min-w-0">
                    <p className="text-[10px] text-[#8b6914] uppercase tracking-widest mb-1 font-medium">
                      Insight Card
                    </p>
                    <h4 className="font-['Playfair_Display'] text-[15px] font-semibold text-[#1b1c1a] leading-tight">
                      {msg.insightCard.title}
                    </h4>
                    <p className="text-[11px] text-[#4e4637] mt-1">{msg.insightCard.period}</p>
                    <TransitionLink
                      to={msg.insightCard.link || '/artifact'}
                      className="text-[11px] text-[#8b6914] heritage-link mt-2 self-start"
                    >
                      View in Archive →
                    </TransitionLink>
                  </div>
                </div>
              )}
            </div>
          ))}

          {/* Typing indicator */}
          {isTyping && (
            <div className="self-start flex gap-1.5 p-3 bg-[#f5f3ef] rounded-xl rounded-tl-none border border-[#d1c5b2]/20">
              <div className="w-2 h-2 rounded-full bg-[#807665] animate-bounce" style={{ animationDelay: '0ms' }} />
              <div className="w-2 h-2 rounded-full bg-[#807665] animate-bounce" style={{ animationDelay: '150ms' }} />
              <div className="w-2 h-2 rounded-full bg-[#807665] animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Suggestion chips */}
        {messages.length <= 2 && !isTyping && (
          <div className="px-8 pb-3 flex flex-wrap gap-2 flex-shrink-0">
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                onClick={() => selectSuggestion(s)}
                className="text-[11px] font-['Inter'] text-[#8b6914] border border-[#d1c5b2] rounded-full px-3 py-1 hover:bg-[#f5f3ef] transition-colors"
              >
                {s}
              </button>
            ))}
          </div>
        )}

        {/* Chat input */}
        <div className="p-6 border-t border-[#d1c5b2]/30 bg-white flex-shrink-0">
          <div className="relative flex items-center">
            <input
              id="arkana-chat-input"
              className="w-full bg-transparent border-0 border-b border-[#d1c5b2] focus:border-[#8b6914] focus:ring-0 px-0 py-3 text-[16px] text-[#1b1c1a] placeholder:text-[#4e4637]/50 transition-colors pr-10"
              placeholder="Inquire about an era, artifact, or culture..."
              type="text"
              value={inputVal}
              onChange={(e) => setInputVal(e.target.value)}
              onKeyDown={handleKeyDown}
              aria-label="Type your question"
              disabled={isTyping}
            />
            <button
              id="arkana-chat-send"
              onClick={handleSend}
              disabled={isTyping || !inputVal.trim()}
              className="absolute right-0 text-[#8b6914] hover:text-[#a67c1a] disabled:opacity-30 transition-colors flex items-center justify-center"
              aria-label="Send message"
            >
              <span className="material-symbols-outlined">send</span>
            </button>
          </div>
          <p className="text-[10px] text-[#4e4637]/40 font-['Inter'] mt-2">
            Demo mode — responses are curated from the Arkana heritage archive
          </p>
        </div>
      </section>
    </main>
  );
}