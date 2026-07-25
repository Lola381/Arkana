import ScrollReveal from '../components/ScrollReveal';
import { TransitionLink, useTransition } from '../components/TransitionContext';
import { RELATED_ARTIFACTS } from '../data/artifacts';

export default function ArtifactDetail() {
  const { triggerCardExpand } = useTransition();

  return (
    <main className="flex-grow pt-[120px] pb-[120px] px-5 md:px-20 max-w-[1280px] mx-auto w-full bg-[#fbf9f5] text-[#1b1c1a]" aria-label="Artifact detail: Dancing Nataraja">
      {/* Back link */}
      <div className="mb-12">
        <TransitionLink
          to="/browse"
          className="inline-flex items-center gap-2 text-[12px] font-medium text-[#5f5e5e] hover:text-[#1b1c1a] transition-colors heritage-link"
        >
          <span className="material-symbols-outlined text-[16px]">arrow_left_alt</span>
          Back to Collection
        </TransitionLink>
      </div>

      {/* 2-column layout */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-6 mb-[120px]">
        {/* Left: Image viewer */}
        <div className="md:col-span-7 lg:col-span-8">
          <ScrollReveal>
            <div className="bg-white rounded-xl border border-[#d1c5b2] p-4 md:p-8 aspect-square md:aspect-[4/3] flex items-center justify-center relative shadow-[0_1px_3px_rgba(0,0,0,0.06)] overflow-hidden group">
              <img
                src="https://lh3.googleusercontent.com/aida-public/AB6AXuDmDCaEGkvCRPYfmQ9Nzv6QglL0LySW4t_Ulyd9HUT79YF2jptyo9OF32P2Ljh1ew3ucySvtFtW-jvYvRd_tPfN3QFbK44iMuc3xsKcyW0pgHvX52dNmM3pYhHUXhOwCO6W4MKfnuQ-vR1i_WacWVkXftvpHPdAposq0KfWtKVaLWy5gb3GKbCbkfVfxzpVhWT5EYOodoTGjirVlzJJdSZeb0Yt9p1U2B_-UZNE4Ahr1_XJUtkDZYiMRaOpxAuNdtcSmD1g9cEhQg"
                alt="Dancing Nataraja bronze sculpture, Chola Dynasty 11th century"
                className="w-full h-full object-contain transition-transform duration-700 ease-in-out group-hover:scale-[1.02]"
              />
              <div className="absolute bottom-4 right-4 flex gap-2">
                <button
                  className="w-10 h-10 bg-white/90 backdrop-blur rounded border border-[#d1c5b2] flex items-center justify-center text-[#1b1c1a] hover:text-[#8b6914] transition-colors shadow-sm"
                  aria-label="View 360 degrees"
                >
                  <span className="material-symbols-outlined text-[20px]">360</span>
                </button>
                <button
                  className="w-10 h-10 bg-white/90 backdrop-blur rounded border border-[#d1c5b2] flex items-center justify-center text-[#1b1c1a] hover:text-[#8b6914] transition-colors shadow-sm"
                  aria-label="Zoom in"
                >
                  <span className="material-symbols-outlined text-[20px]">zoom_in</span>
                </button>
              </div>
            </div>
          </ScrollReveal>
        </div>

        {/* Right: Metadata */}
        <div className="md:col-span-5 lg:col-span-4 flex flex-col pt-4 md:pt-0">
          <ScrollReveal delay={100}>
            <div className="mb-8">
              <p className="text-[12px] font-medium text-[#8b6914] uppercase tracking-wider mb-2">11th Century CE</p>
              <h1 className="font-['Playfair_Display'] text-[32px] font-medium text-[#1b1c1a] mb-2 leading-tight">
                Dancing Nataraja
              </h1>
              <p className="text-[18px] text-[#4e4637] mb-1">Chola Dynasty</p>
              <p className="text-[16px] text-[#5f5e5e]">National Museum, New Delhi</p>
            </div>
          </ScrollReveal>

          <ScrollReveal delay={150}>
            <div className="flex items-center gap-4 mb-6">
              <span className="font-['Playfair_Display'] text-[14px] font-medium tracking-[0.12em] text-[#807665] uppercase">
                ABOUT
              </span>
              <div className="h-px bg-[#d1c5b2] flex-grow"></div>
            </div>
            <div className="text-[16px] text-[#4e4637] space-y-4 mb-8 leading-relaxed">
              <p>
                The Nataraja, the Lord of the Dance, represents the Hindu god Shiva performing the divine dance to destroy a weary universe and make preparations for god Brahma to start the process of creation.
              </p>
              <p>
                Cast in bronze during the illustrious Chola period, this iconography became the quintessential representation of Hindu artistic achievement, balancing intricate metallurgy with profound spiritual geometry.
              </p>
            </div>
          </ScrollReveal>

          <ScrollReveal delay={200}>
            <div className="flex flex-wrap gap-4 mt-auto">
              <button className="px-6 py-3 border border-[#1b1c1a] rounded font-semibold text-[12px] text-[#1b1c1a] hover:bg-[#1b1c1a] hover:text-[#fbf9f5] transition-all duration-300 flex items-center gap-2">
                <span className="material-symbols-outlined text-[18px]">bookmark_border</span> Bookmark
              </button>
              <TransitionLink
                to="/explore"
                className="px-6 py-3 border border-[#d1c5b2] rounded font-semibold text-[12px] text-[#1b1c1a] hover:border-[#1b1c1a] transition-all duration-300 flex items-center gap-2"
              >
                <span className="material-symbols-outlined text-[18px]">location_on</span> View on Map
              </TransitionLink>
            </div>
          </ScrollReveal>
        </div>
      </div>

      {/* Cultural Significance */}
      <section className="mb-[120px]">
        <ScrollReveal>
          <div className="flex items-center gap-4 mb-12">
            <span className="font-['Playfair_Display'] text-[14px] font-medium tracking-[0.12em] text-[#807665] uppercase">
              CULTURAL SIGNIFICANCE
            </span>
            <div className="h-px bg-[#d1c5b2] flex-grow"></div>
          </div>
        </ScrollReveal>

        <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
          <div className="md:col-span-8 md:col-start-3 text-[18px] text-[#4e4637] leading-[1.7]">
            <ScrollReveal>
              <p className="mb-6">
                The symbolism of Siva Nataraja is religion, art, and science merged as one. In God's endless dance of creation, preservation, destruction, and paired graces is hidden a deep understanding of our universe.{' '}
                <sup className="text-[#8b6914] text-xs cursor-pointer">[1]</sup>
              </p>
            </ScrollReveal>
            <ScrollReveal delay={50}>
              <p className="mb-6">
                The upper right hand holds the damaru (drum), representing creation. The upper left holds agni (fire), representing destruction. The lower right hand is in abhaya mudra (gesture of fearlessness). The lower left hand points to the raised foot, signaling liberation.{' '}
                <sup className="text-[#8b6914] text-xs cursor-pointer">[2]</sup>
              </p>
            </ScrollReveal>
            <ScrollReveal delay={100}>
              <div className="bg-[#f5f3ef] p-6 rounded-lg border-l-4 border-l-[#8b6914] border border-[#d1c5b2] mt-8 text-[16px] italic leading-relaxed">
                "The dance of Shiva is the dancing universe; the ceaseless flow of energy going through an infinite variety of patterns that melt into one another."<br />
                <span className="text-[#5f5e5e] block mt-2 not-italic text-sm">— Fritjof Capra, The Tao of Physics</span>
              </div>
            </ScrollReveal>
          </div>
        </div>
      </section>

      {/* Related Artifacts */}
      <section className="mb-[120px]">
        <ScrollReveal>
          <div className="flex items-center gap-4 mb-12">
            <span className="font-['Playfair_Display'] text-[14px] font-medium tracking-[0.12em] text-[#807665] uppercase">
              RELATED ARTIFACTS
            </span>
            <div className="h-px bg-[#d1c5b2] flex-grow"></div>
          </div>
        </ScrollReveal>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {RELATED_ARTIFACTS.map((artifact) => (
            <ScrollReveal key={artifact.id}>
              <div
                onClick={(e) => triggerCardExpand('/artifact', e.currentTarget)}
                className="bg-white rounded-lg border border-[#d1c5b2] overflow-hidden shadow-sm block cursor-pointer group card-anim-lift"
                role="link"
                tabIndex={0}
                aria-label={`View ${artifact.title}`}
              >
                <div className="aspect-square bg-[#f5f3ef] overflow-hidden">
                  <img
                    src={artifact.image}
                    alt={artifact.title}
                    className="w-full h-full object-cover transition-transform duration-[600ms] group-hover:scale-105"
                  />
                </div>
                <div className="p-5">
                  <p className="text-[12px] text-[#5f5e5e] uppercase mb-1">{artifact.type}</p>
                  <h3 className="font-['Playfair_Display'] text-[18px] text-[#1b1c1a] font-medium mb-1">
                    {artifact.title}
                  </h3>
                  <p className="text-[14px] text-[#4e4637] line-clamp-2 leading-relaxed">
                    {artifact.description}
                  </p>
                </div>
              </div>
            </ScrollReveal>
          ))}
        </div>
      </section>

      {/* FOOTER */}
      <footer className="bg-[#f5f3ef] border-t border-[#d1c5b2] py-16 -mx-5 md:-mx-20 px-5 md:px-20">
        <div className="max-w-[1280px] mx-auto flex flex-col md:flex-row justify-between items-center gap-8">
          <span className="font-['Playfair_Display'] text-[24px] italic text-[#1b1c1a] opacity-80">
            ARKANA.
          </span>
          <div className="flex gap-6 text-[14px]">
            <TransitionLink to="/" className="text-[#4e4637] hover:text-[#8b6914] transition-colors">About</TransitionLink>
            <TransitionLink to="/" className="text-[#4e4637] hover:text-[#8b6914] transition-colors">Privacy</TransitionLink>
            <TransitionLink to="/" className="text-[#4e4637] hover:text-[#8b6914] transition-colors">Contact</TransitionLink>
          </div>
          <p className="text-[14px] text-[#5f5e5e]">
            © 2026 ARKANA. Preserving India's Cultural Legacy.
          </p>
        </div>
      </footer>
    </main>
  );
}
