import { useEffect, useRef } from 'react';

/**
 * GlobalCursor — the circular "Read" cursor that follows the mouse
 * across ALL .article-card elements site-wide.
 *
 * - Tracks pointermove on window for position
 * - Shows/hides based on whether the pointer is over an .article-card
 * - Alternates color (pink/purple vs teal) by card index in the DOM
 */
export default function GlobalCursor() {
  const cursorRef = useRef(null);

  useEffect(() => {
    const cursor = cursorRef.current;
    if (!cursor) return;

    const onMove = (e) => {
      cursor.style.left = `${e.clientX}px`;
      cursor.style.top = `${e.clientY}px`;
    };

    const onOver = (e) => {
      const card = e.target.closest('.article-card');
      if (card) {
        cursor.classList.add('global-cursor--active');
        /* Alternate hue by card's DOM position */
        const allCards = [...document.querySelectorAll('.article-card')];
        const idx = allCards.indexOf(card);
        cursor.style.background = idx % 2 === 0
          ? 'hsl(330, 60%, 58%)'   /* pink/purple */
          : 'hsl(210, 65%, 55%)';  /* teal/blue   */
      } else {
        cursor.classList.remove('global-cursor--active');
      }
    };

    window.addEventListener('pointermove', onMove, { passive: true });
    window.addEventListener('pointerover', onOver, { passive: true });

    return () => {
      window.removeEventListener('pointermove', onMove);
      window.removeEventListener('pointerover', onOver);
    };
  }, []);

  return (
    <div ref={cursorRef} className="global-cursor" aria-hidden="true">
      Read
    </div>
  );
}
