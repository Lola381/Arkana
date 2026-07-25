import { useState } from 'react';
import { useTransition } from './TransitionContext';

/**
 * ProfileCard — Effect #6: Expanding Profile Card (Poster → Profile)
 *
 * HTML structure matches the CodePen reference exactly:
 *   .profile-card[.profile-card--dark]
 *     img
 *     section
 *       h2
 *       p
 *       div
 *         .pc-tag
 *         button[.pc-following]
 *
 * The frosted-glass overlay is handled by CSS ::before.
 * The + → − icon is handled by CSS button::before / button::after.
 */
export default function ProfileCard({ artifact, dark = false }) {
  const [following, setFollowing] = useState(false);
  const { triggerCardExpand } = useTransition();

  const handleFollow = (e) => {
    e.stopPropagation();
    setFollowing((prev) => !prev);
  };

  return (
    <div
      className={`profile-card${dark ? ' profile-card--dark' : ''}`}
      onClick={(e) => triggerCardExpand('/artifact', e.currentTarget)}
      role="button"
      tabIndex={0}
      aria-label={`View ${artifact.title}`}
    >
      {/* Poster image — direct child so CSS ::before sits over it */}
      <img
        src={artifact.image}
        alt={artifact.title}
        loading="lazy"
      />

      {/* Content section — direct child, 33% of card height */}
      <section>
        <h2>{artifact.title}</h2>

        <p>{artifact.description}</p>

        {/* Footer row: saves tag + follow button */}
        <div>
          <div className="pc-tag" aria-label={`${artifact.followers ?? '2.4k'} saves`}>
            <span className="material-symbols-outlined">bookmark</span>
            {artifact.followers ?? '2.4k'}
          </div>

          <button
            className={following ? 'pc-following' : ''}
            onClick={handleFollow}
            aria-pressed={following}
          >
            {following ? 'Saved' : 'Save'}
          </button>
        </div>
      </section>
    </div>
  );
}
