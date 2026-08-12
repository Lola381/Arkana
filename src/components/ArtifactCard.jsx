import { useCallback } from 'react';
import { useCardModal } from './CardModalContext';

/**
 * ArtifactCard — universal card component used on Home, Explore, Browse, Culture.
 *
 * Uses the "Article Hover Reveal" style (Effect #5):
 *   - Image with gradient overlay
 *   - Type badge + title with animated underline
 *   - Period text
 *   - Custom global cursor hides the browser cursor (cursor: none)
 *
 * On click, opens the CardModal (Photography Page Transition).
 *
 * Props:
 *   artifact — { id, title, type, period, description, image }
 *   index    — card index for stagger offset (even cards sit lower)
 */
export default function ArtifactCard({ artifact, index = 0 }) {
  const { openCard } = useCardModal();

  const handleClick = useCallback((e) => {
    openCard(artifact, e.currentTarget);
  }, [artifact, openCard]);

  const isEven = index % 2 === 0;

  return (
    <article
      className={`article-card${isEven ? ' article-card--even' : ''}`}
      onClick={handleClick}
      role="button"
      tabIndex={0}
      aria-label={`View ${artifact.title}`}
      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') handleClick(e); }}
    >
      {/* Image */}
      <div className="article-card__image-wrap">
        <img
          src={artifact.image}
          alt={artifact.title}
          className="article-card__image"
          loading="lazy"
        />
      </div>

      {/* Full-card gradient overlay with text */}
      <div className="article-card__link" aria-hidden="true">
        <div className="article-card__body">
          <span className="article-card__type">{artifact.type ?? ''}</span>
          <h3 className="article-card__title">
            {artifact.title}
            <span className="article-card__underline" />
          </h3>
          <span className="article-card__author">{artifact.period ?? ''}</span>
        </div>
      </div>
    </article>
  );
}
