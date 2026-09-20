/* All Wrapped Up — site behaviour (no dependencies) */
(function () {
  'use strict';

  // Sticky header shadow
  var header = document.querySelector('.site-header');
  function onScroll() { if (header) header.classList.toggle('scrolled', window.scrollY > 8); }
  window.addEventListener('scroll', onScroll, { passive: true }); onScroll();

  // Mobile nav
  var toggle = document.querySelector('.nav-toggle');
  var links = document.querySelector('.nav-links');
  if (toggle && links) {
    toggle.addEventListener('click', function () {
      var open = links.classList.toggle('open');
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && links.classList.contains('open')) { links.classList.remove('open'); toggle.setAttribute('aria-expanded', 'false'); toggle.focus(); }
    });
  }

  // Scroll reveal
  var revealEls = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window && revealEls.length) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) { if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); } });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
    revealEls.forEach(function (el) { io.observe(el); });
  } else { revealEls.forEach(function (el) { el.classList.add('in'); }); }

  // Footer year
  document.querySelectorAll('[data-year]').forEach(function (el) { el.textContent = new Date().getFullYear(); });

  // Holiday countdown (days until Dec 25 + suggested booking deadline)
  var cd = document.querySelector('[data-countdown]');
  if (cd) {
    var now = new Date();
    var xmas = new Date(now.getFullYear(), 11, 25);
    if (now > xmas) xmas = new Date(now.getFullYear() + 1, 11, 25);
    var diff = xmas - now;
    var days = Math.floor(diff / 864e5), hrs = Math.floor(diff % 864e5 / 36e5), mins = Math.floor(diff % 36e5 / 6e4);
    cd.innerHTML = '<div><b>' + days + '</b><span>days</span></div><div><b>' + hrs + '</b><span>hours</span></div><div><b>' + mins + '</b><span>minutes</span></div>';
    var slot = document.querySelector('[data-book-by]');
    if (slot) {
      var bookBy = new Date(xmas); bookBy.setDate(bookBy.getDate() - 14);
      slot.textContent = bookBy.toLocaleDateString('en-US', { month: 'long', day: 'numeric' });
    }
  }

  // Price estimator
  var PRICES = { small: 6, medium: 10, large: 16, oversized: 25 };
  var ADDONS = { notes: 2, logo: 1.5, luxe: 4 };
  function money(n) { return '$' + Math.round(n).toLocaleString('en-US'); }
  function volumeRate(total) { if (total >= 250) return 0.25; if (total >= 100) return 0.2; if (total >= 25) return 0.1; return 0; }

  document.querySelectorAll('[data-estimator]').forEach(function (form) {
    var out = form.querySelector('[data-amount]');
    var brk = form.querySelector('[data-breakdown]');
    var save = form.querySelector('[data-save]');
    var link = form.querySelector('[data-quote-link]');
    function calc() {
      var counts = {}, total = 0, subtotal = 0;
      Object.keys(PRICES).forEach(function (k) {
        var el = form.querySelector('[name="' + k + '"]');
        var n = el ? Math.max(0, parseInt(el.value, 10) || 0) : 0;
        counts[k] = n; total += n; subtotal += n * PRICES[k];
        var lbl = form.querySelector('[data-count="' + k + '"]'); if (lbl) lbl.textContent = n;
      });
      var addons = 0;
      Object.keys(ADDONS).forEach(function (k) {
        var el = form.querySelector('[name="addon_' + k + '"]');
        if (el && el.checked) addons += total * ADDONS[k];
      });
      var rate = volumeRate(total);
      var discount = subtotal * rate;
      var rush = form.querySelector('[name="rush"]');
      var rushFee = (rush && rush.checked) ? (subtotal - discount + addons) * 0.25 : 0;
      var est = subtotal - discount + addons + rushFee;
      if (out) out.textContent = total ? money(est * 0.95) + ' – ' + money(est * 1.1) : '$0';
      if (brk) {
        var parts = [];
        if (total) parts.push(total + ' gift' + (total === 1 ? '' : 's') + ' wrapped');
        if (discount) parts.push(Math.round(rate * 100) + '% volume discount applied');
        if (addons) parts.push('add-ons ' + money(addons));
        if (rushFee) parts.push('rush +25%');
        brk.textContent = parts.length ? parts.join(' · ') : 'Add a few gifts to see an estimate.';
      }
      if (save) { save.hidden = !discount; if (discount) save.textContent = 'You save ' + money(discount) + ' with volume pricing'; }
      if (link) {
        var q = 'contact.html?gifts=' + total + '&small=' + counts.small + '&medium=' + counts.medium + '&large=' + counts.large + '&oversized=' + counts.oversized + '&estimate=' + encodeURIComponent(out ? out.textContent : '');
        link.setAttribute('href', q);
      }
    }
    form.addEventListener('input', calc); form.addEventListener('change', calc); calc();
  });

  // Pre-fill contact form from estimator link
  var contactForm = document.querySelector('form[data-contact]');
  if (contactForm) {
    var p = new URLSearchParams(location.search);
    var gifts = p.get('gifts');
    var msg = contactForm.querySelector('[name="message"]');
    var count = contactForm.querySelector('[name="gift_count"]');
    if (gifts && count && !count.value) count.value = gifts;
    if (gifts && msg && !msg.value) {
      msg.value = 'Estimate from your website: ' + (p.get('estimate') || '') + '\n' +
        'Small: ' + (p.get('small') || 0) + ', Medium: ' + (p.get('medium') || 0) + ', Large: ' + (p.get('large') || 0) + ', Oversized: ' + (p.get('oversized') || 0) + '\n\n';
    }
    var type = p.get('type'); var sel = contactForm.querySelector('[name="client_type"]');
    if (type && sel) sel.value = type;
    // mailto fallback: builds an email if the form endpoint is unreachable (works offline / before form activation)
    var fallback = contactForm.querySelector('[data-mailto]');
    if (fallback) {
      fallback.addEventListener('click', function (e) {
        e.preventDefault();
        var fd = new FormData(contactForm), lines = [];
        fd.forEach(function (v, k) { if (k.charAt(0) !== '_' && v) lines.push(k.replace(/_/g, ' ') + ': ' + v); });
        location.href = 'mailto:abthearp@gmail.com?subject=' + encodeURIComponent('Gift wrapping quote request') + '&body=' + encodeURIComponent(lines.join('\n'));
      });
    }
  }

  // Testimonial rotator (only on small screens where the grid collapses)
  var quotes = document.querySelectorAll('.quotes .quote');
  if (quotes.length > 1 && window.matchMedia('(max-width:560px)').matches && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    var i = 0; quotes.forEach(function (q, idx) { q.style.display = idx ? 'none' : ''; });
    setInterval(function () { quotes[i].style.display = 'none'; i = (i + 1) % quotes.length; quotes[i].style.display = ''; }, 6000);
  }
})();
