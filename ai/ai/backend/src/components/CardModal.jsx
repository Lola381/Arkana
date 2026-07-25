import { useEffect, useState, useRef, useCallback } from 'react';
import { createPortal } from 'react-dom';
import { useCardModal } from './CardModalContext';

/**
 * CardModal — Photography Page Transition
 *
 * When any article card is clicked, this modal:
 *  1. Scales from 0 at the card's exact position to fill the screen
 *  2. Reveals an artsy dark background with slow-shifting gradient
 *  3. Shows the artifact image on the left with a live 3D tilt (mouse tracking)
 *  4. Staggers in: type tag → title (slides up) → divider (draws across) →
 *     period → description → action buttons
 *  5. Closes by scaling back to 0 at the same origin
 */
export default function CardModal() {
  const { modal, closeCard } = useCardModal();
  const { isOpen, originX, originY } = modal;

  /* Keep artifact data during close animation */
  const [artifact, setArtifact] = useState(null);
  const [rendered, setRendered] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const [contentIn, setContentIn] = useState(false);

  const imgRef = useRef(null);
  const t1 = useRef(null);
  const t2 = useRef(null);
  const t3 = useRef(null);

  useEffect(() => {
    if (isOpen && modal.artifact) {
      setArtifact(modal.artifact);
      setRendered(true);
      clearTimeout(t1.current);
      clearTimeout(t2.current);
      clearTimeout(t3.current);
      /* Double rAF: ensure DOM has rendered before triggering transition */
      t1.current = requestAnimationFrame(() =>
        requestAnimationFrame(() => setExpanded(true))
      );
      t2.current = setTimeout(() => setContentIn(true), 520);
    } else {
      /* Trigger close animation */
      setExpanded(false);
      setContentIn(false);
      t3.current = setTimeout(() => setRendered(false), 700);
    }
    return () => {
      clearTimeout(t2.current);
      clearTimeout(t3.current);
    };
  }, [isOpen]);

  /* Keyboard close */
  useEffect(() => {
    const onKey = (e) => { if (e.key === 'Escape') closeCard(); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [closeCard]);

  /* 3D tilt on the artifact image */
  const handleImgMove = useCallback((e) => {
    const img = imgRef.current;
    if (!img) return;
    const r = img.getBoundingClientRect();
    const dx = e.clientX - r.left - r.width / 2;
    const dy = e.clientY - r.top - r.height / 2;
    const rx = (dy / r.height) * -10;
    const ry = (dx / r.width) * 10;
    img.style.transform = `perspective(600px) rotateX(${rx}deg) rotateY(${ry}deg) scale(1.03)`;
  }, []);

  const handleImgLeave = useCallback(() => {
    if (imgRef.current) imgRef.current.style.transform = '';
  }, []);

  if (!rendered || !artifact) return null;

  return createPortal(
    <div
      className={`card-modal${expanded ? ' card-modal--open' : ''}`}
      style={{ '--origin-x': originX, '--origin-y': originY }}
      role="dialog"
      aria-modal="true"
      aria-label={`${artifact.title} detail`}
    >
      {/* Artsy animated gradient background */}
      <div className="card-modal__bg" aria-hidden="true" />

      {/* Close button */}
      <button
        className={`card-modal__close${contentIn ? ' card-modal__close--in' : ''}`}
        onClick={closeCard}
        aria-label="Close"
      >
        ✕
      </button>

      {/* Two-column layout */}
      <div className="card-modal__inner">

        {/* Left — large image with 3D tilt */}
        <div className={`card-modal__img-side${contentIn ? ' card-modal__img-side--in' : ''}`}>
          <div className="card-modal__img-frame">
            <img
              ref={imgRef}
              src={artifact.image}
              alt={artifact.title}
              className="card-modal__img"
              onMouseMove={handleImgMove}
              onMouseLeave={handleImgLeave}
              draggable={false}
            />
          </div>
        </div>

        {/* Right — staggered content */}
        <div className={`card-modal__content${contentIn ? ' card-modal__content--in' : ''}`}>

          {/* Type badge */}
          <div className="card-modal__copy-wrap">
            <span className="card-modal__type">{artifact.type}</span>
          </div>

          {/* Title — slides up */}
          <div className="card-modal__copy-wrap">
            <h2 className="card-modal__title">{artifact.title}</h2>
          </div>

          {/* Divider — draws across */}
          <div className="card-modal__divider" />

          {/* Period */}
          <div className="card-modal__copy-wrap">
            <p className="card-modal__period">{artifact.period}</p>
          </div>

          {/* Description (if available) */}
          {artifact.description && (
            <div className="card-modal__copy-wrap">
              <p className="card-modal__description">{artifact.description}</p>
            </div>
          )}

          {/* Action buttons */}
          <div className="card-modal__actions">
            <button
              className="card-modal__btn card-modal__btn--ghost"
              onClick={closeCard}
            >
              ← Return
            </button>
            <button className="card-modal__btn card-modal__btn--gold">
              View Full Details
            </button>
          </div>
        </div>
      </div>
    </div>,
    document.body
  );
}
