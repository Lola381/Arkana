import { useCallback } from 'react';
import { useCardModal } from './CardModalContext';

/**
 * ArticleCard — used on the Browse page article grid.
 * Same hover-reveal style as ArtifactCard; opens CardModal on click.
 */
export default function ArticleCard({ article, index = 0 }) {
  const { openCard } = useCardModal();
  const isEven = index % 2 === 0;

  const handleClick = useCallback((e) => {
    openCard(article, e.currentTarget);
  }, [article, openCard]);

  return (
    <article
      className={`article-card${isEven ? ' article-card--even' : ''}`}
      onClick={handleClick}
      role="button"
      tabIndex={0}
      aria-label={`View ${article.title}`}
      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') handleClick(e); }}
    >
      <div className="article-card__image-wrap">
        <img
          src={article.image}
          alt={article.title}
          className="article-card__image"
          loading="lazy"
        />
      </div>

      <div className="article-card__link" aria-hidden="true">
        <div className="article-card__body">
          <span className="article-card__type">{article.type ?? ''}</span>
          <h3 className="article-card__title">
            {article.title}
            <span className="article-card__underline" />
          </h3>
          <span className="article-card__author">{article.period ?? ''}</span>
        </div>
      </div>
    </article>
  );
}
