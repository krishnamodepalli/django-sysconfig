export function initScrollSpy(closeSearchCallback) {
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

  // Clean up old listener if any (since we re-init on navigation)
  window.removeEventListener('scroll', window._currentScrollSpy);
  window._currentScrollSpy = spy;
  window.addEventListener('scroll', spy);

  spy();
  if (closeSearchCallback) {
    links.forEach(function (l) { l.onclick = closeSearchCallback; });
  }
}
