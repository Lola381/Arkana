import { createContext, useContext, useState, useCallback } from 'react';

const CardModalContext = createContext(null);

export function CardModalProvider({ children }) {
  const [modal, setModal] = useState({
    isOpen: false,
    artifact: null,
    originX: '50%',
    originY: '50%',
  });

  /**
   * Open the card modal, anchoring the scale animation to the clicked card.
   * @param {object} artifact - The artifact data object
   * @param {HTMLElement} cardElement - The card DOM element that was clicked
   */
  const openCard = useCallback((artifact, cardElement) => {
    const rect = cardElement.getBoundingClientRect();
    const originX = `${rect.left + rect.width / 2}px`;
    const originY = `${rect.top + rect.height / 2}px`;
    document.body.style.overflow = 'hidden';
    setModal({ isOpen: true, artifact, originX, originY });
  }, []);

  const closeCard = useCallback(() => {
    document.body.style.overflow = '';
    setModal((prev) => ({ ...prev, isOpen: false }));
  }, []);

  return (
    <CardModalContext.Provider value={{ modal, openCard, closeCard }}>
      {children}
    </CardModalContext.Provider>
  );
}

export function useCardModal() {
  const ctx = useContext(CardModalContext);
  if (!ctx) throw new Error('useCardModal must be used within CardModalProvider');
  return ctx;
}
