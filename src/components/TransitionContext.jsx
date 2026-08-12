import { createContext, useContext, useState, useCallback } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

const TransitionContext = createContext(null);

export function TransitionProvider({ children }) {
  const navigate = useNavigate();
  const location = useLocation();

  // Wipe transition states
  const [isWipingIn, setIsWipingIn] = useState(false);
  const [isWipingOut, setIsWipingOut] = useState(false);

  // Card expand transition states
  const [isExpanding, setIsExpanding] = useState(false);
  const [isFadingOut, setIsFadingOut] = useState(false);
  const [cardRect, setCardRect] = useState(null);

  const [isTransitioning, setIsTransitioning] = useState(false);

  // Trigger standard Geometric Wipe
  const triggerWipe = useCallback((toPath) => {
    if (isTransitioning || location.pathname === toPath) return;
    setIsTransitioning(true);
    setIsWipingIn(true);

    setTimeout(() => {
      navigate(toPath);
      window.scrollTo(0, 0);
      setIsWipingIn(false);
      setIsWipingOut(true);

      setTimeout(() => {
        setIsWipingOut(false);
        setIsTransitioning(false);
      }, 600);
    }, 450);
  }, [navigate, location.pathname, isTransitioning]);

  // Trigger Expanding Card Transition
  const triggerCardExpand = useCallback((toPath, cardElement) => {
    if (isTransitioning) return;
    setIsTransitioning(true);

    const rect = cardElement.getBoundingClientRect();
    setCardRect(rect);
    setIsExpanding(true);

    // After 450ms, swap route
    setTimeout(() => {
      navigate(toPath);
      window.scrollTo(0, 0);
      setIsFadingOut(true);

      // Fade out the overlay card cover
      setTimeout(() => {
        setIsExpanding(false);
        setIsFadingOut(false);
        setCardRect(null);
        setIsTransitioning(false);
      }, 300);
    }, 450);
  }, [navigate, isTransitioning]);

  return (
    <TransitionContext.Provider
      value={{
        triggerWipe,
        triggerCardExpand,
        isWipingIn,
        isWipingOut,
        isExpanding,
        isFadingOut,
        cardRect,
        isTransitioning,
        currentPath: location.pathname,
      }}
    >
      {children}
    </TransitionContext.Provider>
  );
}

export function useTransition() {
  const context = useContext(TransitionContext);
  if (!context) {
    throw new Error('useTransition must be used within a TransitionProvider');
  }
  return context;
}

export function TransitionLink({ to, className, onClick, children, ...props }) {
  const { triggerWipe } = useTransition();

  const handleClick = (e) => {
    e.preventDefault();
    triggerWipe(to);
    if (onClick) onClick(e);
  };

  return (
    <a href={to} onClick={handleClick} className={className} {...props}>
      {children}
    </a>
  );
}

export function TransitionNavLink({ to, className, activeClassName = 'text-[#6f5100] font-bold', onClick, children, ...props }) {
  const { triggerWipe, currentPath } = useTransition();
  const isActive = currentPath === to;

  const handleClick = (e) => {
    e.preventDefault();
    triggerWipe(to);
    if (onClick) onClick(e);
  };

  const combinedClassName = `${className} ${isActive ? activeClassName : ''}`.trim();

  return (
    <a href={to} onClick={handleClick} className={combinedClassName} {...props}>
      {children}
    </a>
  );
}
