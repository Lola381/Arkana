import { useState, useEffect, useRef } from 'react';
import { TransitionLink } from '../components/TransitionContext';
import { CHAT_RESPONSES } from '../data/artifacts';

export default function Explore() {
  const [sliderVal, setSliderVal] = useState(33);
  const [inputVal, setInputVal] = useState('');
  const [messages, setMessages] = useState([
    {
      id: 1,
      sender: 'ai',
      text: "Welcome to the archive. I can help you explore any aspect of India's cultural heritage — from ancient Mauryan sculptures to contemporary folk traditions. What would you like to discover?",
    },
    {
      id: 2,
      sender: 'user',
      text: 'Tell me about the Ashokan pillars and their inscriptions.',
    },
    {
      id: 3,
      sender: 'ai',
      text: 'The Ashokan Pillars were established by Emperor Ashoka during the 3rd century BCE. They bear inscriptions in Brahmi script detailing his policies of Dhamma (moral law) — emphasizing non-violence, tolerance, and compassion.',
      citation: '1',
      hasCard: true,
    },
  ]);
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);

  // Map pin coordinate data
  const mapPins = [
    { id: 'rajasthan', label: 'Rajasthan', top: '28%', left: '38%', subtitle: 'Rajput miniatures' },
    { id: 'mp', label: 'Madhya Pradesh', top: '45%', left: '52%', subtitle: 'Gond Art' },
    { id: 'maharashtra', label: 'Maharashtra', top: '62%', left: '35%', subtitle: 'Warli Art' },
    { id: 'tn', label: 'Tamil Nadu', top: '72%', left: '48%', subtitle: 'Chola Bronzes' },
    { id: 'delhi', label: 'Delhi', top: '20%', left: '50%', subtitle: 'Mughal Architecture' },
  ];

  // Dynamic Year computation
  const yearVal = Math.round(-1000 + (sliderVal / 100) * 3024);
  const formattedYear = yearVal < 0 ? `${Math.abs(yearVal)} BCE` : `${yearVal} CE`;

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  const handleSend = () => {
    const text = inputVal.trim();
    if (!text) return;

    setMessages((prev) => [...prev, { id: Date.now(), sender: 'user', text }]);
    setInputVal('');
    setIsTyping(true);

    setTimeout(() => {
      const responseText = CHAT_RESPONSES[Math.floor(Math.random() * CHAT_RESPONSES.length)];
      setMessages((prev) => [
        ...prev,
        { id: Date.now() + 1, sender: 'ai', text: responseText },
      ]);
      setIsTyping(false);
    }, 1000);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') handleSend();
  };

  const selectPin = (pinLabel) => {
    setInputVal(`Tell me about the art and heritage of ${pinLabel}.`);
  };

  return (
    <main className="flex flex-col md:flex-row h-screen pt-20 overflow-hidden bg-[#FAF8F4]" aria-label="Explorer page">
      {/* LEFT: Map Panel */}
      <section className="w-full md:w-[60%] h-[50vh] md:h-full relative bg-[#efeeea] border-r border-[#d1c5b2]/50 flex-shrink-0" aria-label="Interactive map">
        <div className="absolute inset-0" style={{ background: 'linear-gradient(135deg, #e6e2da 0%, #d8d2c8 100%)' }}>
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

          {/* India label */}
          <div className="absolute top-[42%] left-[44%] font-['Playfair_Display'] text-[48px] text-[#1b1c1a]/10 select-none pointer-events-none font-bold tracking-widest">
            INDIA
          </div>

          {/* Gold pin markers */}
          {mapPins.map((pin) => (
            <button
              key={pin.id}
              className="absolute group z-10"
              style={{ top: pin.top, left: pin.left }}
              onClick={() => selectPin(pin.label)}
              aria-label={`${pin.label} — ${pin.subtitle}`}
              title={`${pin.label} — ${pin.subtitle}`}
            >
              <div className="w-4 h-4 bg-[#8b6914] rounded-full shadow-[0_0_12px_rgba(139,105,20,0.6)] group-hover:scale-150 transition-transform duration-300"></div>
              <div className="absolute -top-8 left-1/2 -translate-x-1/2 bg-white/90 backdrop-blur border border-[#d1c5b2] rounded px-2 py-1 text-xs font-medium text-[#1b1c1a] whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity">
                {pin.label}
              </div>
            </button>
          ))}
        </div>

        {/* Timeline slider at bottom */}
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

      {/* RIGHT: Chat Panel */}
      <section className="w-full md:w-[40%] h-[50vh] md:h-full bg-white flex flex-col" aria-label="Ask Arkana AI chat">
        {/* Panel Header */}
        <div className="flex items-center gap-4 px-8 py-6 border-b border-[#d1c5b2]/30 flex-shrink-0">
          <div className="flex-grow h-px bg-[#d1c5b2]"></div>
          <h2 className="font-['Playfair_Display'] text-[14px] text-[#8b6914] uppercase tracking-widest whitespace-nowrap">
            Ask Arkana
          </h2>
          <div className="flex-grow h-px bg-[#d1c5b2]"></div>
        </div>

        {/* Messages list */}
        <div className="flex-grow overflow-y-auto p-8 space-y-8 flex flex-col chat-scroll">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`max-w-[85%] ${
                msg.sender === 'user'
                  ? 'self-end bg-[#f5f3ef] p-4 rounded-xl rounded-tr-none border border-[#d1c5b2]/20 text-[#1b1c1a]'
                  : 'self-start text-[#4e4637]'
              } font-['Inter'] text-[16px] leading-relaxed`}
            >
              <p>
                {msg.text}
                {msg.sender === 'ai' && msg.citation && (
                  <sup className="text-[#8b6914] text-xs cursor-pointer ml-0.5" title="Source citation">
                    [{msg.citation}]
                  </sup>
                )}
              </p>

              {/* Inline Insight Card if message hasCard */}
              {msg.hasCard && (
                <div className="bg-white border border-[#d1c5b2] p-4 rounded flex gap-4 hover:shadow-[0_2px_8px_rgba(0,0,0,0.08)] transition-shadow cursor-pointer mt-4" role="article">
                  <img
                    src="https://lh3.googleusercontent.com/aida-public/AB6AXuC4GiUO8DnCPkZiHnNW5Tmstim5dcTAiKAtm9bi72Hap9GEURhywdMcZtYZP7P3mMtn_YbwP2ysP9mG-eB5Cgagv6skn0J_9ruQMakIXyb_i6giRqGz-_0klySrnr1kyupeE8BVWkdZ8wQFLeCPfLxdx4eXKrXlHwMpPJTuxL34Lx2qnmK5885rNsRqfzUXYgaXXj2DHthPgRMIdpMN5w3_hgC13Q586EMUflva30TeOeNg5MbXF1sD-AQmm9-Fn2OpxvKcsr3Edg"
                    alt="Ashokan Pillar stone inscription"
                    className="w-20 h-20 object-cover rounded bg-[#eae8e4] flex-shrink-0"
                  />
                  <div className="flex flex-col justify-center min-w-0">
                    <h4 className="font-['Playfair_Display'] text-[16px] font-semibold text-[#1b1c1a]">
                      Ashokan Pillar Fragment
                    </h4>
                    <p className="text-[12px] text-[#4e4637] mt-1">3rd Century BCE · Maurya Empire</p>
                    <TransitionLink
                      to="/artifact"
                      className="text-[12px] text-[#8b6914] heritage-link mt-2 self-start"
                    >
                      View in Archive →
                    </TransitionLink>
                  </div>
                </div>
              )}
            </div>
          ))}

          {/* Typing Indicator */}
          {isTyping && (
            <div className="self-start flex gap-1.5 p-3 bg-[#f5f3ef] rounded-xl rounded-tl-none border border-[#d1c5b2]/20">
              <div className="w-2 h-2 rounded-full bg-[#807665] animate-bounce" style={{ animationDelay: '0ms' }} />
              <div className="w-2 h-2 rounded-full bg-[#807665] animate-bounce" style={{ animationDelay: '150ms' }} />
              <div className="w-2 h-2 rounded-full bg-[#807665] animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Chat Input */}
        <div className="p-6 border-t border-[#d1c5b2]/30 bg-white flex-shrink-0">
          <div className="relative flex items-center">
            <input
              className="w-full bg-transparent border-0 border-b border-[#d1c5b2] focus:border-[#8b6914] focus:ring-0 px-0 py-3 text-[16px] text-[#1b1c1a] placeholder:text-[#4e4637]/50 transition-colors"
              placeholder="Inquire about an era, artifact, or culture..."
              type="text"
              value={inputVal}
              onChange={(e) => setInputVal(e.target.value)}
              onKeyDown={handleKeyDown}
              aria-label="Type your question"
            />
            <button
              onClick={handleSend}
              className="absolute right-0 text-[#8b6914] hover:text-[#a67c1a] transition-colors flex items-center justify-center"
              aria-label="Send message"
            >
              <span className="material-symbols-outlined">send</span>
            </button>
          </div>
        </div>
      </section>
    </main>
  );
}
