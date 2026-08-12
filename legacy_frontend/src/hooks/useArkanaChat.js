import { useState, useCallback, useRef } from 'react';
import { findResponse } from '../data/chatResponses';

/**
 * useArkanaChat
 *
 * Custom hook that drives the "Ask Arkana" chat panel on the Explore page.
 * Simulates the RAG pipeline output format:
 *   - Token-by-token streaming animation
 *   - Citation rendering
 *   - Insight card attachment
 *   - Map pin highlight events via onMapEvent callback
 *
 * @param {Function} onMapEvent  — called with { pinId, label } when NER fires
 */
export function useArkanaChat(onMapEvent, onResponseFound) {
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      sender: 'ai',
      text: "Welcome to the archive. I can help you explore any aspect of India's cultural heritage — from ancient Mauryan sculptures to contemporary folk traditions. What would you like to discover?",
      citation: null,
      source: null,
      insightCard: null,
      isStreaming: false,
    },
  ]);
  const [isTyping, setIsTyping] = useState(false);
  const [inputVal, setInputVal] = useState('');
  const streamRef = useRef(null);

  /**
   * Stream text character-by-character into an existing message.
   * Faster at start, then natural typing speed.
   */
  const streamText = useCallback((id, fullText, onDone) => {
    let charIndex = 0;
    const INITIAL_BURST = 60; // chars to show instantly before per-char streaming
    const MIN_DELAY = 8;
    const MAX_DELAY = 22;

    // Show the first N chars instantly for responsiveness
    setMessages((prev) =>
      prev.map((m) =>
        m.id === id ? { ...m, text: fullText.slice(0, INITIAL_BURST) } : m
      )
    );
    charIndex = INITIAL_BURST;

    const tick = () => {
      if (charIndex >= fullText.length) {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === id ? { ...m, text: fullText, isStreaming: false } : m
          )
        );
        onDone?.();
        return;
      }
      // Slow down slightly at punctuation for natural feel
      const char = fullText[charIndex];
      const delay =
        ['.', '!', '?', '\n'].includes(char)
          ? MAX_DELAY * 5
          : Math.random() * (MAX_DELAY - MIN_DELAY) + MIN_DELAY;

      charIndex++;
      setMessages((prev) =>
        prev.map((m) =>
          m.id === id ? { ...m, text: fullText.slice(0, charIndex) } : m
        )
      );
      streamRef.current = setTimeout(tick, delay);
    };

    if (charIndex < fullText.length) {
      streamRef.current = setTimeout(tick, MIN_DELAY);
    } else {
      onDone?.();
    }
  }, []);

  const sendMessage = useCallback(
    (text) => {
      const trimmed = text.trim();
      if (!trimmed) return;

      // Clear any existing stream
      if (streamRef.current) clearTimeout(streamRef.current);

      // Append user message
      const userMsgId = `user-${Date.now()}`;
      setMessages((prev) => [
        ...prev,
        { id: userMsgId, sender: 'user', text: trimmed },
      ]);
      setInputVal('');
      setIsTyping(true);

      // Find matching demo response
      const response = findResponse(trimmed);

      // Call callback with the response (contains geoData, etc.)
      if (onResponseFound) {
        onResponseFound(response);
      }

      // Simulate thinking delay (600–1200ms)
      const thinkDelay = 600 + Math.random() * 600;

      setTimeout(() => {
        setIsTyping(false);

        const aiMsgId = `ai-${Date.now()}`;

        // Insert AI message placeholder (starts streaming)
        setMessages((prev) => [
          ...prev,
          {
            id: aiMsgId,
            sender: 'ai',
            text: '',
            citation: response.citation,
            source: response.source,
            insightCard: response.insightCard,
            mapEvent: response.mapEvent,
            isStreaming: true,
          },
        ]);

        // Fire map event early (like NER running ahead of generation)
        if (response.mapEvent && onMapEvent) {
          setTimeout(() => onMapEvent(response.mapEvent), 400);
        }

        // Stream the response text
        streamText(aiMsgId, response.text, () => {
          // After streaming done, reveal insight card with a slight delay
          // (card appears after text settles)
          if (response.insightCard) {
            setTimeout(() => {
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === aiMsgId ? { ...m, cardVisible: true } : m
                )
              );
            }, 300);
          }
        });
      }, thinkDelay);
    },
    [streamText, onMapEvent, onResponseFound]
  );

  return { messages, isTyping, inputVal, setInputVal, sendMessage };
}
