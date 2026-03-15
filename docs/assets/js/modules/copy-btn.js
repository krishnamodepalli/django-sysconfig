export function initCopyButtons() {
  // Use global event delegation so we don't have to re-bind on every navigation
  if (window._copyButtonListenerAdded) return;

  document.addEventListener('click', function (e) {
    var btn = e.target.closest('.copy-btn');
    if (!btn) return;
    var block = btn.closest('.code-block');
    if (!block) return;
    var codeEl = block.querySelector('code');
    if (!codeEl) return;
    var code = codeEl.textContent || '';

    function setFeedback(msg) {
      btn.classList.add('copied');
      btn.setAttribute('data-tooltip', msg);
      setTimeout(function () {
        btn.classList.remove('copied');
        btn.setAttribute('data-tooltip', 'Copy');
      }, 2000);
    }

    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(code).then(function () {
        setFeedback('Copied!');
      }).catch(function () {
        fallbackCopy(code, setFeedback);
      });
    } else {
      fallbackCopy(code, setFeedback);
    }
  });

  window._copyButtonListenerAdded = true;
}

function fallbackCopy(text, cb) {
  var ta = document.createElement('textarea');
  ta.value = text;
  ta.style.position = 'fixed';
  ta.style.opacity = '0';
  document.body.appendChild(ta);
  ta.select();
  try {
    var ok = document.execCommand('copy');
    if (ok) cb('Copied!');
  } catch (err) { }
  document.body.removeChild(ta);
}
