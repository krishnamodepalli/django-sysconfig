import { score, hl } from './fuzzy-search.js';

export function initSearch(searchIndexUrl) {
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

  function closeSearch() {
    overlay.classList.remove('open');
    kbI = -1;
  }

  if (btn) btn.onclick = openSearch;
  if (overlay) overlay.onclick = function (e) { if (e.target === overlay) closeSearch(); };
  var esc = document.querySelector('.sm-esc');
  if (esc) esc.onclick = closeSearch;

  if (hitsEl) hitsEl.onclick = function (e) {
    if (e.target.closest('.sh-hit')) closeSearch();
  };

  function loadIdx() {
    fetch(searchIndexUrl)
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
      html += '<div class="sh-group-lbl">' + (g.label ? g.label + ' — ' : '') + g.page + '</div>';
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

  // Keydown global listener for search
  document.addEventListener('keydown', function (e) {
    if ((e.ctrlKey || e.metaKey) && e.code === 'KeyK') { e.preventDefault(); openSearch(); }
    if (e.key === 'Escape' && overlay.classList.contains('open')) closeSearch();
    if (overlay.classList.contains('open')) {
      if (e.key === 'ArrowDown') { e.preventDefault(); shiftKb(1); }
      if (e.key === 'ArrowUp') { e.preventDefault(); shiftKb(-1); }
      if (e.key === 'Enter') { e.preventDefault(); activateKb(); }
    }
  });

  function shiftKb(d) {
    var els = hitsEl.querySelectorAll('.sh-hit'); if (!els.length) return;
    els[kbI] && els[kbI].classList.remove('kb-focus');
    kbI = Math.max(0, Math.min(els.length - 1, kbI + d));
    els[kbI].classList.add('kb-focus'); els[kbI].scrollIntoView({ block: 'nearest' });
  }
  function activateKb() { var el = hitsEl.querySelector('.sh-hit.kb-focus'); if (el) el.click(); }

  return { closeSearch };
}
