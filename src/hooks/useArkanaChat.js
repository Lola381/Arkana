import { useState, useCallback, useRef, useEffect } from 'react';
import { queryChatStream } from '../services/arkanaApi';

/**
 * useArkanaChat
 * 
 * Custom hook that drives the "Ask Arkana" chat panel.
 * Connects to the real FastAPI backend via SSE streaming.
 * 
 * Event types from backend:
 *   - token: {type: 'token', data: '...'} - streaming text chunks
 *   - citation: {type: 'citation', data: {index, source_title, institution, chunk_id}}
 *   - map_event: {type: 'map_event', data: {type: 'MAP_HIGHLIGHT'|'MAP_PAN'|'TIMELINE_SEEK', ...}}
 *   - insight_card: {type: 'insight_card', data: {artifact_id, title, image_url, tribe, period, institution}}
 *   - done: {type: 'done', data: null}
 *   - error: {type: 'error', data: 'error message'}
 * 
 * @param {Function} onMapEvent  — called with { type, data } when map events fire
 * @param {Function} onInsightCard — called with insight card data when received
 */
export function useArkanaChat(onMapEvent, onInsightCard) {
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      sender: 'ai',
      text: "Welcome to the archive. I can help you explore any aspect of India's cultural heritage — from ancient Mauryan sculptures to contemporary folk traditions. What would you like to discover?",
      citations: [],
      insightCard: null,
      isStreaming: false,
    },
  ]);
  const [isTyping, setIsTyping] = useState(false);
  const [inputVal, setInputVal] = useState('');
  const streamRef = useRef(null);
  const currentAiMessageId = useRef(null);
  const citationsRef = useRef([]);
  const conversationHistoryRef = useRef([]);

  /**
   * Stream text chunks into the current AI message
   */
  const appendToken = useCallback((messageId, token) => {
    setMessages((prev) =>
      prev.map((m) =>
        m.id === messageId ? { ...m, text: m.text + token } : m
      )
    );
  }, []);

  /**
   * Add a citation to the current AI message
   */
  const addCitation = useCallback((citation) => {
    citationsRef.current.push(citation);
    setMessages((prev) =>
      prev.map((m) =>
        m.id === currentAiMessageId.current
          ? { ...m, citations: [...citationsRef.current] }
          : m
      )
    );
  }, []);

  /**
   * Send a message to the Arkana backend via SSE
   */
  const sendMessage = useCallback(
    async (text) => {
      const trimmed = text.trim();
      if (!trimmed) return;

      // Clear any existing stream
      if (streamRef.current) {
        streamRef.current.cancel?.();
        streamRef.current = null;
      }

      // Append user message
      const userMsgId = `user-${Date.now()}`;
      setMessages((prev) => [
        ...prev,
        { id: userMsgId, sender: 'user', text: trimmed },
      ]);
      setInputVal('');
      setIsTyping(true);

      // Add to conversation history (for context)
      conversationHistoryRef.current.push({ role: 'user', content: trimmed });

      // Create AI message placeholder
      const aiMsgId = `ai-${Date.now()}`;
      currentAiMessageId.current = aiMsgId;
      citationsRef.current = [];

      setMessages((prev) => [
        ...prev,
        {
          id: aiMsgId,
          sender: 'ai',
          text: '',
          citations: [],
          insightCard: null,
          isStreaming: true,
        },
      ]);

      try {
        await queryChatStream(
          trimmed,
          conversationHistoryRef.current.slice(-6), // Last 3 turns
          {}, // mapContext - could be enhanced with current map state
          (event) => {
            switch (event.type) {
              case 'token':
                appendToken(aiMsgId, event.data);
                break;

              case 'citation':
                addCitation(event.data);
                break;

              case 'map_event':
                if (onMapEvent) {
                  onMapEvent(event.data);
                }
                break;

              case 'insight_card':
                // Update the current message with the insight card
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === aiMsgId ? { ...m, insightCard: event.data } : m
                  )
                );
                if (onInsightCard) {
                  onInsightCard(event.data);
                }
                break;

              case 'error':
                console.error('Backend error:', event.data);
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === aiMsgId
                      ? { ...m, text: `[Error: ${event.data}]`, isStreaming: false }
                      : m
                  )
                );
                break;

              case 'done':
                // Streaming complete - add assistant response to history
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === aiMsgId ? { ...m, isStreaming: false } : m
                  )
                );
                // Get the final text for conversation history
                const finalMsg = messages.find((m) => m.id === aiMsgId);
                if (finalMsg) {
                  conversationHistoryRef.current.push({
                    role: 'assistant',
                    content: finalMsg.text,
                  });
                }
                setIsTyping(false);
                break;

              default:
                console.warn('Unknown event type:', event.type);
            }
          }
        );
      } catch (error) {
        console.error('Chat stream error:', error);
        setMessages((prev) =>
          prev.map((m) =>
            m.id === aiMsgId
              ? { ...m, text: `[Error: ${error.message}]`, isStreaming: false }
              : m
          )
        );
        setIsTyping(false);
      }
    },
    [appendToken, addCitation, onMapEvent, onInsightCard, messages]
  );

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current.cancel?.();
      }
    };
  }, []);

  return { messages, isTyping, inputVal, setInputVal, sendMessage };
}