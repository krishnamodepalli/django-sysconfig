(function () {
  'use strict';

  const { isWatch, pathPrefix } = window.DOCS_CONFIG || { isWatch: false, pathPrefix: '' };

  // ── Components ─────────────────────────────────────────────────────────────

  function initSidebar() {
    document.querySelectorAll('.sg-hdr').forEach(function (h) {
      h.onclick = function () { h.closest('.sg').classList.toggle('closed'); };
    });

    var sb = document.getElementById('sidebar'),
        mob = document.getElementById('mob-overlay'),
        ham = document.getElementById('hamburger');

    function closeSb() { sb.classList.remove('open'); mob.classList.remove('open'); }
    if (ham) ham.onclick = function () { sb.classList.toggle('open'); mob.classList.toggle('open'); };
    if (mob) mob.onclick = closeSb;
  }

  function initScrollSpy() {
    var links = Array.from(document.querySelectorAll('.toc-item[data-id]'));
    if (!links.length) return;
    var headers = links.map(function (l) { return document.getElementById(l.dataset.id); }).filter(Boolean);
    var activeIdx = -1;

    function spy() {
      var top = window.scrollY + 100;
      var newIdx = -1;
      for (var i = 0; i < headers.length; i++) {
        if (headers[i].offsetTop <= top) newIdx = i;
        else break;
      }
      if (newIdx === -1 && headers.length > 0) newIdx = 0;
      if (newIdx !== activeIdx) {
        links.forEach(function (l, i) { l.classList.toggle('active', i === newIdx); });
        activeIdx = newIdx;
      }
    }
    window.addEventListener('scroll', spy);
    spy();
    links.forEach(function (l) { l.onclick = closeSearch; });
  }

  function initTables() {
    document.querySelectorAll('.md table').forEach(function (t) {
      if (t.parentNode.className === 'table-wrap') return;
      var w = document.createElement('div'); w.className = 'table-wrap';
      t.parentNode.insertBefore(w, t); w.appendChild(t);
    });
  }

  // ── Global Search ──
  var overlay = document.getElementById('search-overlay'),
      input = document.getElementById('search-input'),
      hitsEl = document.getElementById('search-hits'),
      btn = document.getElementById('search-btn');
  var idx = null, kbI = -1;

  function openSearch() {
    overlay.classList.add('open');
    input.focus();
    input.select();
    if (!idx) loadIdx();
  }
  function closeSearch() { overlay.classList.remove('open'); kbI = -1; }

  if (btn) btn.onclick = openSearch;
  if (overlay) overlay.onclick = function (e) { if (e.target === overlay) closeSearch(); };
  var esc = document.querySelector('.sm-esc');
  if (esc) esc.onclick = closeSearch;

  if (hitsEl) hitsEl.onclick = function(e) { if (e.target.closest('.sh-hit')) closeSearch(); };

  function loadIdx() {
    fetch(pathPrefix + '/search-index.json')
      .then(function (r) { return r.json(); })
      .then(function (data) {
        idx = data;
        var q = sessionStorage.getItem('docs-search') || '';
        if (q) { input.value = q; runSearch(q); }
      });
  }

  if (input) input.oninput = function () {
    kbI = -1;
    var q = input.value.trim();
    sessionStorage.setItem('docs-search', q);
    runSearch(q);
  };

  // ... (lev, score, hl, runSearch logic remains same as before) ...
  function lev(a, b) {
    if (a.length < b.length) { var tmp = a; a = b; b = tmp; }
    if (b.length === 0) return a.length;
    var prev = Array.from({ length: b.length + 1 }, function (_, i) { return i; });
    for (var i = 0; i < a.length; i++) {
      var curr = [i + 1];
      for (var j = 0; j < b.length; j++) {
        curr.push(Math.min(prev[j + 1] + 1, curr[j] + 1, prev[j] + (a[i] === b[j] ? 0 : 1)));
      }
      prev = curr;
    }
    return prev[b.length];
  }

  function score(target, query) {
    if (!target || !query) return 0;
    var t = target.toLowerCase(), q = query.toLowerCase();
    if (t === q) return 10000;
    var idx = t.indexOf(q);
    if (idx !== -1) {
      var s = 5000;
      if (idx === 0) s += 2000;
      else if (t[idx - 1] === ' ' || t[idx - 1] === '.') s += 1500;
      return s + (q.length * 20) - idx;
    }
    var qTokens = q.split(/\s+/).filter(function (x) { return x.length > 1; });
    if (!qTokens.length) return 0;
    var tTokens = t.split(/[^a-z0-9]+/).filter(Boolean);
    if (q.length >= 2 && q.length <= 4) {
      var acronym = tTokens.map(function (tt) { return tt[0]; }).join('').slice(0, q.length);
      if (acronym === q) return 8000;
    }
    var total = 0, matches = 0;
    qTokens.forEach(function (qt) {
      var best = 0;
      tTokens.forEach(function (tt) {
        if (tt === qt) { best = Math.max(best, 1000); }
        else if (tt.indexOf(qt) === 0) { best = Math.max(best, 800); }
        else if (tt.indexOf(qt) !== -1) { best = Math.max(best, 400); }
        else if (qt.length > 2) {
          var d = lev(tt, qt);
          if (d === 1) best = Math.max(best, 300);
        }
      });
      if (best > 0) { total += best; matches++; }
    });
    if (matches === 0) return 0;
    return (total / qTokens.length) * (matches / qTokens.length);
  }

  function hl(text, q) {
    if (!q) return text;
    var tokens = q.toLowerCase().split(/\s+/).filter(function (x) { return x.length > 1; });
    if (!tokens.length) return text;
    var out = text;
    tokens.forEach(function (t) {
      var safe = t.replace(/[-\[\]{}()*+?.,\\^$|#\s]/g, '\\$&');
      try { out = out.replace(new RegExp('(' + safe + ')', 'gi'), '<mark>$1</mark>'); } catch (e) { }
    });
    return out;
  }

  function runSearch(q) {
    if (!q) { hitsEl.innerHTML = ''; return; }
    if (!idx) { hitsEl.innerHTML = '<div class="sh-empty">Loading…</div>'; return; }
    var scored = idx
      .map(function (item) {
        var sTitle = score(item.title, q);
        var sExcerpt = item.excerpt ? score(item.excerpt, q) : 0;
        var s = (sTitle * 2.0) + (sExcerpt * 0.5);
        return { item: item, s: s };
      })
      .filter(function (x) { return x.s > 50; })
      .sort(function (a, b) { return b.s - a.s; })
      .slice(0, 12);
    if (!scored.length) {
      hitsEl.innerHTML = '<div class="sh-empty"><svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>No results for <strong>' + q + '</strong></div>';
      return;
    }
    var groups = {};
    scored.forEach(function (x) {
      var k = x.item.pageSlug;
      if (!groups[k]) groups[k] = { label: x.item.group, page: x.item.pageTitle, items: [] };
      groups[k].items.push(x);
    });
    var html = '';
    var pageIco = '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>';
    var hIco = '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="4" y1="6" x2="20" y2="6"/><line x1="4" y1="12" x2="14" y2="12"/></svg>';
    Object.keys(groups).forEach(function (slug) {
      var g = groups[slug];
      html += '<div class="sh-group-lbl">' + g.label + ' — ' + g.page + '</div>';
      g.items.forEach(function (x) {
        var isH = x.item.type === 'heading';
        var href = x.item.url + (isH && x.item.id ? '#' + x.item.id : '');
        var excerpt = x.item.excerpt ? '<div class="sh-hit-excerpt">' + hl(x.item.excerpt, q) + '</div>' : '';
        html += '<a class="sh-hit' + (isH ? ' is-h' : '') + '" href="' + href + '">'
          + '<div class="sh-hit-icon">' + (isH ? hIco : pageIco) + '</div>'
          + '<div class="sh-hit-body"><div class="sh-hit-title">' + hl(x.item.title, q) + '</div>'
          + '<div class="sh-hit-meta">' + g.page + (isH ? ' · ' + g.label : '') + '</div>'
          + excerpt + '</div></a>';
      });
    });
    hitsEl.innerHTML = html;
  }

  // ── Navigation Engine (SPA) ────────────────────────────────────────────────

  async function navigate(url, push = true) {
    try {
      const response = await fetch(url);
      const html = await response.text();
      const parser = new DOMParser();
      const doc = parser.parseFromString(html, 'text/html');

      // Update title
      document.title = doc.title;

      // Update content and TOC
      document.getElementById('content').innerHTML = doc.getElementById('content').innerHTML;
      document.getElementById('toc').innerHTML = doc.getElementById('toc').innerHTML;

      // Update Sidebar active state
      document.querySelectorAll('.slink').forEach(link => {
        const href = link.getAttribute('href');
        link.classList.toggle('active', url.endsWith(href) || url === href);
      });

      if (push) history.pushState({ url }, doc.title, url);

      window.scrollTo(0, 0);
      reinit();
    } catch (err) {
      console.error('Navigation failed', err);
      window.location.href = url; // Fallback
    }
  }

  window.onpopstate = function (e) {
    if (e.state && e.state.url) navigate(e.state.url, false);
  };

  document.addEventListener('click', function (e) {
    var link = e.target.closest('a');
    if (!link) return;

    var href = link.getAttribute('href');
    if (!href || href.startsWith('http') || href.startsWith('#')) return;

    // Internal link
    e.preventDefault();
    navigate(href);
  });

  // ── Lifecycle ──────────────────────────────────────────────────────────────

  function reinit() {
    initTables();
    initScrollSpy();
  }

  function bootstrap() {
    initSidebar();
    reinit();

    // Keybinds
    document.addEventListener('keydown', function (e) {
      if ((e.ctrlKey || e.metaKey) && e.code === 'KeyK') { e.preventDefault(); openSearch(); }
      if (e.key === 'Escape' && overlay.classList.contains('open')) closeSearch();
      if (overlay.classList.contains('open')) {
        if (e.key === 'ArrowDown') { e.preventDefault(); shiftKb(1); }
        if (e.key === 'ArrowUp') { e.preventDefault(); shiftKb(-1); }
        if (e.key === 'Enter') { e.preventDefault(); activateKb(); }
      }
    });

    if (isWatch) {
      (function () {
        var ws = new WebSocket('ws://' + window.location.hostname + ':35729');
        ws.onmessage = function (msg) { if (msg.data === 'reload') window.location.reload(); };
      })();
    }
  }

  bootstrap();
})();
