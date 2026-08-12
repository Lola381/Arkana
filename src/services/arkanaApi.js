/**
 * Arkana API Client
 * 
 * Connects the React frontend to the FastAPI backend endpoints.
 * Base URL defaults to the local development server.
 */

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

/**
 * Send a chat query to the Arkana RAG pipeline (non-streaming)
 * @param {string} query - User's question
 * @param {Array} conversationHistory - Previous messages [{role, content}]
 * @param {Object} mapContext - Current map state {tribe_name, region}
 * @returns {Promise<{answer, citations, map_events}>}
 */
export async function queryChat(query, conversationHistory = [], mapContext = {}) {
  const response = await fetch(`${API_BASE}/api/chat/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, conversation_history: conversationHistory, map_context: mapContext }),
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
  
  return response.json();
}

/**
 * Send a chat query with Server-Sent Events streaming
 * @param {string} query - User's question
 * @param {Array} conversationHistory - Previous messages [{role, content}]
 * @param {Object} mapContext - Current map state {tribe_name, region}
 * @param {Function} onEvent - Callback for each SSE event {type, data}
 * @returns {Promise<void>}
 */
export async function queryChatStream(query, conversationHistory = [], mapContext = {}, onEvent) {
  const response = await fetch(`${API_BASE}/api/chat/query/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, conversation_history: conversationHistory, map_context: mapContext }),
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
  
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || ''; // Keep incomplete line in buffer
    
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try {
          const event = JSON.parse(line.slice(6));
          onEvent(event);
        } catch (e) {
          console.warn('Failed to parse SSE event:', line, e);
        }
      }
    }
  }
}

/**
 * Get collection statistics (vector count, etc.)
 */
export async function getCollectionStats() {
  const response = await fetch(`${API_BASE}/api/collection/stats`);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

/**
 * List heritage sites with optional filters
 * @param {Object} filters - {state, category, limit}
 */
export async function listSites(filters = {}) {
  const params = new URLSearchParams();
  if (filters.state) params.append('state', filters.state);
  if (filters.category) params.append('category', filters.category);
  if (filters.limit) params.append('limit', filters.limit);
  
  const response = await fetch(`${API_BASE}/api/sites?${params}`);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

/**
 * Health check endpoint
 */
export async function healthCheck() {
  const response = await fetch(`${API_BASE}/health`);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}