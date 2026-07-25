/* ============================
   ARKANA — Explore Map Module
   Handles the Heritage Explorer page:
   - Leaflet.js map with vintage tiles
   - AI-powered search via Groq API
   - Location extraction & map plotting
   - Timeline era filtering
   - Quick-jump heritage chips
   ============================ */

const ExploreMap = (() => {
  // ─── Configuration ─────────────────────────────────────
  const GROQ_API_URL = 'https://api.groq.com/openai/v1/chat/completions';
  const GROQ_MODEL = 'llama-3.1-8b-instant';

  // Reads API key from window config or environment
  let API_KEY = window.GROQ_API_KEY || '';

  // System prompt optimized for map-first exploration
  const SYSTEM_PROMPT = `You are Arkana Heritage Explorer, a knowledgeable AI guide specializing in Indian cultural heritage geography and history. Your purpose is to help users discover heritage sites on an interactive map.

Your expertise covers:
- Ancient Indian civilizations (Indus Valley, Vedic, Maurya, Gupta, etc.)
- Indian art forms and their geographic origins (Warli, Gond, Madhubani, Tanjore, Pattachitra, etc.)
- Architecture and monuments (temples, forts, palaces, caves, stepwells)
- Historical dynasties and rulers (Chola, Mughal, Rajput, Vijayanagara, Maratha, etc.)
- UNESCO World Heritage Sites in India
- Classical dance and music forms and their regional origins
- Indian textiles, crafts, and their regions
- Festivals, rituals, and cultural traditions by region

IMPORTANT RULES:
1. ONLY answer questions related to Indian cultural heritage, history, art, architecture, traditions, and related topics.
2. If a user asks about something unrelated, politely decline: "I'm designed to help you explore India's heritage on the map. Would you like to discover [suggest a heritage topic]?"
3. Keep responses concise but rich — aim for 1-3 paragraphs focused on geographic and historical context.
4. Emphasize locations, regions, and geographic spread in your answers.
5. When mentioning dates, use BCE/CE format.
6. Use relevant emoji sparingly.

CRITICAL — LOCATION DATA:
After your text response, you MUST include a JSON block with geographic locations. This powers the interactive map. Use this EXACT format:

<<<LOCATIONS>>>
[{"name": "Place Name", "lat": 27.1751, "lng": 78.0421, "label": "Brief 3-5 word description", "era": "Period/Dynasty"}]
<<</LOCATIONS>>>

Rules for location data:
- ALWAYS include at least 1 location if your answer mentions any place, monument, region, or city.
- For a SINGLE monument/place (e.g., Taj Mahal): include that one location with precise coordinates.
  Example: Taj Mahal → [{"name": "Taj Mahal, Agra", "lat": 27.1751, "lng": 78.0421, "label": "Mughal Marble Mausoleum", "era": "Mughal (1632-1653 CE)"}]
- For EMPIRES/DYNASTIES (e.g., Mughal Empire): include 4-8 major cities/capitals/important sites.
  Example: Mughal Empire → Delhi, Agra, Fatehpur Sikri, Lahore, Aurangabad, Jaipur, etc.
- For ART FORMS: include the region(s) where they originated and are practiced.
- For DANCE/MUSIC forms: include the state(s) of origin.
- The "era" field should contain the dynasty/period name and approximate dates.
- The "label" should be a brief descriptor: "Mughal Capital", "Chola Temple City", "Origin of Warli Art", etc.
- Use accurate latitude and longitude coordinates for Indian locations.
- If off-topic, use: <<<LOCATIONS>>>[]<<</LOCATIONS>>>
- NEVER skip the location block.`;

  // ─── Era Data for Timeline ────────────────────────────
  const ERAS = [
    { name: 'Indus Valley', start: -3000, end: -1500, query: 'Indus Valley Civilization major sites like Harappa and Mohenjo-daro' },
    { name: 'Vedic Period', start: -1500, end: -500, query: 'Vedic period kingdoms and important sites' },
    { name: 'Maurya Empire', start: -322, end: -185, query: 'Maurya Empire major cities and Ashoka pillar sites' },
    { name: 'Gupta Empire', start: 320, end: 550, query: 'Gupta Empire golden age cities and cultural centers' },
    { name: 'Chola Dynasty', start: 848, end: 1279, query: 'Chola Dynasty capital and major temple cities' },
    { name: 'Delhi Sultanate', start: 1206, end: 1526, query: 'Delhi Sultanate major cities and monuments' },
    { name: 'Vijayanagara', start: 1336, end: 1646, query: 'Vijayanagara Empire capital Hampi and major sites' },
    { name: 'Mughal Empire', start: 1526, end: 1857, query: 'Mughal Empire major cities capitals and monuments' },
    { name: 'Maratha Empire', start: 1674, end: 1818, query: 'Maratha Empire forts and important cities' },
    { name: 'Modern India', start: 1947, end: 2024, query: 'Major UNESCO World Heritage Sites in India' }
  ];

  // ─── State ─────────────────────────────────────────────
  let chatHistory = [];
  let map = null;
  let markersLayer = null;
  let mapInitialized = false;
  let isProcessing = false;

  // DOM references
  let input, sendBtn, messagesContainer, messagesInner, typingIndicator, suggestionsEl;
  let mapInfoEl, mapTitleEl, mapDescEl, mapLegendEl, legendItemsEl;
  let timelineSlider, timelineLabel, timelineContainer;

  // Custom gold marker icon
  const goldIcon = () => L.divIcon({
    className: 'arkana-marker',
    html: `<div class="arkana-marker-pin"><span class="material-symbols-outlined" style="font-size:16px;color:#fff0da;">location_on</span></div><div class="arkana-marker-pulse"></div>`,
    iconSize: [36, 36],
    iconAnchor: [18, 36],
    popupAnchor: [0, -36]
  });

  // Numbered marker icon (for multi-location empires)
  const numberedIcon = (num) => L.divIcon({
    className: 'arkana-marker',
    html: `<div class="arkana-marker-pin"><span style="font-size:13px;color:#fff0da;font-weight:600;transform:rotate(45deg);display:block;">${num}</span></div><div class="arkana-marker-pulse"></div>`,
    iconSize: [36, 36],
    iconAnchor: [18, 36],
    popupAnchor: [0, -36]
  });

  // ─── Initialize ────────────────────────────────────────
  function init() {
    input = document.getElementById('explore-input');
    sendBtn = document.getElementById('explore-send');
    messagesContainer = document.getElementById('explore-chat-messages');
    messagesInner = document.getElementById('explore-messages-inner');
    typingIndicator = document.getElementById('explore-typing');
    suggestionsEl = document.getElementById('explore-suggestions');
    mapInfoEl = document.getElementById('explore-map-info');
    mapTitleEl = document.getElementById('explore-map-title');
    mapDescEl = document.getElementById('explore-map-desc');
    mapLegendEl = document.getElementById('explore-map-legend');
    legendItemsEl = document.getElementById('explore-legend-items');
    timelineSlider = document.getElementById('explore-timeline-slider');
    timelineLabel = document.getElementById('explore-timeline-label');
    timelineContainer = document.getElementById('explore-timeline-container');

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
    document.querySelectorAll('.explore-suggestion').forEach(chip => {
      chip.addEventListener('click', () => {
        input.value = chip.dataset.suggestion;
        sendBtn.disabled = false;
        handleSend();
      });
    });

    // Quick-jump map chips
    document.querySelectorAll('.explore-quick-chip').forEach(chip => {
      chip.addEventListener('click', () => {
        input.value = chip.dataset.query;
        sendBtn.disabled = false;
        handleSend();
      });
    });

    // Timeline slider
    initTimeline();
  }

  // ─── Initialize Leaflet Map ────────────────────────────
  function initMap() {
    const mapEl = document.getElementById('explore-map');
    if (!mapEl || mapInitialized) return;

    // Create map centered on India
    map = L.map('explore-map', {
      center: [22.5, 79.0],
      zoom: 5,
      zoomControl: false,
      attributionControl: false
    });

    // Add zoom control to bottom-right
    L.control.zoom({ position: 'bottomright' }).addTo(map);

    // Use Stadia Stamen Toner Lite for a clean vintage look (free, no key needed)
    // Fallback to OpenStreetMap
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '© OpenStreetMap'
    }).addTo(map);

    // Create a layer group for markers
    markersLayer = L.layerGroup().addTo(map);

    // Add default heritage markers for India overview
    addDefaultMarkers();

    mapInitialized = true;

    // Invalidate size after a short delay
    setTimeout(() => {
      if (map) map.invalidateSize();
    }, 300);
  }

  // ─── Add Default Heritage Markers ──────────────────────
  function addDefaultMarkers() {
    const defaultSites = [
      { name: 'Delhi', lat: 28.6139, lng: 77.2090, label: 'Mughal & Sultanate Capital' },
      { name: 'Agra', lat: 27.1751, lng: 78.0421, label: 'Taj Mahal & Mughal Architecture' },
      { name: 'Jaipur', lat: 26.9124, lng: 75.7873, label: 'Rajput Heritage City' },
      { name: 'Hampi', lat: 15.3350, lng: 76.4600, label: 'Vijayanagara Ruins' },
      { name: 'Thanjavur', lat: 10.7870, lng: 79.1378, label: 'Chola Temple City' },
      { name: 'Varanasi', lat: 25.3176, lng: 83.0068, label: 'Oldest Living City' },
      { name: 'Khajuraho', lat: 24.8318, lng: 79.9199, label: 'Chandela Temples' },
      { name: 'Konark', lat: 19.8876, lng: 86.0945, label: 'Sun Temple' },
      { name: 'Ajanta', lat: 20.5519, lng: 75.7033, label: 'Buddhist Cave Paintings' },
      { name: 'Mahabalipuram', lat: 12.6172, lng: 80.1927, label: 'Pallava Shore Temples' },
    ];

    defaultSites.forEach(site => {
      const marker = L.marker([site.lat, site.lng], { icon: goldIcon() })
        .bindPopup(`
          <div class="arkana-popup">
            <strong>${site.name}</strong>
            <br><span style="color:#6f5100;font-size:12px;">${site.label}</span>
          </div>
        `, {
          className: 'arkana-popup-container',
          maxWidth: 250
        });
      markersLayer.addLayer(marker);
    });
  }

  // ─── Initialize Timeline ──────────────────────────────
  function initTimeline() {
    if (!timelineSlider || !timelineLabel) return;

    timelineSlider.addEventListener('input', () => {
      const val = parseInt(timelineSlider.value);
      const year = Math.round(-3000 + (val / 100) * 5024);
      
      if (year < 0) {
        timelineLabel.textContent = Math.abs(year) + ' BCE';
      } else {
        timelineLabel.textContent = year + ' CE';
      }

      // Find matching era
      const matchedEra = ERAS.find(era => year >= era.start && year <= era.end);
      if (matchedEra) {
        timelineLabel.textContent += ` · ${matchedEra.name}`;
      }
    });

    // Double-click on timeline to search that era
    timelineSlider.addEventListener('dblclick', () => {
      const val = parseInt(timelineSlider.value);
      const year = Math.round(-3000 + (val / 100) * 5024);
      const matchedEra = ERAS.find(era => year >= era.start && year <= era.end);
      
      if (matchedEra) {
        input.value = matchedEra.query;
        sendBtn.disabled = false;
        handleSend();
      }
    });
  }

  // ─── Handle Send ───────────────────────────────────────
  async function handleSend() {
    const text = input.value.trim();
    if (!text || isProcessing) return;
    isProcessing = true;

    // Add user message
    addMessage(text, true);
    input.value = '';
    sendBtn.disabled = true;

    // Hide suggestions
    if (suggestionsEl) {
      suggestionsEl.style.display = 'none';
    }

    // Hide timeline to show map better
    if (timelineContainer) {
      timelineContainer.style.opacity = '0.3';
      timelineContainer.style.pointerEvents = 'none';
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

        // Store clean text in history
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
        errorMsg = 'API key issue. Please check the configuration.';
      } else if (error.message.includes('429')) {
        errorMsg = 'Too many requests — please wait a moment and try again.';
      }

      addMessage(errorMsg, false, true);
    }

    isProcessing = false;

    // Restore timeline
    if (timelineContainer) {
      setTimeout(() => {
        timelineContainer.style.opacity = '1';
        timelineContainer.style.pointerEvents = 'auto';
      }, 2000);
    }
  }

  // ─── Parse Locations from Response ─────────────────────
  function parseLocations(response) {
    let text = response;
    let locations = [];

    const locRegex = /<<<LOCATIONS>>>\s*([\s\S]*?)\s*<<<\/LOCATIONS>>>/;
    const match = response.match(locRegex);

    if (match) {
      text = response.replace(locRegex, '').trim();

      try {
        locations = JSON.parse(match[1].trim());
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
    const useNumbers = locations.length > 1;

    locations.forEach((loc, index) => {
      const icon = useNumbers ? numberedIcon(index + 1) : goldIcon();
      const marker = L.marker([loc.lat, loc.lng], { icon })
        .bindPopup(`
          <div class="arkana-popup">
            <strong>${escapeHtml(loc.name)}</strong>
            ${loc.label ? `<br><span style="color:#6f5100;font-size:12px;">${escapeHtml(loc.label)}</span>` : ''}
            ${loc.era ? `<br><span style="color:#807665;font-size:11px;font-style:italic;">${escapeHtml(loc.era)}</span>` : ''}
          </div>
        `, {
          className: 'arkana-popup-container',
          maxWidth: 280
        });

      markersLayer.addLayer(marker);
      bounds.push([loc.lat, loc.lng]);

      // Add marker entrance animation delay
      setTimeout(() => {
        if (index === 0) marker.openPopup();
      }, 800 + (index * 200));
    });

    // Fly to location(s)
    if (bounds.length === 1) {
      map.flyTo(bounds[0], 12, {
        duration: 1.5,
        easeLinearity: 0.25
      });
    } else if (bounds.length > 1) {
      const leafletBounds = L.latLngBounds(bounds);
      map.flyToBounds(leafletBounds, {
        padding: [60, 60],
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
      mapDescEl.textContent = `${locations[0].label || ''}${locations[0].era ? ' · ' + locations[0].era : ''}`;
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
      legendItemsEl.innerHTML = locations.map((loc, i) =>
        `<div class="flex items-center gap-2 cursor-pointer explore-legend-item" data-lat="${loc.lat}" data-lng="${loc.lng}">
          <div class="w-5 h-5 rounded-full bg-primary-container flex-shrink-0 flex items-center justify-center text-[10px] text-on-primary-container font-bold">${i + 1}</div>
          <span class="font-label-sm text-[11px] text-on-surface truncate">${escapeHtml(loc.name)}</span>
        </div>`
      ).join('');

      // Click on legend item to fly to that location
      legendItemsEl.querySelectorAll('.explore-legend-item').forEach(item => {
        item.addEventListener('click', () => {
          const lat = parseFloat(item.dataset.lat);
          const lng = parseFloat(item.dataset.lng);
          map.flyTo([lat, lng], 12, { duration: 1 });

          // Open the matching marker popup
          markersLayer.eachLayer(layer => {
            const latlng = layer.getLatLng();
            if (Math.abs(latlng.lat - lat) < 0.01 && Math.abs(latlng.lng - lng) < 0.01) {
              layer.openPopup();
            }
          });
        });
      });

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
          <span class="material-symbols-outlined text-[18px]">${isError ? 'error_outline' : 'travel_explore'}</span>
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
