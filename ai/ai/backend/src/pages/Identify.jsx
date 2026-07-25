import { useState, useEffect, useRef } from 'react';
import ScrollReveal from '../components/ScrollReveal';
import { TransitionLink, useTransition } from '../components/TransitionContext';
import { SIMILAR_ARTIFACTS } from '../data/artifacts';

export default function Identify() {
  const [barWidth, setBarWidth] = useState('0%');
  const { triggerCardExpand } = useTransition();
  const cardRefs = useRef([]);

  useEffect(() => {
    // Animate confidence bar after mount
    const timer = setTimeout(() => {
      setBarWidth('87%');
    }, 500);
    return () => clearTimeout(timer);
  }, []);

  const handleMouseMove = (e, idx) => {
    const card = cardRefs.current[idx];
    if (!card) return;
    const rect = card.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;
    const rotateY = ((e.clientX - centerX) / rect.width) * 6;
    const rotateX = ((centerY - e.clientY) / rect.height) * 4;
    card.style.transform = `perspective(800px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale(1.02)`;
  };

  const handleMouseLeave = (idx) => {
    const card = cardRefs.current[idx];
    if (card) {
      card.style.transform = '';
    }
  };

  return (
    <main className="flex-grow w-full max-w-[1280px] mx-auto px-5 md:px-20 py-16 md:py-[120px] pt-[120px] bg-[#fbf9f5] text-[#1b1c1a]" aria-label="Visual artifact identification">
      <header className="mb-24 text-center max-w-3xl mx-auto">
        <ScrollReveal>
          <div className="flex items-center justify-center gap-4 mb-8">
            <div className="h-[1px] bg-[#d1c5b2] w-12"></div>
            <span className="font-['Playfair_Display'] text-[14px] font-medium uppercase tracking-widest text-[#4e4637]">
              IDENTIFY
            </span>
            <div className="h-[1px] bg-[#d1c5b2] w-12"></div>
          </div>
          <h1 className="font-['Playfair_Display'] text-[40px] md:text-[64px] font-semibold text-[#1b1c1a] mb-6 leading-tight">
            Upload an artifact to discover its story
          </h1>
          <p className="text-[18px] text-[#4e4637] leading-[1.6] max-w-2xl mx-auto">
            Our visual intelligence system analyzes physical characteristics, patterns, and materials to connect fragments of history to their broader cultural narrative.
          </p>
        </ScrollReveal>
      </header>

      {/* Upload Zone */}
      <section className="mb-32 flex justify-center" aria-label="Upload zone">
        <ScrollReveal>
          <label
            htmlFor="artifact-upload"
            className="w-full max-w-[480px] aspect-[4/3] border border-dashed border-[#d1c5b2] bg-white flex flex-col items-center justify-center p-8 hover:border-[#8b6914] transition-colors duration-300 cursor-pointer group rounded shadow-sm"
            role="button"
            aria-label="Upload artifact image"
          >
            <span className="material-symbols-outlined text-4xl text-[#4e4637] mb-4 group-hover:text-[#8b6914] transition-colors duration-300">
              photo_camera
            </span>
            <p className="text-[18px] font-medium text-[#1b1c1a]">Drag an image here</p>
            <p className="text-[12px] text-[#4e4637] mt-2 font-medium tracking-wide uppercase">or click to browse from your device</p>
            <button
              type="button"
              className="mt-6 px-6 py-3 border border-[#1b1c1a] rounded font-semibold text-[14px] text-[#1b1c1a] hover:bg-[#1b1c1a] hover:text-[#fbf9f5] transition-all duration-300"
            >
              Select Artifact
            </button>
            <input type="file" id="artifact-upload" accept="image/*" className="sr-only" aria-hidden="true" />
          </label>
        </ScrollReveal>
      </section>

      {/* Results (example state) */}
      <section className="mb-32" aria-label="Identification results">
        <div className="flex flex-col md:flex-row gap-6">
          <div className="w-full md:w-5/12">
            <ScrollReveal>
              <div className="bg-white rounded border border-[#d1c5b2] p-2 shadow-sm">
                <img
                  src="https://lh3.googleusercontent.com/aida-public/AB6AXuCa0bQsVMb3c8k7JaLCWbMSrisQEvW2a804GQzSmy0F727je-dthytTEPeCsdghJT3m08vfu3WW8AUWgkikSphZ_cV9iAcUxpUTO413C_-N6KEcsJahj-XVfqsEG2SdhvvZkr4G3iYGZg6ELNDe80n6IFNcKx4EKmuL6BAPsxNT6nl_J4ugDe2QJSVv6V553yd1n0AWgsDgoCRzkyCSYI6iwZQlLTnbeDGOlCYJAy792K48UASx3PticROPkgCeCOd3crvTcmSXyA"
                  alt="Uploaded Warli art artifact"
                  className="w-full h-auto object-cover rounded-sm"
                />
              </div>
            </ScrollReveal>
          </div>
          <div className="w-full md:w-7/12 flex flex-col justify-center px-4 md:px-8">
            <ScrollReveal delay={100}>
              <div className="flex items-center gap-4 mb-6">
                <span className="font-['Playfair_Display'] text-[14px] font-medium uppercase tracking-widest text-[#8b6914]">
                  IDENTIFIED AS
                </span>
                <div className="h-[1px] bg-[#d1c5b2] flex-grow"></div>
              </div>
              <h2 className="font-['Playfair_Display'] text-[32px] font-medium text-[#1b1c1a] mb-4">
                Warli Art
              </h2>
              <p className="text-[18px] text-[#4e4637] mb-8 leading-relaxed">
                Characterized by rudimentary geometric vocabulary: a circle, triangle and square. These paintings are predominantly created by tribal women to depict daily life, nature, and social events.
              </p>
            </ScrollReveal>

            {/* Confidence meter */}
            <ScrollReveal delay={150}>
              <div className="mb-8">
                <div className="flex justify-between items-end mb-2">
                  <span className="text-[12px] font-medium text-[#4e4637] uppercase tracking-wide">
                    Analysis Confidence
                  </span>
                  <span className="text-[16px] font-semibold text-[#8b6914]">87%</span>
                </div>
                <div className="h-1.5 w-full bg-[#e4e2de] overflow-hidden rounded-full">
                  <div
                    className="h-full bg-[#8b6914] rounded-full transition-all duration-[1200ms] ease-[cubic-bezier(0.16,1,0.3,1)]"
                    style={{ width: barWidth }}
                  />
                </div>
              </div>
            </ScrollReveal>

            {/* Tags */}
            <ScrollReveal delay={200}>
              <div className="flex flex-wrap gap-3 mb-10">
                {['Maharashtra', 'Tribal', 'Geometric', 'Pigment on Mud'].map((tag) => (
                  <span
                    key={tag}
                    className="px-4 py-1.5 border border-[#d1c5b2] rounded-full text-[12px] font-medium text-[#4e4637]"
                  >
                    {tag}
                  </span>
                ))}
              </div>
              <TransitionLink
                to="/explore"
                className="text-[#8b6914] font-medium text-[16px] heritage-link group inline-flex items-center gap-2"
              >
                Explore Warli on Map
                <span className="material-symbols-outlined text-[14px] transition-transform group-hover:translate-x-1">
                  arrow_forward
                </span>
              </TransitionLink>
            </ScrollReveal>
          </div>
        </div>
      </section>

      {/* Similar Artifacts (Tilt Card Showcase) */}
      <section className="mb-32" aria-label="Similar artifacts">
        <ScrollReveal>
          <div className="flex items-center gap-4 mb-12">
            <span className="font-['Playfair_Display'] text-[14px] font-medium tracking-[0.12em] text-[#1b1c1a] uppercase">
              SIMILAR ARTIFACTS
            </span>
            <div className="h-[1px] bg-[#d1c5b2] flex-grow"></div>
          </div>
        </ScrollReveal>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {SIMILAR_ARTIFACTS.map((artifact, idx) => (
            <ScrollReveal key={artifact.id} delay={idx * 50}>
              <div
                ref={(el) => (cardRefs.current[idx] = el)}
                onClick={(e) => triggerCardExpand('/artifact', e.currentTarget)}
                onMouseMove={(e) => handleMouseMove(e, idx)}
                onMouseLeave={() => handleMouseLeave(idx)}
                className="card-anim-tilt bg-white rounded border border-[#d1c5b2] shadow-sm overflow-hidden group cursor-pointer"
                role="link"
                tabIndex={0}
                aria-label={`View ${artifact.title}`}
              >
                <div className="aspect-square relative overflow-hidden bg-[#fbf9f5]">
                  <img
                    src={artifact.image}
                    alt={artifact.title}
                    className="w-full h-full object-cover transition-transform duration-[600ms] group-hover:scale-105"
                  />
                  <div className="absolute top-3 right-3 bg-white/90 backdrop-blur-sm px-2 py-1 rounded border border-[#d1c5b2]/30 z-10">
                    <span className="text-[12px] font-semibold text-[#8b6914]">{artifact.match}</span>
                  </div>
                </div>
                <div className="p-5 relative z-[3] bg-white">
                  <h3 className="text-[16px] font-semibold text-[#1b1c1a] mb-1">{artifact.title}</h3>
                  <p className="text-[12px] text-[#4e4637]">{artifact.location}</p>
                </div>
              </div>
            </ScrollReveal>
          ))}
        </div>
      </section>

      {/* Cultural Context */}
      <section className="mb-16" aria-label="Cultural context">
        <ScrollReveal>
          <div className="flex items-center gap-4 mb-12">
            <span className="font-['Playfair_Display'] text-[14px] font-medium tracking-[0.12em] text-[#1b1c1a] uppercase">
              CULTURAL CONTEXT
            </span>
            <div className="h-[1px] bg-[#d1c5b2] flex-grow"></div>
          </div>
        </ScrollReveal>

        <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
          <div className="md:col-span-8 bg-[#f5f3ef] p-8 md:p-12 border border-[#d1c5b2]/50">
            <ScrollReveal>
              <h3 className="font-['Playfair_Display'] text-[28px] font-medium text-[#1b1c1a] mb-6">
                The Language of Shapes
              </h3>
              <p className="text-[18px] text-[#4e4637] leading-[1.7] mb-6">
                Unlike other Indian folk art forms, Warli painting does not depict mythological characters or images of deities. Instead, it relies on a strict geometric vocabulary to depict social life. The circle represents the sun and the moon, while the triangle is derived from mountains and pointed trees.
              </p>
              <p className="text-[16px] text-[#4e4637] leading-[1.6]">
                The ritualistic paintings are usually created on the inside walls of village huts. The walls are made of a mixture of branches, earth, and red brick that make a red ochre background for the paintings. The white pigment is made from a mixture of rice paste and water.
              </p>
            </ScrollReveal>
          </div>
          <div className="md:col-span-4 flex flex-col justify-center items-start p-8">
            <ScrollReveal delay={100}>
              <div className="w-16 h-16 rounded-full bg-[#e4e2de] flex items-center justify-center mb-6">
                <span className="material-symbols-outlined text-3xl text-[#4e4637]">auto_awesome</span>
              </div>
              <h4 className="text-[16px] font-semibold text-[#1b1c1a] mb-2">Automated Analysis</h4>
              <p className="text-[12px] text-[#4e4637] mb-8 leading-relaxed">
                Our vision model is trained on over 50,000 verified archival images across 200 distinct Indian cultural regions.
              </p>
              <a
                href="#"
                onClick={(e) => e.preventDefault()}
                className="text-[#8b6914] font-medium text-[16px] heritage-link group inline-flex items-center gap-2"
              >
                View Methodology
                <span className="material-symbols-outlined text-[14px] transition-transform group-hover:translate-x-1">
                  arrow_forward
                </span>
              </a>
            </ScrollReveal>
          </div>
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
          <p className="text-[14px] text-[#4e4637]">
            © 2026 ARKANA. Preserving India's Cultural Legacy.
          </p>
        </div>
      </footer>
    </main>
  );
}
