/* ============================
   ARKANA — Components
   Chat, filters, accordion, timeline,
   auth toggle — all interactive logic.
   ============================ */

const Components = (() => {

  // ---- Init All (runs once after pages loaded) ----
  function init() {
    initTimeline();
    initChat();
    initFilterChips();
    initAccordion();
    initAuthToggle();
  }

  // ---- Page-Specific Init (runs on every navigation) ----
  function initPageSpecific(pageId) {
    if (pageId === 'identify') {
      Animations.animateConfidenceBar();
    }
    if (pageId === 'browse') {
      initFilterChips();
      initAccordion();
    }
    if (pageId === 'explore') {
      // Use the new AI-powered ExploreMap module
      ExploreMap.init();
    }
    if (pageId === 'askarkana') {
      AskArkana.init();
    }
  }

  // ---- Timeline Slider (Explorer) ----
  function initTimeline() {
    const slider = document.getElementById('timeline-slider');
    const label = document.getElementById('timeline-label');
    if (!slider || !label) return;

    slider.addEventListener('input', () => {
      const val = parseInt(slider.value);
      const year = Math.round(-1000 + (val / 100) * 3024);
      label.textContent = year < 0
        ? Math.abs(year) + ' BCE'
        : year + ' CE';
    });
  }

  // ---- Chat (Explorer) ----
  function initChat() {
    const input = document.getElementById('chat-input');
    const sendBtn = document.getElementById('chat-send');
    const messages = document.getElementById('chat-messages');
    if (!input || !sendBtn || !messages) return;

    // Remove old listeners by cloning
    const newSend = sendBtn.cloneNode(true);
    sendBtn.parentNode.replaceChild(newSend, sendBtn);
    const newInput = input.cloneNode(true);
    input.parentNode.replaceChild(newInput, input);

    function addMessage(text, isUser = false) {
      const div = document.createElement('div');
      if (isUser) {
        div.className = 'max-w-[85%] self-end bg-surface-container-low p-4 rounded-xl rounded-tr-none border border-outline-variant/20 text-on-surface font-body-md text-body-md';
        div.innerHTML = `<p>${escapeHtml(text)}</p>`;
      } else {
        div.className = 'max-w-[85%] self-start';
        const p = document.createElement('p');
        p.className = 'font-body-md text-body-md text-on-surface-variant leading-relaxed';
        p.textContent = text;
        div.appendChild(p);
      }
      messages.appendChild(div);
      messages.scrollTop = messages.scrollHeight;
    }

    function handleSend() {
      const val = newInput.value.trim();
      if (!val) return;
      addMessage(val, true);
      newInput.value = '';
      // Simulated AI response
      setTimeout(() => {
        const responses = [
          "That's a fascinating aspect of Indian heritage. The Indus Valley Civilization, dating back to around 3000 BCE, laid the foundation for many cultural practices we see in the subcontinent today.",
          "Excellent question. The Mughal Empire's patronage of the arts created a rich synthesis of Persian, Central Asian, and indigenous Indian aesthetic traditions.",
          "The Chola dynasty (9th–13th centuries CE) is renowned for extraordinary bronze casting using the lost-wax (cire perdue) technique, producing some of the finest metalwork in human history.",
          "Folk art traditions like Warli, Gond, and Madhubani continue to be practiced today, serving both ritual and aesthetic purposes in their communities of origin."
        ];
        addMessage(responses[Math.floor(Math.random() * responses.length)], false);
      }, 800);
    }

    newSend.addEventListener('click', handleSend);
    newInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') handleSend();
    });
  }

  // ---- Filter Chips (Browse) ----
  function initFilterChips() {
    document.querySelectorAll('.filter-chip').forEach(chip => {
      chip.addEventListener('click', () => {
        document.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('chip-active'));
        chip.classList.add('chip-active');

        const filter = chip.dataset.filter;
        const countEl = document.getElementById('result-count');
        if (countEl) {
          const counts = {
            all: '1,204', warli: '47', gond: '89', mughal: '312',
            buddhist: '156', chola: '203', rajput: '178'
          };
          countEl.textContent = `Showing ${counts[filter] || '1,204'} artifacts`;
        }
      });
    });
  }

  // ---- Accordion (Browse sidebar) ----
  function initAccordion() {
    document.querySelectorAll('.accordion-btn').forEach(btn => {
      // Remove old listeners by cloning
      const newBtn = btn.cloneNode(true);
      btn.parentNode.replaceChild(newBtn, btn);

      newBtn.addEventListener('click', () => {
        const content = newBtn.nextElementSibling;
        const icon = newBtn.querySelector('.accordion-icon');
        if (!content || !icon) return;
        const isOpen = content.classList.contains('open');
        content.classList.toggle('open', !isOpen);
        icon.classList.toggle('open', !isOpen);
        newBtn.setAttribute('aria-expanded', !isOpen);
      });
    });
  }

  // ---- Auth Toggle (Login) ----
  function initAuthToggle() {
    const toggle = document.getElementById('toggle-auth');
    if (!toggle) return;

    toggle.addEventListener('click', (e) => {
      e.preventDefault();
      const isLogin = toggle.textContent.trim() === 'Register';
      toggle.textContent = isLogin ? 'Sign in' : 'Register';

      const submitBtn = document.querySelector('#auth-form button[type="submit"]');
      if (submitBtn) submitBtn.textContent = isLogin ? 'Create Account' : 'Sign In';

      const heading = document.querySelector('#page-login h1');
      if (heading) heading.textContent = isLogin ? 'Create an Account' : 'Welcome to Arkana';
    });
  }

  // ---- Utility ----
  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  return { init, initPageSpecific };
})();
