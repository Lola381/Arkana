/* ============================
   ARKANA — Router & Page Transitions
   Handles SPA navigation, geometric wipe,
   and expanding card transitions.
   ============================ */

const Router = (() => {
  // DOM references
  const overlay = document.getElementById('transition-overlay');
  const cardCover = document.getElementById('card-cover');
  const navbar = document.getElementById('navbar');
  const hamburger = document.getElementById('hamburger');
  const mobileMenu = document.getElementById('mobile-menu');
  const mobileClose = document.getElementById('mobile-menu-close');

  let currentPage = 'home';
  let isTransitioning = false;
  let pages = {};

  // ---- Initialize ----
  function init() {
    // Collect page containers
    document.querySelectorAll('.page').forEach(el => {
      const id = el.id.replace('page-', '');
      pages[id] = el;
    });

    // Load page fragments from /pages/ folder
    loadAllPages().then(() => {
      // Attach global click listener for [data-page] links
      document.addEventListener('click', handleNavClick);

      // Mobile menu
      if (hamburger) hamburger.addEventListener('click', openMobileMenu);
      if (mobileClose) mobileClose.addEventListener('click', closeMobileMenu);

      // Navbar scroll effect
      window.addEventListener('scroll', handleScroll, { passive: true });

      // Show initial page
      const hash = window.location.hash.replace('#', '') || 'home';
      if (pages[hash]) {
        pages[hash].classList.add('active');
        currentPage = hash;
      }
      updateNavLinks();
      Animations.initReveal();
      Components.init();
      
      if (currentPage === 'askarkana') {
        AskArkana.init();
      }
      if (currentPage === 'explore') {
        ExploreMap.init();
      }
    });
  }

  // ---- Load Page Fragments ----
  async function loadAllPages() {
    const pageNames = ['home', 'explore', 'browse', 'culture', 'artifact', 'identify', 'askarkana', 'login'];
    const promises = pageNames.map(async (name) => {
      try {
        const resp = await fetch(`pages/${name}.html`);
        if (resp.ok) {
          const html = await resp.text();
          const container = pages[name];
          if (container) container.innerHTML = html;
        }
      } catch (e) {
        console.warn(`Could not load pages/${name}.html:`, e);
      }
    });
    await Promise.all(promises);
  }

  // ---- Navigation Click Handler ----
  function handleNavClick(e) {
    const navLink = e.target.closest('[data-page]');
    if (!navLink) return;
    e.preventDefault();

    const pageId = navLink.dataset.page;
    if (!pageId || !pages[pageId]) return;

    // Check if clicking an expand-card
    const card = e.target.closest('.expand-card');
    if (card && card.dataset.page) {
      showPage(card.dataset.page, card);
    } else {
      showPage(pageId);
    }

    // Close mobile menu
    closeMobileMenu();
  }

  // ---- Show Page (with transition) ----
  function showPage(pageId, fromCard = null) {
    if (isTransitioning || pageId === currentPage) return;
    isTransitioning = true;

    const target = pages[pageId];
    if (!target) { isTransitioning = false; return; }

    if (fromCard) {
      expandingCardTransition(pageId, target, fromCard);
    } else {
      geometricWipeTransition(pageId, target);
    }
  }

  // ---- Geometric Wipe Transition (trans.txt #4) ----
  function geometricWipeTransition(pageId, target) {
    overlay.classList.add('wipe-in');

    setTimeout(() => {
      swapPages(pageId, target);

      overlay.classList.remove('wipe-in');
      overlay.classList.add('wipe-out');

      setTimeout(() => {
        overlay.classList.remove('wipe-out');
        isTransitioning = false;
      }, 600);
    }, 450);
  }

  // ---- Expanding Card Transition (trans.txt #2) ----
  function expandingCardTransition(pageId, target, card) {
    const rect = card.getBoundingClientRect();

    cardCover.style.cssText = `
      top: ${rect.top}px; left: ${rect.left}px;
      width: ${rect.width}px; height: ${rect.height}px;
      opacity: 1; border-radius: 4px;
    `;

    requestAnimationFrame(() => {
      cardCover.style.cssText = `
        top: 0; left: 0; width: 100vw; height: 100vh;
        opacity: 1; border-radius: 0;
        transition: all 500ms cubic-bezier(0.16, 1, 0.3, 1);
      `;

      setTimeout(() => {
        swapPages(pageId, target);

        setTimeout(() => {
          cardCover.style.cssText = `
            top: 0; left: 0; width: 100vw; height: 100vh;
            opacity: 0; border-radius: 0;
            transition: opacity 300ms ease;
          `;
          setTimeout(() => {
            cardCover.style.cssText = 'opacity: 0;';
            isTransitioning = false;
          }, 300);
        }, 50);
      }, 450);
    });
  }

  // ---- Swap Pages (shared logic) ----
  function swapPages(pageId, target) {
    pages[currentPage].classList.remove('active');
    target.classList.add('active');
    currentPage = pageId;
    window.scrollTo(0, 0);
    window.location.hash = pageId;
    updateNavLinks();
    Animations.initReveal();
    Components.initPageSpecific(pageId);
  }

  // ---- Update Active Nav Link ----
  function updateNavLinks() {
    document.querySelectorAll('#navbar [data-page]').forEach(el => {
      el.classList.remove('text-primary', 'font-bold');
      if (el.dataset.page === currentPage) {
        el.classList.add('text-primary');
      }
    });
  }

  // ---- Mobile Menu ----
  function openMobileMenu() {
    mobileMenu.classList.add('open');
    hamburger.setAttribute('aria-expanded', 'true');
  }

  function closeMobileMenu() {
    mobileMenu.classList.remove('open');
    if (hamburger) hamburger.setAttribute('aria-expanded', 'false');
  }

  // ---- Navbar Scroll ----
  function handleScroll() {
    if (window.scrollY > 40) {
      navbar.classList.add('scrolled');
    } else {
      navbar.classList.remove('scrolled');
    }
  }

  // ---- Public API ----
  return {
    init,
    showPage,
    getCurrentPage: () => currentPage
  };
})();

// Boot on DOM ready
document.addEventListener('DOMContentLoaded', Router.init);
