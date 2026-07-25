import ScrollReveal from '../components/ScrollReveal';
import { TransitionLink, useTransition } from '../components/TransitionContext';
import { RELATED_CULTURES, WARLI_ARTIFACTS } from '../data/artifacts';

export default function Culture() {
  const { triggerCardExpand } = useTransition();

  return (
    <main className="pt-20 pb-[120px] bg-[#fbf9f5] min-h-screen text-[#1b1c1a]" aria-label="Warli culture profile">
      {/* Hero */}
      <section className="relative w-full h-[400px] md:h-[500px] overflow-hidden">
        <div
          className="absolute inset-0 bg-cover bg-center"
          style={{
            backgroundImage:
              "url('https://lh3.googleusercontent.com/aida-public/AB6AXuBQcJj6OPcGErQ70_awi8ecdg_yPoPqJXrmA0WQ2j5-ZlZyPCfTqMape0CpngvKTUn6Sw8VTpDhKzbZ-svZv1O4_-kiwp3omF3vkweOebMgbRyIZgFVAODP6gNQM3DXRvzMkvf0PpH3thS8iqRUy7O-o-TKFgXDNGSz9LN3C3JJ_YM7SgE28cQ2QZ8hYOrxxIWW4blLdpd23mjWYrO5IA7TrfkN2q7_SDgIuGb_x4KV3n8ygymUpb8hFcJ1CXTH-Th4-11ywo7qNg')",
          }}
        />
        <div className="absolute inset-0 bg-gradient-to-t from-[#fbf9f5] via-[#fbf9f5]/60 to-transparent" />
        <div className="absolute inset-x-0 bottom-0 max-w-[1280px] mx-auto px-5 md:px-20 pb-12">
          <ScrollReveal>
            <h1 className="font-['Playfair_Display'] text-[40px] md:text-[64px] font-semibold text-[#1b1c1a] mb-2">
              Warli
            </h1>
            <p className="text-[18px] text-[#4e4637]">Maharashtra · 2500 BCE – Present</p>
          </ScrollReveal>
        </div>
      </section>

      {/* About */}
      <section className="max-w-[1280px] mx-auto px-5 md:px-20 py-16 md:py-24">
        <ScrollReveal>
          <div className="flex items-center w-full mb-12">
            <h2 className="font-['Playfair_Display'] text-[14px] font-medium tracking-[0.12em] text-[#1b1c1a] uppercase pr-4 whitespace-nowrap">
              About
            </h2>
            <div className="h-px bg-[#d1c5b2] flex-grow"></div>
          </div>
        </ScrollReveal>

        <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-center">
          <div className="md:col-span-7 text-[18px] text-[#4e4637] leading-[1.7] space-y-6">
            <ScrollReveal>
              <p>
                Warli painting is a form of tribal art mostly created by the tribal people from the North Sahyadri Range in Maharashtra, India. This traditional art form, characterized by its rudimentary graphic vocabulary, uses a circle, a triangle, and a square to represent the world.
              </p>
            </ScrollReveal>
            <ScrollReveal delay={100}>
              <p>
                Unlike other Indian folk art forms, Warli paintings do not depict mythological characters or images of deities. Instead, they portray the social life of the tribal people. Scenes of human figures engaged in hunting, dancing, sowing, and harvesting are common, reflecting a profound harmony with nature.
              </p>
            </ScrollReveal>
          </div>
          <div className="md:col-span-5 aspect-square bg-[#fbf9f5] border border-[#d1c5b2] rounded flex flex-col items-center justify-center relative overflow-hidden group cursor-pointer shadow-[0_1px_3px_rgba(0,0,0,0.06)]">
            <div className="absolute inset-0 bg-[#f5f3ef] opacity-50"></div>
            <span className="material-symbols-outlined text-[#807665] text-5xl mb-3 z-10">3d_rotation</span>
            <span className="text-[12px] font-medium text-[#4e4637] uppercase tracking-widest z-10">
              Interactive 3D Viewer
            </span>
            <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity bg-[#fbf9f5]/85 z-20">
              <span className="text-[16px] text-[#4e4637]">3D Model Loading...</span>
            </div>
          </div>
        </div>
      </section>

      {/* Timeline */}
      <section className="max-w-[1280px] mx-auto px-5 md:px-20 py-16 md:py-24">
        <ScrollReveal>
          <div className="flex items-center w-full mb-12">
            <h2 className="font-['Playfair_Display'] text-[14px] font-medium tracking-[0.12em] text-[#1b1c1a] uppercase pr-4 whitespace-nowrap">
              Timeline
            </h2>
            <div className="h-px bg-[#d1c5b2] flex-grow"></div>
          </div>
        </ScrollReveal>

        <div className="relative border-l border-[#d1c5b2] ml-[5px] md:ml-[11px] space-y-12 pb-8">
          {[
            {
              period: '2500 BCE – 3000 BCE',
              title: 'Origins in Antiquity',
              desc: 'Rooted in ancient traditions, early forms of Warli art are believed to have originated in the Sahyadri ranges. The geometric motifs parallel prehistoric cave paintings.',
            },
            {
              period: '10th Century CE',
              title: 'Establishment of Ritual Practice',
              desc: 'The art form solidifies as a vital component of marriage ceremonies and harvest festivals, painted exclusively by the women of the tribe (Savasinis).',
            },
            {
              period: '1970s',
              title: 'Commercial Introduction',
              desc: 'Jivya Soma Mashe brings global recognition by painting on a daily basis for artistic expression rather than solely for rituals.',
            },
            {
              period: 'Present Day',
              title: 'Global Heritage',
              desc: 'Warli motifs adorn modern fashion, interiors, and digital spaces. Efforts continue to preserve the authentic techniques and intellectual property of the indigenous creators.',
            },
          ].map((event, idx) => (
            <ScrollReveal key={idx} delay={idx * 50}>
              <div className="relative pl-8 md:pl-12 group">
                <div className="absolute w-3 h-3 bg-[#fbf9f5] border border-[#8b6914] rounded-full -left-[6px] top-1.5 transition-colors group-hover:bg-[#8b6914]" />
                <div className="text-[12px] font-medium text-[#8b6914] mb-1">{event.period}</div>
                <h3 className="font-['Playfair_Display'] text-[24px] font-medium text-[#1b1c1a] mb-2">
                  {event.title}
                </h3>
                <p className="text-[16px] text-[#4e4637] leading-[1.6] max-w-2xl">{event.desc}</p>
              </div>
            </ScrollReveal>
          ))}
        </div>
      </section>

      {/* Artifacts Horizontal Scroll */}
      <section className="pl-5 md:pl-20 py-16 md:py-24 overflow-hidden">
        <ScrollReveal>
          <div className="flex items-center w-full mb-12 pr-5 md:pr-20">
            <h2 className="font-['Playfair_Display'] text-[14px] font-medium tracking-[0.12em] text-[#1b1c1a] uppercase pr-4 whitespace-nowrap">
              Artifacts
            </h2>
            <div className="h-px bg-[#d1c5b2] flex-grow"></div>
          </div>
        </ScrollReveal>

        <div className="flex overflow-x-auto no-scrollbar gap-6 pb-8 snap-x pr-5 md:pr-20">
          {WARLI_ARTIFACTS.map((artifact) => (
            <div
              key={artifact.id}
              onClick={(e) => triggerCardExpand('/artifact', e.currentTarget)}
              className="min-w-[280px] w-[280px] bg-white border border-[#d1c5b2] rounded shadow-sm snap-start group overflow-hidden flex flex-col cursor-pointer card-anim-lift"
              role="link"
              tabIndex={0}
              aria-label={`View ${artifact.title}`}
            >
              <div className="h-48 overflow-hidden bg-[#efeeea]">
                <img
                  src={artifact.image}
                  alt={artifact.title}
                  className="w-full h-full object-cover transition-transform duration-[600ms] group-hover:scale-105"
                  loading="lazy"
                />
              </div>
              <div className="p-5">
                <h3 className="text-[16px] text-[#1b1c1a] font-semibold mb-1">{artifact.title}</h3>
                <p className="text-[12px] text-[#4e4637]">{artifact.period}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Related Art Forms */}
      <section className="max-w-[1280px] mx-auto px-5 md:px-20 py-16 md:py-24">
        <ScrollReveal>
          <div className="flex items-center w-full mb-12">
            <h2 className="font-['Playfair_Display'] text-[14px] font-medium tracking-[0.12em] text-[#1b1c1a] uppercase pr-4 whitespace-nowrap">
              Related Art Forms
            </h2>
            <div className="h-px bg-[#d1c5b2] flex-grow"></div>
          </div>
        </ScrollReveal>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {RELATED_CULTURES.map((culture) => (
            <ScrollReveal key={culture.id}>
              <TransitionLink
                to="/culture"
                className="block group bg-white border border-[#d1c5b2] rounded shadow-sm overflow-hidden"
              >
                <div className="h-40 overflow-hidden bg-[#efeeea]">
                  <img
                    src={culture.image}
                    alt={culture.title}
                    className="w-full h-full object-cover transition-transform duration-[600ms] group-hover:scale-105"
                  />
                </div>
                <div className="p-6">
                  <h3 className="font-['Playfair_Display'] text-[20px] font-medium text-[#1b1c1a] mb-1">
                    {culture.title}
                  </h3>
                  <p className="text-[14px] text-[#4e4637] leading-[1.6] line-clamp-2">
                    {culture.description}
                  </p>
                </div>
              </TransitionLink>
            </ScrollReveal>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="max-w-[1280px] mx-auto px-5 md:px-20 py-16 flex justify-center">
        <ScrollReveal>
          <TransitionLink to="/explore" className="inline-flex items-center gap-2 group cursor-pointer">
            <span className="font-['Playfair_Display'] italic text-[28px] md:text-[40px] heritage-link text-[#1b1c1a]">
              Ask Arkana about Warli Art
            </span>
            <span className="material-symbols-outlined text-[#8b6914] transition-transform duration-300 group-hover:translate-x-2">
              arrow_forward
            </span>
          </TransitionLink>
        </ScrollReveal>
      </section>

      {/* FOOTER */}
      <footer className="bg-[#f5f3ef] border-t border-[#d1c5b2] py-16">
        <div className="max-w-[1280px] mx-auto px-5 md:px-20 flex flex-col md:flex-row justify-between items-center gap-8">
          <span className="font-['Playfair_Display'] text-[24px] italic text-[#1b1c1a] opacity-80">
            ARKANA.
          </span>
          <p className="text-[14px] text-[#4e4637]">
            © 2026 ARKANA. Preserving India's Cultural Legacy.
          </p>
          <div className="flex gap-6 text-[14px]">
            <TransitionLink to="/" className="text-[#4e4637] hover:text-[#8b6914] transition-colors">About</TransitionLink>
            <TransitionLink to="/" className="text-[#4e4637] hover:text-[#8b6914] transition-colors">Privacy</TransitionLink>
            <TransitionLink to="/" className="text-[#4e4637] hover:text-[#8b6914] transition-colors">Contact</TransitionLink>
          </div>
        </div>
      </footer>
    </main>
  );
}
