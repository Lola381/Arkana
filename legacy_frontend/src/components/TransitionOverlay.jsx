import { useEffect, useState } from 'react';
import { useTransition } from './TransitionContext';

export default function TransitionOverlay() {
  const {
    isWipingIn,
    isWipingOut,
    isExpanding,
    isFadingOut,
    cardRect,
  } = useTransition();

  const [isExpanded, setIsExpanded] = useState(false);

  useEffect(() => {
    if (isExpanding && cardRect) {
      const id = requestAnimationFrame(() => {
        setIsExpanded(true);
      });
      return () => cancelAnimationFrame(id);
    } else {
      setIsExpanded(false);
    }
  }, [isExpanding, cardRect]);

  // Compute styles for Expanding Card overlay
  let cardCoverStyle = {};
  if (isExpanding && cardRect) {
    if (!isExpanded) {
      cardCoverStyle = {
        position: 'fixed',
        top: `${cardRect.top}px`,
        left: `${cardRect.left}px`,
        width: `${cardRect.width}px`,
        height: `${cardRect.height}px`,
        opacity: 1,
        borderRadius: '4px',
        background: '#ffffff',
        border: '1px solid #d1c5b2',
        zIndex: 9999,
        pointerEvents: 'none',
      };
    } else {
      cardCoverStyle = {
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100vw',
        height: '100vh',
        opacity: isFadingOut ? 0 : 1,
        borderRadius: 0,
        background: '#ffffff',
        zIndex: 9999,
        pointerEvents: 'none',
        transition: isFadingOut
          ? 'opacity 300ms ease'
          : 'all 500ms cubic-bezier(0.16, 1, 0.3, 1)',
      };
    }
  }

  return (
    <>
      {/* Geometric Wipe Transition Overlay */}
      <div
        className={`wipe-overlay ${isWipingIn ? 'wipe-in' : ''} ${isWipingOut ? 'wipe-out' : ''}`}
        aria-hidden="true"
      >
        <div className="wipe-piece"></div>
        <div className="wipe-piece"></div>
        <div className="wipe-piece"></div>
        <div className="wipe-piece"></div>
      </div>

      {/* Expanding Card Cover Overlay */}
      {isExpanding && cardRect && (
        <div style={cardCoverStyle} aria-hidden="true" />
      )}
    </>
  );
}
