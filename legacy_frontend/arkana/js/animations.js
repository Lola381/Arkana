/* ============================
   ARKANA — Animations
   Scroll reveal, parallax, confidence bar
   ============================ */

const Animations = (() => {

  // ---- Scroll Reveal ----
  function initReveal() {
    const reveals = document.querySelectorAll('.page.active .reveal');
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('active');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1, rootMargin: '0px 0px -80px 0px' });

    reveals.forEach(el => {
      el.classList.remove('active');
      observer.observe(el);
    });

    // Trigger immediately for elements already in viewport
    setTimeout(() => {
      reveals.forEach(el => {
        const rect = el.getBoundingClientRect();
        if (rect.top < window.innerHeight - 50) {
          el.classList.add('active');
        }
      });
    }, 100);
  }

  // ---- Hero Parallax (Mousemove) ----
  function initParallax() {
    document.addEventListener('mousemove', (e) => {
      const elements = document.querySelectorAll('.floating-element');
      if (elements.length === 0) return;

      elements.forEach(el => {
        const speed = parseFloat(el.dataset.speed) || 0.1;
        const x = (e.clientX * speed) / 10;
        const y = (e.clientY * speed) / 10;
        el.style.transform = `translateX(${x}px) translateY(${y}px)`;
      });
    }, { passive: true });
  }

  // ---- Confidence Bar Animation (Identify page) ----
  function animateConfidenceBar() {
    const bar = document.getElementById('confidence-bar');
    if (!bar) return;
    bar.classList.remove('animate');
    setTimeout(() => bar.classList.add('animate'), 500);
  }

  // ---- Card Tilt Animation B (3D tilt toward cursor) ----
  function initCardTilt() {
    document.addEventListener('mousemove', (e) => {
      const cards = document.querySelectorAll('.card-anim-b:hover');
      cards.forEach(card => {
        const rect = card.getBoundingClientRect();
        const centerX = rect.left + rect.width / 2;
        const centerY = rect.top + rect.height / 2;
        const rotateY = ((e.clientX - centerX) / rect.width) * 6;
        const rotateX = ((centerY - e.clientY) / rect.height) * 4;
        card.style.transform = `rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale(1.02)`;
      });
    }, { passive: true });

    // Reset on mouse leave
    document.addEventListener('mouseleave', (e) => {
      if (e.target.classList && e.target.classList.contains('card-anim-b')) {
        e.target.style.transform = '';
      }
    }, true);
  }

  // ---- Init ----
  function init() {
    initParallax();
    initCardTilt();
  }

  return { init, initReveal, animateConfidenceBar };
})();
