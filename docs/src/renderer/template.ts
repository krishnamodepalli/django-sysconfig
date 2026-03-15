import { DocsConfig, PageMetadata } from '../types.js';
import {
  buildCanonicalBaseUrl,
  getRelativeRootPrefix,
  toAbsoluteSitePath,
  toRelativeDocHref,
} from '../paths.js';

export function renderPage({
  slug,
  title,
  description,
  bodyHtml,
  tocHtml,
  cfg,
  isWatch
}: {
  slug: string;
  title: string;
  description?: string;
  bodyHtml: string;
  tocHtml: string;
  cfg: DocsConfig;
  allPages: PageMetadata[];
  isWatch: boolean;
}) {
  const { name = 'Docs', version = '', repo = '', baseUrl = '' } = cfg.site;
  const pathPrefix = cfg.pathPrefix || '';
  const relPrefix = getRelativeRootPrefix(slug);
  const slugToHref = (targetSlug: string) => toRelativeDocHref(slug, targetSlug);

  const sidebarHtml = cfg.nav.map(g => {
    const links = g.pages.map(p =>
      `<a class="slink${p.slug===slug?' active':''}" href="${slugToHref(p.slug)}">${p.title}</a>`
    ).join('');
    return `<div class="sg">\n  <div class="sg-hdr"><span>${g.label}</span>`
      + `<svg class="sg-chev" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="6 9 12 15 18 9"/></svg></div>\n`
      + `  <div class="sg-items">${links}</div>\n</div>`;
  }).join('\n');

  const group = cfg.nav.find(g => g.pages.some(p => p.slug === slug));
  const breadcrumb = group
    ? `<div class="breadcrumb"><span>${group.label}</span><span>${title}</span></div>`
    : '';

  const flatPages = cfg.nav.flatMap(g => g.pages);
  const idx = flatPages.findIndex(p => p.slug === slug);
  const prev = idx > 0 ? flatPages[idx - 1] : null;
  const next = idx < flatPages.length - 1 ? flatPages[idx + 1] : null;

  const prevBtn = prev
    ? `<a class="pnav-btn" href="${slugToHref(prev.slug)}"><span class="pnav-dir">← Previous</span><span class="pnav-title">${prev.title}</span></a>`
    : '<div></div>';
  const nextBtn = next
    ? `<a class="pnav-btn right" href="${slugToHref(next.slug)}"><span class="pnav-dir">Next →</span><span class="pnav-title">${next.title}</span></a>`
    : '<div></div>';

  const canonicalBaseUrl = buildCanonicalBaseUrl(baseUrl, pathPrefix);
  const canon = canonicalBaseUrl ? `\n<link rel="canonical" href="${canonicalBaseUrl}/${slug}/">` : '';
  const ghLink = repo
    ? `<a href="${repo}" class="hdr-icon-link" aria-label="GitHub" target="_blank" rel="noopener">`
      + `<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12c0 4.42 2.87 8.17 6.84 9.49.5.09.68-.22.68-.48v-1.7C6.73 19.91 6.14 18 6.14 18c-.46-1.16-1.11-1.47-1.11-1.47-.91-.62.07-.61.07-.61 1 .07 1.53 1.03 1.53 1.03.9 1.52 2.34 1.08 2.91.83.09-.65.35-1.09.63-1.34-2.22-.25-4.55-1.11-4.55-4.94 0-1.09.39-1.98 1.03-2.68-.1-.25-.45-1.27.1-2.64 0 0 .84-.27 2.75 1.02A9.56 9.56 0 0 1 12 6.8c.85.004 1.71.11 2.51.33 1.91-1.29 2.75-1.02 2.75-1.02.55 1.37.2 2.39.1 2.64.64.7 1.03 1.59 1.03 2.68 0 3.84-2.34 4.68-4.57 4.93.36.31.68.92.68 1.85v2.74c0 .27.18.58.69.48A10.01 10.01 0 0 0 22 12c0-5.52-4.48-10-10-10z"/></svg></a>`
    : '';

  const firstSlug = flatPages[0]?.slug ?? '';

  return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>${title} — ${name} Docs</title>
<meta name="description" content="${description || `${title} — ${name} documentation`}">${canon}
<meta property="og:title" content="${title} — ${name} Docs">
<meta property="og:description" content="${description || ''}">
<meta property="og:type" content="article">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=Newsreader:opsz,wght@6..72,300;6..72,400&family=DM+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="${relPrefix}/assets/css/github.min.css">
<link rel="stylesheet" href="${relPrefix}/assets/css/main.css">
</head>
<body>

<div id="mob-overlay"></div>

<div id="search-overlay" role="dialog" aria-modal="true" aria-label="Search documentation">
  <div id="search-modal">
    <div class="sm-input-row">
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
      <input id="search-input" type="text" placeholder="Search documentation…" autocomplete="off" spellcheck="false" aria-label="Search">
      <span class="sm-esc" role="button" tabindex="0" aria-label="Close">esc</span>
    </div>
    <div id="search-hits" role="listbox" aria-label="Search results"></div>
    <div class="sm-footer"><kbd>↑</kbd><kbd>↓</kbd> navigate &nbsp;<kbd>↵</kbd> open &nbsp;<kbd>esc</kbd> close</div>
  </div>
</div>

<header id="hdr">
  <button id="hamburger" aria-label="Open navigation">
    <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
  </button>
  <a href="${slugToHref(firstSlug)}" class="logo" aria-label="${name} docs home">
    <div class="logo-mark" aria-hidden="true">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>
    </div>
    <span class="logo-name"><b>${name}</b> Docs</span>
  </a>
  <span class="logo-ver">${version}</span>
  <div class="hdr-gap"></div>
  <button id="search-btn" aria-label="Search (Ctrl+K)">
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
    Search…
    <span class="kbd-wrap" aria-hidden="true"><kbd>Ctrl</kbd><kbd>K</kbd></span>
  </button>
  ${ghLink}
</header>

<div id="layout">
  <nav id="sidebar" aria-label="Documentation">
    ${sidebarHtml}
  </nav>
  <main id="main">
    <article id="content">
      ${breadcrumb}
      <div class="md">${bodyHtml}</div>
      <nav class="page-nav" aria-label="Page navigation">${prevBtn}${nextBtn}</nav>
    </article>
    <aside id="toc" aria-label="On this page">${tocHtml}</aside>
  </main>
</div>

<footer>
  <span>${name} Docs ${version}</span>
  ${repo ? `<a href="${repo}" target="_blank" rel="noopener">GitHub ↗</a>` : ''}
</footer>

<script>
  window.DOCS_CONFIG = {
    isWatch: ${isWatch},
    pathPrefix: '${pathPrefix}',
    searchIndexUrl: '${toAbsoluteSitePath(pathPrefix, 'search-index.json')}'
  };
</script>
<script src="${relPrefix}/assets/js/main.js" type="module"></script>
</body>
</html>`;
}
