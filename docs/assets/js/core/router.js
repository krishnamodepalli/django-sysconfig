export function initRouter(reinitCallback) {
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
      const urlPath = url.split('#')[0];
      const normalizedUrl = urlPath.endsWith('/') ? urlPath : urlPath + '/';
      document.querySelectorAll('.slink').forEach(link => {
        const href = link.getAttribute('href');
        link.classList.toggle('active', normalizedUrl === href);
      });

      // Open the group containing the new active link; close all others
      document.querySelectorAll('.sg:not(.sg-flat)').forEach(function (group) {
        group.classList.toggle('closed', !group.querySelector('.slink.active'));
      });

      if (push) history.pushState({ url }, doc.title, url);

      window.scrollTo(0, 0);
      if (reinitCallback) reinitCallback();
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

    // Allow default browser behavior for modifier keys
    if (e.ctrlKey || e.metaKey || e.altKey || e.shiftKey) return;

    var href = link.getAttribute('href');
    if (!href || href.startsWith('http') || href.startsWith('#')) return;

    // Internal link
    e.preventDefault();
    navigate(href);
  });

  return { navigate };
}
