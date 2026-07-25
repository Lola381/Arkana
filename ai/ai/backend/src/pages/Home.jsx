import { useEffect } from 'react';
import { TransitionLink } from '../components/TransitionContext';
import ScrollReveal from '../components/ScrollReveal';
import ArtifactCard from '../components/ArtifactCard';
import { COLLECTION_ARTIFACTS, HERO_IMAGES } from '../data/artifacts';

export default function Home() {
  useEffect(() => {
    const handleMouseMove = (e) => {
      const elements = document.querySelectorAll('.floating-element');
      elements.forEach((el) => {
        const speed = parseFloat(el.getAttribute('data-speed')) || 0.1;
        const x = (e.clientX * speed) / 10;
        const y = (e.clientY * speed) / 10;
        const rotate = el.getAttribute('data-rotate') || '0deg';
        el.style.transform = `translateX(${x}px) translateY(${y}px) rotate(${rotate})`;
      });
    };

    window.addEventListener('mousemove', handleMouseMove, { passive: true });
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  return (
    <div className="bg-[#fbf9f5] min-h-screen text-[#1b1c1a] font-['Inter'] antialiased">
      {/* SECTION 1: HERO */}
      <section className="relative min-h-screen flex items-center justify-center overflow-hidden bg-[#fbf9f5] pt-20">
        {/* Floating Artifact Elements */}
        <div className="absolute inset-0 z-0 pointer-events-none">
          {HERO_IMAGES.map((img, idx) => {
            // Extracted rotations based on coordinates
            const rotations = ['-6deg', '3deg', '12deg', '-12deg'];
            const rotate = rotations[idx] || '0deg';
            return (
              <div
                key={idx}
                className={`floating-element absolute shadow-sm border border-[#d1c5b2] overflow-hidden bg-white ${img.pos}`}
                data-speed={img.speed}
                data-rotate={rotate}
                style={{ transform: `rotate(${rotate})` }}
              >
                <img src={img.src} alt={img.alt} className="w-full h-full object-cover" />
              </div>
            );
          })}
        </div>

        {/* Hero Content */}
        <div className="relative z-10 text-center max-w-4xl mx-auto px-5 md:px-0">
          <ScrollReveal>
            <h1 className="font-['Playfair_Display'] text-[40px] md:text-[64px] font-semibold text-[#1b1c1a] leading-[1.1] tracking-[-0.02em] mb-6">
              Discover India's<br />Living Heritage
            </h1>
          </ScrollReveal>
          <ScrollReveal delay={100}>
            <p className="text-[18px] text-[#4e4637] leading-[1.6] max-w-2xl mx-auto mb-10">
              An archival journey through 300+ meticulously digitized artifacts, exploring millennia of art, architecture, and cultural narratives.
            </p>
          </ScrollReveal>
          <ScrollReveal delay={200}>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <TransitionLink
                to="/browse"
                className="px-8 py-3 border border-[#1b1c1a] rounded font-semibold hover:bg-[#1b1c1a] hover:text-[#fbf9f5] transition-colors duration-300"
              >
                Explore Collection
              </TransitionLink>
              <TransitionLink
                to="/explore"
                className="px-8 py-3 text-[#8b6914] heritage-link font-medium flex items-center gap-1"
              >
                Ask Arkana <span className="material-symbols-outlined text-[14px]">arrow_forward</span>
              </TransitionLink>
            </div>
          </ScrollReveal>
        </div>
      </section>

      {/* SECTION 2: FEATURED CULTURES */}
      <section className="py-[120px] max-w-[1280px] mx-auto px-5 md:px-20">
        <ScrollReveal>
          <div className="flex items-center gap-4 mb-20">
            <span className="font-['Playfair_Display'] text-[14px] font-medium tracking-[0.12em] text-[#1b1c1a] uppercase">CULTURES</span>
            <div className="h-[1px] bg-[#d1c5b2] flex-grow"></div>
          </div>
        </ScrollReveal>

        <div className="space-y-32">
          {/* Culture 1 */}
          <ScrollReveal>
            <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-center">
              <div className="md:col-span-4 md:col-start-1 space-y-6">
                <span className="text-[12px] font-medium uppercase text-[#807665] tracking-wider">Folk Tradition</span>
                <h2 className="font-['Playfair_Display'] text-[32px] font-medium text-[#1b1c1a]">Warli Painting</h2>
                <p className="text-[16px] text-[#4e4637] leading-[1.6]">
                  Rooted in the indigenous traditions of Maharashtra, Warli art employs simple geometric vocabulary to depict intricate social life, nature, and rituals on earth-toned walls.
                </p>
                <TransitionLink to="/culture" className="heritage-link text-[#8b6914] font-medium mt-4">
                  Discover Warli
                </TransitionLink>
              </div>
              <div className="md:col-span-7 md:col-start-6 h-[500px] md:h-[600px] artifact-image-container border border-[#d1c5b2]">
                <img
                  className="w-full h-full object-cover"
                  src="https://lh3.googleusercontent.com/aida-public/AB6AXuApO_jE8us-Xp_A0aTWB7s_sR-3c64OlEY6wG1rL0t4cTQOv_fZDedEVEmf7tUurs8Dq-leO9N_u3J-vRkhL3AdlR8xJZE_vA_oGS0asCoxz2XfIx3zisdsND5_Iq6t7rpckdbOiUGO5a6RlPwMpxYvlAzroVVbh5qnx_kSiLV76kZek1Hp9aW0YvqB-urGwKDtktHX-8l5vi39kVZfqpUY9u7khLvvk7NTgC-S3P93ALnQVmJB5xb8lt92AqP4WhAZEDtqG1Ryhw"
                  alt="Warli Art"
                />
              </div>
            </div>
          </ScrollReveal>

          {/* Culture 2 (Flipped) */}
          <ScrollReveal>
            <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-center">
              <div className="md:col-span-7 md:col-start-1 h-[500px] md:h-[600px] artifact-image-container border border-[#d1c5b2] order-2 md:order-1">
                <img
                  className="w-full h-full object-cover"
                  src="https://lh3.googleusercontent.com/aida-public/AB6AXuBTRmBqC2GrfspdfLryjH_PLTJLh95wMYWbj5QR4cCTGqgUoM5JE3g5peTEhyvowfm3nV_u5Z-KB6xUdzjbs3Z8oRApPw7q2RQDglGj2LAMwcSkLATEJYrnHHhM41IoOrAUeudaJXnB2Tvf3EhpOUKVqgfzClY8mw0OpAe1OrQGcAT11X_bRudrzovndhJEp4iX4vll5NQfKK5CUxqIUZHaCzmbtQQNU8G7UJYpvwq1i841Mz-sbBRt09nTxYo1KjCnK7rVZbcW1w"
                  alt="Mughal Miniature"
                />
              </div>
              <div className="md:col-span-4 md:col-start-9 space-y-6 order-1 md:order-2">
                <span className="text-[12px] font-medium uppercase text-[#807665] tracking-wider">Courtly Art</span>
                <h2 className="font-['Playfair_Display'] text-[32px] font-medium text-[#1b1c1a]">Mughal Miniatures</h2>
                <p className="text-[16px] text-[#4e4637] leading-[1.6]">
                  A synthesis of Persian elegance and Indian vitality, these meticulous paintings offer an intimate window into the opulence, flora, and fauna of the imperial court.
                </p>
                <TransitionLink to="/browse" className="heritage-link text-[#8b6914] font-medium mt-4">
                  Explore Miniatures
                </TransitionLink>
              </div>
            </div>
          </ScrollReveal>

          {/* Culture 3 */}
          <ScrollReveal>
            <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-center">
              <div className="md:col-span-4 md:col-start-1 space-y-6">
                <span className="text-[12px] font-medium uppercase text-[#807665] tracking-wider">Lost-Wax Casting</span>
                <h2 className="font-['Playfair_Display'] text-[32px] font-medium text-[#1b1c1a]">Chola Bronzes</h2>
                <p className="text-[16px] text-[#4e4637] leading-[1.6]">
                  Originating from the Tamil heartland, these dynamic sculptures capture divine grace and cosmic rhythm through unparalleled mastery of the lost-wax metallurgical process.
                </p>
                <TransitionLink to="/artifact" className="heritage-link text-[#8b6914] font-medium mt-4">
                  View Bronzes
                </TransitionLink>
              </div>
              <div className="md:col-span-7 md:col-start-6 h-[500px] md:h-[600px] artifact-image-container border border-[#d1c5b2]">
                <img
                  className="w-full h-full object-cover"
                  src="https://lh3.googleusercontent.com/aida-public/AB6AXuBZmxSyF4QvpXPPvzKmgDFipy8AJs9OI4Q5KSxtMT0bTS00wjPoCDX63jYWAZ4OV8osK8PyrJ0lzwzVdh2yvy9XruQlaGGDX3XjyB9zh9pyev2fBAwj3YatVmI8DzS9nDpbveoWOtGSCdmBaGCnwunX3iMk2wqAUbGetmcAXzd2NgQOthwvXJS1sUPrmXBnvA4FeeH-zFal3uhwgnlB-pcG6Q0zG_JlbSX1z8Xa714805gzsoGeWi4S-KtcWGYvHvfXhK6Y1sw20A"
                  alt="Chola Nataraja Bronze"
                />
              </div>
            </div>
          </ScrollReveal>
        </div>
      </section>

      {/* SECTION 3: ASK ARKANA (AI Preview) */}
      <section className="py-[120px] bg-[#f2ede6]">
        <div className="max-w-3xl mx-auto px-5 text-center">
          <span className="material-symbols-outlined text-[36px] text-[#8b6914] mb-6 block">auto_awesome</span>
          <h2 className="font-['Playfair_Display'] text-[32px] md:text-[40px] leading-[1.2] text-[#1b1c1a] mb-10">
            Ask anything about India's heritage
          </h2>
          <div className="relative max-w-[640px] mx-auto mb-8">
            <input
              className="w-full bg-white border border-[#d1c5b2] rounded-full py-4 pl-6 pr-14 text-[16px] text-[#1b1c1a] focus:outline-none focus:border-[#8b6914] focus:ring-1 focus:ring-[#8b6914] transition-colors shadow-sm"
              placeholder="E.g., What is the significance of the lotus in Hindu architecture?"
              type="text"
            />
            <TransitionLink
              to="/explore"
              className="absolute right-2 top-1/2 -translate-y-1/2 p-2 text-[#8b6914] hover:bg-[#efeeea] rounded-full transition-colors flex items-center justify-center"
            >
              <span className="material-symbols-outlined">search</span>
            </TransitionLink>
          </div>
          <div className="flex flex-wrap justify-center gap-3">
            <span className="text-[14px] text-[#4e4637] py-2">Try:</span>
            <TransitionLink
              to="/explore"
              className="px-4 py-2 bg-white border border-[#d1c5b2] rounded-full text-[14px] hover:border-[#8b6914] transition-colors text-[#1b1c1a]"
            >
              Warli art
            </TransitionLink>
            <TransitionLink
              to="/explore"
              className="px-4 py-2 bg-white border border-[#d1c5b2] rounded-full text-[14px] hover:border-[#8b6914] transition-colors text-[#1b1c1a]"
            >
              Mughal architecture
            </TransitionLink>
            <TransitionLink
              to="/explore"
              className="px-4 py-2 bg-white border border-[#d1c5b2] rounded-full text-[14px] hover:border-[#8b6914] transition-colors text-[#1b1c1a]"
            >
              Chola bronze
            </TransitionLink>
          </div>
        </div>
      </section>

      {/* SECTION 4: FROM THE COLLECTION */}
      <section className="py-[120px] max-w-[1280px] mx-auto px-5 md:px-20">
        <ScrollReveal>
          <div className="flex items-center gap-4 mb-16">
            <span className="font-['Playfair_Display'] text-[14px] font-medium tracking-[0.12em] text-[#1b1c1a] uppercase">FROM THE COLLECTION</span>
            <div className="h-[1px] bg-[#d1c5b2] flex-grow"></div>
          </div>
        </ScrollReveal>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {COLLECTION_ARTIFACTS.map((artifact) => (
            <ScrollReveal key={artifact.id}>
              {/* Uses Lift & Glow (Animation A) */}
              <ArtifactCard artifact={artifact} variant="lift" showBookmark={false} showType={true} />
            </ScrollReveal>
          ))}
        </div>

        <ScrollReveal delay={100}>
          <div className="mt-12 text-center">
            <TransitionLink
              to="/browse"
              className="px-8 py-3 border border-[#1b1c1a] rounded font-semibold hover:bg-[#1b1c1a] hover:text-[#fbf9f5] transition-colors duration-300 inline-block"
            >
              View Full Archive
            </TransitionLink>
          </div>
        </ScrollReveal>
      </section>

      {/* SECTION 5: SOURCES */}
      <section className="py-20 border-t border-[#d1c5b2]/30 bg-[#fbf9f5]">
        <ScrollReveal>
          <div className="max-w-[1280px] mx-auto px-5 md:px-20 text-center">
            <h4 className="text-[12px] font-medium text-[#807665] uppercase tracking-widest mb-8">Archival Partners &amp; Sources</h4>
            <div className="flex flex-wrap justify-center items-center gap-8 md:gap-16 opacity-60 grayscale hover:grayscale-0 transition-all duration-500">
              <span className="font-['Playfair_Display'] text-[20px] font-semibold">IGNCA</span>
              <span className="font-['Playfair_Display'] text-[20px] font-semibold">National Museum</span>
              <span className="font-['Playfair_Display'] text-[20px] font-semibold">ASI</span>
              <span className="font-['Playfair_Display'] text-[20px] font-semibold">Salar Jung</span>
            </div>
          </div>
        </ScrollReveal>
      </section>

      {/* FOOTER */}
      <footer className="bg-[#f5f3ef] border-t border-[#d1c5b2] py-20">
        <div className="max-w-[1280px] mx-auto px-5 md:px-20 flex flex-col md:flex-row justify-between items-center gap-8">
          <div className="font-['Playfair_Display'] text-[24px] italic text-[#1b1c1a] opacity-80">
            ARKANA.
          </div>
          <div className="flex gap-6 text-[14px]">
            <TransitionLink to="/" className="text-[#4e4637] hover:text-[#8b6914] transition-colors">About</TransitionLink>
            <TransitionLink to="/" className="text-[#4e4637] hover:text-[#8b6914] transition-colors">Privacy</TransitionLink>
            <TransitionLink to="/" className="text-[#4e4637] hover:text-[#8b6914] transition-colors">Contact</TransitionLink>
          </div>
          <div className="text-[14px] text-[#807665]">
            © 2026 ARKANA. Preserving India's Cultural Legacy.
          </div>
        </div>
      </footer>
    </div>
  );
}
