/* ============================
   ARKANA — Ask Arkana AI Chat + Map
   Handles Groq API calls with heritage-only
   system prompt, location extraction, and
   Leaflet.js map integration.
   ============================ */

const AskArkana = (() => {
  // ─── Configuration ─────────────────────────────────────
  const GROQ_API_URL = 'https://api.groq.com/openai/v1/chat/completions';
  const GROQ_MODEL = 'llama-3.1-8b-instant';

  // Reads API key from window config or environment
  let API_KEY = window.GROQ_API_KEY || '';

  // System prompt with location extraction instructions
  const SYSTEM_PROMPT = `You are Arkana, a knowledgeable and passionate AI guide specializing exclusively in Indian cultural heritage. Your expertise covers:

- Ancient Indian civilizations (Indus Valley, Vedic, Maurya, Gupta, etc.)
- Indian art forms (Warli, Gond, Madhubani, Tanjore, Pattachitra, Kalamkari, etc.)
- Architecture and monuments (temples, forts, palaces, caves, stepwells)
- Classical dance forms (Bharatanatyam, Kathak, Odissi, Kathakali, Kuchipudi, etc.)
- Classical and folk music (Hindustani, Carnatic, folk traditions)
- Indian textiles and crafts (Banarasi silk, Pashmina, Chikankari, block printing, etc.)
- Historical dynasties and rulers (Chola, Mughal, Rajput, Vijayanagara, Maratha, etc.)
- Festivals, rituals, and traditions
- Indian literature, philosophy, and scriptures
- UNESCO World Heritage Sites in India
- Archaeological discoveries and museum collections
- Traditional Indian cuisine in cultural context
- Indian languages and scripts

IMPORTANT RULES:
1. ONLY answer questions related to Indian cultural heritage, history, art, architecture, traditions, and related topics.
2. If a user asks about something unrelated (e.g., coding, math, current politics, sports, technology, personal advice, other countries' cultures), politely decline and redirect them: "I appreciate your curiosity! However, I'm specifically designed to help you explore India's rich cultural heritage. Would you like to learn about [suggest a relevant heritage topic]?"
3. Keep responses informative but conversational — like a knowledgeable museum guide.
4. Use rich details, historical context, and interesting facts to make responses engaging.
5. When mentioning dates, use BCE/CE format.
6. Keep responses concise but thorough — aim for 2-4 paragraphs unless a longer explanation is warranted.
7. You may use relevant emoji sparingly to make responses visually engaging.
8. Always maintain a warm, welcoming, and educational tone.

CRITICAL — LOCATION DATA:
After your text response, you MUST include a JSON block with geographic locations relevant to your answer. This data powers an interactive map. Use this EXACT format:

<<<LOCATIONS>>>
[{"name": "Place Name", "lat": 27.1751, "lng": 78.0421, "label": "Brief 3-5 word description"}]
<<</LOCATIONS>>>

Rules for location data:
- Always include at least 1 location if your answer mentions any place, monument, region, or city in India.
- For a single monument/place (e.g., Taj Mahal), include just that one location.
- For empires/dynasties (e.g., Mughal Empire), include 3-8 major cities/capitals under that empire with their coordinates.
- For art forms, include the region(s) where they originated.
- For dance/music forms, include the state(s) where they originated.
- Use accurate latitude and longitude coordinates for Indian locations.
- The "label" should be a brief descriptor like "Mughal Capital", "Chola Temple", "Origin of Warli Art", etc.
- If the question is off-topic and you decline to answer, use: <<<LOCATIONS>>>[]<<</LOCATIONS>>>
- NEVER skip the location block. Always include it.`;

  // ─── State ─────────────────────────────────────────────
  let chatHistory = [];
  let map = null;
  let markersLayer = null;
  let mapInitialized = false;

  // DOM references
  let input, sendBtn, messagesContainer, messagesInner, typingIndicator, suggestionsEl;
  let mapInfoEl, mapTitleEl, mapDescEl, mapLegendEl, legendItemsEl;

  // Custom gold marker icon
  const goldIcon = () => L.divIcon({
    className: 'arkana-marker',
    html: `<div class="arkana-marker-pin"><span class="material-symbols-outlined" style="font-size:16px;color:#fff0da;">location_on</span></div><div class="arkana-marker-pulse"></div>`,
    iconSize: [36, 36],
    iconAnchor: [18, 36],
    popupAnchor: [0, -36]
  });

  // ─── Initialize ────────────────────────────────────────
  function init() {
    input = document.getElementById('arkana-input');
    sendBtn = document.getElementById('arkana-send');
    messagesContainer = document.getElementById('arkana-chat-messages');
    messagesInner = document.getElementById('arkana-messages-inner');
    typingIndicator = document.getElementById('arkana-typing');
    suggestionsEl = document.getElementById('arkana-suggestions');
    mapInfoEl = document.getElementById('arkana-map-info');
    mapTitleEl = document.getElementById('arkana-map-title');
    mapDescEl = document.getElementById('arkana-map-desc');
    mapLegendEl = document.getElementById('arkana-map-legend');
    legendItemsEl = document.getElementById('arkana-legend-items');

    if (!input || !sendBtn) return;

    // Initialize map
    initMap();

    // Clone to remove old listeners
    const newSend = sendBtn.cloneNode(true);
    sendBtn.parentNode.replaceChild(newSend, sendBtn);
    sendBtn = newSend;

    const newInput = input.cloneNode(true);
    input.parentNode.replaceChild(newInput, input);
    input = newInput;

    // Event listeners
    sendBtn.addEventListener('click', handleSend);
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    });

    input.addEventListener('input', () => {
      sendBtn.disabled = !input.value.trim();
    });

    // Suggestion chips
    document.querySelectorAll('.arkana-chip[data-suggestion]').forEach(chip => {
      chip.addEventListener('click', () => {
        input.value = chip.dataset.suggestion;
        sendBtn.disabled = false;
        handleSend();
      });
    });
  }

  // ─── Initialize Leaflet Map ────────────────────────────
  function initMap() {
    const mapEl = document.getElementById('arkana-map');
    if (!mapEl || mapInitialized) return;

    // Create map centered on India
    map = L.map('arkana-map', {
      center: [22.5, 79.0],
      zoom: 5,
      zoomControl: false,
      attributionControl: false
    });

    // Add zoom control to bottom-right
    L.control.zoom({ position: 'bottomright' }).addTo(map);

    // Use OpenStreetMap tiles (free, no API key needed)
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '© OpenStreetMap'
    }).addTo(map);

    // Create a layer group for markers
    markersLayer = L.layerGroup().addTo(map);

    mapInitialized = true;

    // Invalidate size after a short delay (fixes rendering in hidden panels)
    setTimeout(() => {
      if (map) map.invalidateSize();
    }, 300);
  }

  // ─── Handle Send ───────────────────────────────────────
  async function handleSend() {
    const text = input.value.trim();
    if (!text) return;

    // Add user message
    addMessage(text, true);
    input.value = '';
    sendBtn.disabled = true;

    // Hide suggestions
    if (suggestionsEl) {
      suggestionsEl.style.display = 'none';
    }

    // Show typing indicator
    showTyping(true);

    // Add to chat history
    chatHistory.push({ role: 'user', content: text });

    try {
      const rawResponse = await callGroqAPI(chatHistory);
      showTyping(false);

      if (rawResponse) {
        // Extract locations and clean response
        const { text: cleanText, locations } = parseLocations(rawResponse);

        // Store clean text in history (without location JSON)
        chatHistory.push({ role: 'assistant', content: cleanText });
        addMessage(cleanText, false);

        // Update map with locations
        if (locations && locations.length > 0) {
          updateMap(locations);
        }
      }
    } catch (error) {
      showTyping(false);
      console.error('Groq API error:', error);

      let errorMsg = 'I encountered an issue connecting to my knowledge base. Please try again.';
      if (error.message.includes('401') || error.message.includes('Unauthorized')) {
        errorMsg = 'Your API key appears to be invalid. Please refresh the page and enter a valid Groq API key.';
        API_KEY = '';
      } else if (error.message.includes('429')) {
        errorMsg = 'I\'m receiving too many requests right now. Please wait a moment and try again.';
      }

      addMessage(errorMsg, false, true);
    }
  }

  // ─── Parse Locations from Response ─────────────────────
  function parseLocations(response) {
    let text = response;
    let locations = [];

    // Try to extract <<<LOCATIONS>>> block
    const locRegex = /<<<LOCATIONS>>>\s*([\s\S]*?)\s*<<<\/LOCATIONS>>>/;
    const match = response.match(locRegex);

    if (match) {
      // Remove the location block from the visible text
      text = response.replace(locRegex, '').trim();

      try {
        locations = JSON.parse(match[1].trim());
        // Validate location data
        locations = locations.filter(loc =>
          loc && typeof loc.lat === 'number' && typeof loc.lng === 'number' && loc.name
        );
      } catch (e) {
        console.warn('Failed to parse location data:', e);
        locations = [];
      }
    }

    return { text, locations };
  }

  // ─── Update Map with Locations ─────────────────────────
  function updateMap(locations) {
    if (!map || !markersLayer) return;

    // Ensure map is properly sized
    map.invalidateSize();

    // Clear existing markers
    markersLayer.clearLayers();

    // Add new markers
    const bounds = [];
    locations.forEach((loc, index) => {
      const marker = L.marker([loc.lat, loc.lng], { icon: goldIcon() })
        .bindPopup(`
          <div class="arkana-popup">
            <strong>${escapeHtml(loc.name)}</strong>
            ${loc.label ? `<br><span style="color:#6f5100;font-size:12px;">${escapeHtml(loc.label)}</span>` : ''}
          </div>
        `, {
          className: 'arkana-popup-container',
          maxWidth: 250
        });

      markersLayer.addLayer(marker);
      bounds.push([loc.lat, loc.lng]);

      // Open popup for the first marker after a delay
      if (index === 0) {
        setTimeout(() => marker.openPopup(), 800);
      }
    });

    // Fly to location(s)
    if (bounds.length === 1) {
      // Single location: fly to it with zoom
      map.flyTo(bounds[0], 10, {
        duration: 1.5,
        easeLinearity: 0.25
      });
    } else if (bounds.length > 1) {
      // Multiple locations: fit bounds with padding
      const leafletBounds = L.latLngBounds(bounds);
      map.flyToBounds(leafletBounds, {
        padding: [50, 50],
        duration: 1.5,
        maxZoom: 8
      });
    }

    // Update info card
    updateMapInfo(locations);

    // Update legend
    updateLegend(locations);
  }

  // ─── Update Map Info Card ──────────────────────────────
  function updateMapInfo(locations) {
    if (!mapInfoEl || !mapTitleEl || !mapDescEl) return;

    if (locations.length === 1) {
      mapTitleEl.textContent = locations[0].name;
      mapDescEl.textContent = locations[0].label || '';
      mapInfoEl.classList.remove('hidden');
      mapInfoEl.classList.add('arkana-fade-in');
    } else if (locations.length > 1) {
      mapTitleEl.textContent = `${locations.length} Heritage Locations`;
      mapDescEl.textContent = locations.map(l => l.name).join(' · ');
      mapInfoEl.classList.remove('hidden');
      mapInfoEl.classList.add('arkana-fade-in');
    } else {
      mapInfoEl.classList.add('hidden');
    }
  }

  // ─── Update Legend ─────────────────────────────────────
  function updateLegend(locations) {
    if (!mapLegendEl || !legendItemsEl) return;

    if (locations.length > 1) {
      legendItemsEl.innerHTML = locations.map(loc =>
        `<div class="flex items-center gap-2">
          <div class="w-2 h-2 rounded-full bg-primary-container flex-shrink-0"></div>
          <span class="font-label-sm text-[11px] text-on-surface truncate">${escapeHtml(loc.name)}</span>
        </div>`
      ).join('');
      mapLegendEl.classList.remove('hidden');
      mapLegendEl.classList.add('arkana-fade-in');
    } else {
      mapLegendEl.classList.add('hidden');
    }
  }

  // ─── Call Groq API ─────────────────────────────────────
  async function callGroqAPI(messages) {
    const apiMessages = [
      { role: 'system', content: SYSTEM_PROMPT },
      ...messages.slice(-10)
    ];

    const response = await fetch(GROQ_API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${API_KEY}`
      },
      body: JSON.stringify({
        model: GROQ_MODEL,
        messages: apiMessages,
        temperature: 0.7,
        max_tokens: 1500,
        top_p: 0.9
      })
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    return data.choices?.[0]?.message?.content || 'I couldn\'t generate a response. Please try again.';
  }

  // ─── Add Message to Chat ───────────────────────────────
  function addMessage(text, isUser = false, isError = false) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `arkana-msg ${isUser ? 'arkana-msg-user' : 'arkana-msg-ai'} arkana-fade-in`;

    const now = new Date();
    const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    if (isUser) {
      msgDiv.innerHTML = `
        <div class="arkana-msg-content arkana-msg-content-user">
          <div class="arkana-msg-bubble arkana-msg-bubble-user">
            <p>${escapeHtml(text)}</p>
          </div>
          <span class="arkana-msg-time arkana-msg-time-user font-label-sm text-label-sm text-on-surface-variant/60">${timeStr}</span>
        </div>
      `;
    } else {
      const formattedText = formatResponse(text);
      msgDiv.innerHTML = `
        <div class="arkana-msg-avatar">
          <span class="material-symbols-outlined text-[18px]">${isError ? 'error_outline' : 'auto_awesome'}</span>
        </div>
        <div class="arkana-msg-content">
          <div class="arkana-msg-bubble arkana-msg-bubble-ai ${isError ? 'arkana-msg-error' : ''}">
            ${formattedText}
          </div>
          <span class="arkana-msg-time font-label-sm text-label-sm text-on-surface-variant/60">${timeStr}</span>
        </div>
      `;
    }

    messagesInner.appendChild(msgDiv);
    scrollToBottom();
  }

  // ─── Format AI Response ────────────────────────────────
  function formatResponse(text) {
    let html = escapeHtml(text);

    // Bold: **text**
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

    // Italic: *text*
    html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');

    // Convert newlines to paragraph breaks
    const paragraphs = html.split(/\n\n+/);
    if (paragraphs.length > 1) {
      html = paragraphs.map(p => `<p>${p.trim()}</p>`).join('');
    } else {
      html = `<p>${html}</p>`;
    }

    // Single newlines to <br>
    html = html.replace(/\n/g, '<br>');

    return html;
  }

  // ─── Typing Indicator ─────────────────────────────────
  function showTyping(show) {
    if (!typingIndicator) return;
    typingIndicator.classList.toggle('hidden', !show);
    if (show) scrollToBottom();
  }

  // ─── Scroll to Bottom ─────────────────────────────────
  function scrollToBottom() {
    requestAnimationFrame(() => {
      if (messagesContainer) {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
      }
    });
  }

  // ─── Escape HTML ──────────────────────────────────────
  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  // ─── Public API ───────────────────────────────────────
  return { init };
})();
