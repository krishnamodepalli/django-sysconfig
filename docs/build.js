#!/usr/bin/env node
'use strict';

/**
 * docsite build.js — static docs generator
 * Usage:  node build.js [--watch]
 * Output: dist/<slug>.html  +  dist/search-index.json  +  dist/index.html
 */

const fs   = require('fs');
const path = require('path');
const { marked } = require('marked');
const hljs       = require('highlight.js');
const matter     = require('gray-matter');

// ── Config ───────────────────────────────────────────────────────────────────
const IS_WATCH = process.argv.includes('--watch');
const ROOT     = process.cwd(); // Assume run from docs/ folder

const configPath = path.resolve(ROOT, 'docs.config.js');
if (!fs.existsSync(configPath)) {
  console.error(`docs.config.js not found at ${configPath}. Run this from your docs folder.`);
  process.exit(1);
}

// Clear cache if watching so we can reload config
function getConfig() {
  if (require.cache[configPath]) delete require.cache[configPath];
  return require(configPath);
}

let cfg = getConfig();
const PATH_PREFIX = process.env.PATH_PREFIX || cfg.pathPrefix || '';
const DOCS_DIR    = path.resolve(ROOT, cfg.docsDir || 'docs');
const OUT_DIR     = path.resolve(ROOT, cfg.outDir  || 'dist');

let allPages = [];
function refreshPages() {
  allPages = cfg.nav.flatMap(g => g.pages.map(p => ({ ...p, group: g.label })));
}
refreshPages();

const slugToHref = s => `${PATH_PREFIX}/${s}/`;
const slugToFile = s => path.join(OUT_DIR, s, 'index.html');
const mdFile     = s => path.join(DOCS_DIR, `${s}.md`);
const ensureDir  = p => { if (!fs.existsSync(p)) fs.mkdirSync(p, { recursive: true }); };
const write      = (f, c) => { ensureDir(path.dirname(f)); fs.writeFileSync(f, c, 'utf8'); };
const escHtml    = s => s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');

// ── Marked Configuration ──────────────────────────────────────────────────────
marked.use({
  gfm: true,
  breaks: false,
  renderer: {
    heading({ text, depth }) {
      const raw = text.replace(/<[^>]*>/g, '');
      const id  = raw.toLowerCase().replace(/[^\w\s-]/g,'').trim().replace(/\s+/g,'-');
      return `<h${depth} id="${id}">${text}<a class="heading-anchor" href="#${id}" aria-hidden="true" tabindex="-1">#</a></h${depth}>\n`;
    },
    code({ text, lang }) {
      const language = (lang || 'plaintext').split(/\s/)[0];
      let hl;
      try {
        hl = hljs.getLanguage(language)
          ? hljs.highlight(text, { language }).value
          : hljs.highlightAuto(text).value;
      } catch { hl = escHtml(text); }
      return (
        `<div class="code-block">\n` +
        `  <div class="code-header">\n` +
        `    <span class="code-lang">${language}</span>\n` +
        `    <button class="copy-btn" aria-label="Copy code" data-tooltip="Copy">` +
        `<svg class="ico-copy" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>` +
        `<svg class="ico-check" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>` +
        `</button>\n` +
        `  </div>\n` +
        `  <pre><code class="hljs language-${language}">${hl}</code></pre>\n` +
        `</div>\n`
      );
    },
    link({ href, title, text }) {
      let outHref = href;
      if (href.startsWith('/') && !href.startsWith('//')) {
        outHref = `${PATH_PREFIX}${href}`;
      }
      return `<a href="${outHref}"${title ? ` title="${title}"` : ''}>${text}</a>`;
    },
  },
});

// ── Callout blocks  :::type … ::: ─────────────────────────────────────────────
const CALLOUT = {
  note:    { icon: '💡', label: 'Note'    },
  tip:     { icon: '✅', label: 'Tip'     },
  warning: { icon: '⚠️',  label: 'Warning' },
  danger:  { icon: '🚨', label: 'Danger'  },
};

function parseCallouts(md) {
  return md.replace(/^:::(\w+)[^\n]*\n([\s\S]*?)^:::/gm, (_, type, body) => {
    const t = type.toLowerCase();
    if (!CALLOUT[t]) return _;
    const { icon, label } = CALLOUT[t];
    const inner = marked.parse(body.trim());
    return (
      `\n<div class="callout callout-${t}" role="note">\n` +
      `  <span class="callout-icon" aria-hidden="true">${icon}</span>\n` +
      `  <div class="callout-body"><p class="callout-title">${label}</p>${inner}</div>\n` +
      `</div>\n`
    );
  });
}

// ── TOC extraction ─────────────────────────────────────────────────────────────
function extractTOC(html) {
  const items = [];
  const re    = /<h([23]) id="([^"]+)">(.+?)<a class="heading-anchor"/g;
  let m;
  while ((m = re.exec(html)) !== null)
    items.push({ level: +m[1], id: m[2], text: m[3].replace(/<[^>]*>/g, '') });
  return items;
}

// ── Search index ───────────────────────────────────────────────────────────────
function stripHtml(html) {
  return html.replace(/<[^>]*>/g,' ').replace(/\s+/g,' ').trim();
}

function buildPageIndex(slug, title, group, html) {
  const url     = slugToHref(slug);
  const entries = [];

  entries.push({
    type: 'page', pageSlug: slug, pageTitle: title, group,
    url, id: null, title,
    excerpt: stripHtml(html).slice(0, 180),
  });

  const re = /<h[23] id="([^"]+)">(.+?)<a class="heading-anchor"/g;
  let m;
  while ((m = re.exec(html)) !== null) {
    const id      = m[1];
    const hText   = m[2].replace(/<[^>]*>/g, '');
    const after   = html.slice(m.index + m[0].length, m.index + m[0].length + 800);
    const excerpt = stripHtml(after).slice(0, 150);
    entries.push({ type: 'heading', pageSlug: slug, pageTitle: title, group, url, id, title: hText, excerpt });
  }
  return entries;
}

// ── CSS & JS ──────────────────────────────────────────────────────────────────
function getCSS() {
  return `
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
html{font-size:16px;scroll-behavior:smooth;-webkit-text-size-adjust:100%}
:root{
  --p:hsl(200,98%,39%);--p-light:hsl(200,98%,95%);--p-mid:hsl(200,60%,85%);
  --p-dark:hsl(200,98%,28%);--p-muted:hsl(200,40%,55%);
  --bg:hsl(200,18%,97%);--bg-sb:hsl(200,14%,96%);--bg-card:#fff;
  --bg-hov:hsl(200,28%,93%);--bg-act:hsl(200,55%,91%);
  --bdr:hsl(200,14%,88%);--bdr-hi:hsl(200,14%,78%);
  --tx:hsl(210,18%,15%);--tx-2:hsl(210,12%,32%);--tx-3:hsl(210,10%,48%);--tx-4:hsl(210,8%,65%);
  --sb-w:260px;--toc-w:210px;--hdr-h:52px;
  --r:6px;--r-lg:10px;
  --sh-sm:0 1px 3px hsl(200 25% 55%/.12);
  --sh-md:0 4px 16px hsl(200 25% 45%/.11);
  --sh-lg:0 8px 32px hsl(200 25% 40%/.15);
  --ease:140ms ease;
  --font:'DM Sans',sans-serif;--serif:'Newsreader',serif;--mono:'IBM Plex Mono',monospace;
}
body{font-family:var(--font);background:var(--bg);color:var(--tx);line-height:1.65;min-height:100vh}

/* ── header ── */
#hdr{position:fixed;inset:0 0 auto 0;height:var(--hdr-h);z-index:200;
  background:var(--bg-card);border-bottom:1px solid var(--bdr);
  display:flex;align-items:center;padding:0 1.2rem;gap:.8rem;box-shadow:var(--sh-sm)}
#hamburger{display:none;background:none;border:none;cursor:pointer;padding:5px;
  border-radius:var(--r);color:var(--tx-3);transition:background var(--ease)}
#hamburger:hover{background:var(--bg-hov);color:var(--tx)}
.logo{display:flex;align-items:center;gap:.5rem;text-decoration:none;color:inherit;flex-shrink:0}
.logo-mark{width:27px;height:27px;border-radius:7px;background:var(--p);
  display:flex;align-items:center;justify-content:center;flex-shrink:0}
.logo-mark svg{color:#fff}
.logo-name{font-family:var(--serif);font-size:1.02rem;font-weight:500;
  letter-spacing:-.015em;white-space:nowrap}
.logo-name b{color:var(--p);font-weight:500}
.logo-ver{font-size:.68rem;color:var(--tx-4);font-family:var(--mono);
  align-self:flex-end;padding-bottom:2px;margin-left:.1rem}
.hdr-gap{flex:1;min-width:.5rem}
#search-btn{display:flex;align-items:center;gap:.55rem;background:var(--bg);
  border:1px solid var(--bdr);border-radius:20px;padding:.32rem .85rem .32rem .7rem;
  cursor:pointer;font-family:var(--font);font-size:.81rem;color:var(--tx-3);white-space:nowrap;
  transition:border-color var(--ease),box-shadow var(--ease),color var(--ease)}
#search-btn:hover{border-color:var(--p-muted);color:var(--tx);box-shadow:0 0 0 3px hsl(200 98% 39%/.1)}
#search-btn svg{color:var(--tx-4);flex-shrink:0}
.kbd-wrap{display:flex;align-items:center;gap:2px;margin-left:.45rem}
.kbd-wrap kbd{font-family:var(--mono);font-size:.63rem;background:var(--bg-card);
  border:1px solid var(--bdr-hi);border-radius:3px;padding:1px 4px;
  color:var(--tx-4);box-shadow:0 1px 0 var(--bdr-hi);line-height:1.4}
.hdr-icon-link{color:var(--tx-3);display:flex;align-items:center;margin-left:.25rem;
  transition:color var(--ease)}
.hdr-icon-link:hover{color:var(--p)}

/* ── search overlay ── */
#search-overlay{position:fixed;inset:0;background:hsl(210 20% 8%/.55);
  z-index:600;display:none;align-items:flex-start;justify-content:center;
  padding-top:clamp(4rem,10vh,7rem);backdrop-filter:blur(4px)}
#search-overlay.open{display:flex;animation:so-in .13s ease}
@keyframes so-in{from{opacity:0}to{opacity:1}}
#search-modal{background:var(--bg-card);border:1px solid var(--bdr);border-radius:var(--r-lg);
  box-shadow:var(--sh-lg);width:min(600px,calc(100vw - 2rem));overflow:hidden;
  animation:sm-in .15s ease}
@keyframes sm-in{from{transform:translateY(-6px);opacity:0}to{transform:none;opacity:1}}
.sm-input-row{display:flex;align-items:center;gap:.7rem;
  padding:.8rem 1rem;border-bottom:1px solid var(--bdr)}
.sm-input-row svg{color:var(--tx-4);flex-shrink:0}
#search-input{flex:1;background:none;border:none;outline:none;
  font-family:var(--font);font-size:.97rem;color:var(--tx);caret-color:var(--p)}
#search-input::placeholder{color:var(--tx-4)}
.sm-esc{font-family:var(--mono);font-size:.7rem;background:var(--bg);border:1px solid var(--bdr);
  border-radius:4px;padding:2px 6px;color:var(--tx-4);cursor:pointer;flex-shrink:0}
#search-hits{max-height:420px;overflow-y:auto;padding:.45rem}
.sh-empty{padding:2rem 1rem;text-align:center;color:var(--tx-3);font-size:.875rem}
.sh-empty svg{display:block;margin:0 auto .55rem;color:var(--tx-4)}
.sh-group-lbl{font-size:.67rem;font-weight:600;letter-spacing:.07em;text-transform:uppercase;
  color:var(--tx-4);padding:.55rem .6rem .22rem}
.sh-hit{display:flex;align-items:flex-start;gap:.7rem;padding:.55rem .65rem;
  border-radius:var(--r);cursor:pointer;text-decoration:none;color:inherit;
  transition:background var(--ease)}
.sh-hit:hover,.sh-hit.kb-focus{background:var(--p-light)}
.sh-hit-icon{width:26px;height:26px;border-radius:var(--r);background:var(--bg);
  border:1px solid var(--bdr);display:flex;align-items:center;
  justify-content:center;flex-shrink:0;color:var(--tx-3);margin-top:1px}
.sh-hit.is-h .sh-hit-icon{background:var(--p-light);border-color:var(--p-mid);color:var(--p)}
.sh-hit-body{flex:1;min-width:0}
.sh-hit-title{font-size:.862rem;font-weight:500;color:var(--tx);
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.sh-hit-title mark,.sh-hit-excerpt mark{background:none;color:var(--p);font-weight:600}
.sh-hit-meta{font-size:.76rem;color:var(--tx-3);margin-top:.08rem;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.sh-hit-excerpt{font-size:.76rem;color:var(--tx-3);margin-top:.12rem;
  display:-webkit-box;-webkit-line-clamp:1;-webkit-box-orient:vertical;overflow:hidden}
.sm-footer{border-top:1px solid var(--bdr);padding:.5rem .9rem;display:flex;
  align-items:center;gap:.35rem;justify-content:flex-end;font-size:.7rem;color:var(--tx-4);flex-wrap:wrap}
.sm-footer kbd{font-family:var(--mono);background:var(--bg);border:1px solid var(--bdr);
  border-radius:3px;padding:1px 4px;font-size:.62rem;margin:0 1px}

/* ── layout ── */
#layout{display:flex;padding-top:var(--hdr-h);min-height:100vh}

/* ── sidebar ── */
#sidebar{position:fixed;top:var(--hdr-h);bottom:0;left:0;width:var(--sb-w);
  background:var(--bg-sb);border-right:1px solid var(--bdr);
  overflow-y:auto;padding:1.2rem 0 3rem;
  scrollbar-width:thin;scrollbar-color:var(--bdr-hi) transparent;
  transition:transform .25s cubic-bezier(.4,0,.2,1);z-index:190}
.sg{margin-bottom:.1rem}
.sg-hdr{display:flex;align-items:center;justify-content:space-between;
  padding:.42rem .95rem .42rem 1.15rem;cursor:pointer;user-select:none;
  color:var(--tx-3);font-size:.675rem;font-weight:600;letter-spacing:.08em;
  text-transform:uppercase;transition:color var(--ease)}
.sg-hdr:hover{color:var(--p)}
.sg-chev{transition:transform .18s ease;color:var(--tx-4);flex-shrink:0}
.sg.closed .sg-chev{transform:rotate(-90deg)}
.sg-items{overflow:hidden;transition:max-height .2s ease;max-height:1000px}
.sg.closed .sg-items{max-height:0}
.slink{display:block;padding:.38rem 1.15rem;text-decoration:none;font-size:.855rem;
  color:var(--tx-3);border-left:2px solid transparent;
  transition:color var(--ease),background var(--ease),border-color var(--ease)}
.slink:hover{color:var(--tx);background:var(--bg-hov)}
.slink.active{color:var(--p);background:var(--bg-act);border-left-color:var(--p);font-weight:500}

/* ── main ── */
#main{margin-left:var(--sb-w);flex:1;display:flex;min-width:0}
#content{flex:1;min-width:0;padding:2.6rem 2.8rem 5rem;max-width:800px}

/* ── toc ── */
#toc{width:var(--toc-w);flex-shrink:0;position:sticky;
  top:calc(var(--hdr-h) + 2rem);align-self:flex-start;padding:0 .65rem;margin-top:2.6rem}
.toc-lbl{font-size:.66rem;font-weight:600;letter-spacing:.08em;text-transform:uppercase;
  color:var(--tx-4);margin-bottom:.55rem;padding-left:.45rem}
.toc-list{list-style:none}
.toc-item a{display:block;padding:.26rem .45rem;font-size:.785rem;color:var(--tx-3);
  text-decoration:none;border-left:2px solid transparent;border-radius:0 var(--r) var(--r) 0;
  transition:color var(--ease),border-color var(--ease),background var(--ease);
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.toc-item a:hover{color:var(--tx);background:var(--bg-hov)}
.toc-item.active a{color:var(--p);border-left-color:var(--p);font-weight:500}
.toc-item.h3 a{padding-left:1rem;font-size:.755rem}

/* ── markdown ── */
.md h1,.md h2,.md h3{scroll-margin-top:calc(var(--hdr-h) + 1.5rem)}
.md h1{font-family:var(--serif);font-size:1.95rem;font-weight:300;letter-spacing:-.025em;
  line-height:1.2;margin-bottom:.45rem;padding-bottom:.6rem;border-bottom:1px solid var(--bdr)}
.md h2{font-family:var(--serif);font-size:1.3rem;font-weight:400;letter-spacing:-.01em;
  margin:2.1rem 0 .6rem;padding-bottom:.38rem;border-bottom:1px solid var(--bdr)}
.md h3{font-size:.965rem;font-weight:600;margin:1.55rem 0 .42rem}
.md h4{font-size:.875rem;font-weight:600;color:var(--tx-3);text-transform:uppercase;
  letter-spacing:.05em;margin:1.15rem 0 .32rem}
.md p{margin-bottom:.9rem}
.md>p:first-of-type{font-size:1rem;color:var(--tx-2)}
.md a{color:var(--p);text-decoration:none;border-bottom:1px solid hsl(200 98% 39%/.3);
  transition:color var(--ease),border-color var(--ease)}
.md a:hover{color:var(--p-dark);border-bottom-color:var(--p)}
.md strong{font-weight:600;color:var(--tx)}
.md em{font-style:italic;color:var(--tx-2)}
.md ul,.md ol{padding-left:1.4rem;margin-bottom:.9rem}
.md li{margin-bottom:.26rem}
.md li>ul,.md li>ol{margin-top:.18rem;margin-bottom:0}
.md input[type=checkbox]{appearance:none;-webkit-appearance:none;width:14px;height:14px;
  border:1.5px solid var(--bdr-hi);border-radius:3px;vertical-align:middle;
  position:relative;top:-1px;cursor:default;flex-shrink:0;background:#fff;
  margin-right:.35rem;transition:background var(--ease),border-color var(--ease)}
.md input[type=checkbox]:checked{background:var(--p);border-color:var(--p)}
.md input[type=checkbox]:checked::after{content:'';position:absolute;left:1px;top:3px;
  width:9px;height:5px;border-left:2px solid #fff;border-bottom:2px solid #fff;
  transform:rotate(-45deg) translateY(-2px)}
.table-wrap{width:100%;overflow-x:auto;margin:1.15rem 0;border-radius:var(--r-lg);
  box-shadow:0 0 0 1px var(--bdr)}
.md table{width:100%;border-collapse:collapse;font-size:.855rem}
.md th{background:var(--bg);font-weight:600;font-size:.765rem;letter-spacing:.03em;
  color:var(--tx-3);text-align:left;padding:.52rem .88rem;border-bottom:1px solid var(--bdr)}
.md td{padding:.48rem .88rem;border-bottom:1px solid var(--bdr)}
.md tr:last-child td{border-bottom:none}
.md tbody tr:hover td{background:hsl(200 40% 99%)}
.md :not(pre)>code{font-family:var(--mono);font-size:.8em;background:var(--p-light);
  color:hsl(200,68%,26%);padding:.12em .36em;border-radius:4px;border:1px solid var(--p-mid)}
.code-block{margin:1.15rem 0;border-radius:var(--r-lg);
  border:1px solid var(--bdr);box-shadow:var(--sh-sm);position:relative}
.code-header{display:flex;align-items:center;justify-content:space-between;
  padding:.42rem .78rem;background:hsl(200,10%,94%);border-bottom:1px solid var(--bdr);
  border-radius:var(--r-lg) var(--r-lg) 0 0}
.code-lang{font-family:var(--mono);font-size:.69rem;color:var(--tx-4);font-weight:500;letter-spacing:.04em}
.copy-btn{position:relative;display:flex;align-items:center;justify-content:center;
  background:none;border:1px solid var(--bdr-hi);border-radius:var(--r);
  width:28px;height:28px;color:var(--tx-3);cursor:pointer;transition:all var(--ease)}
.copy-btn:hover{background:#fff;color:var(--p);border-color:var(--p-muted)}
.copy-btn .ico-check{display:none}
.copy-btn.copied .ico-copy{display:none}
.copy-btn.copied .ico-check{display:flex;color:hsl(145,55%,30%)}
.copy-btn.copied{border-color:hsl(145,45%,70%);background:hsl(145,50%,96%)}

/* CSS Tooltip */
[data-tooltip]{position:relative}
[data-tooltip]::after{content:attr(data-tooltip);position:absolute;bottom:calc(100% + 6px);left:50%;
  transform:translateX(-50%);background:hsl(210,20%,12%);color:#fff;font-size:.65rem;
  padding:.2rem .5rem;border-radius:4px;pointer-events:none;opacity:0;
  transition:opacity .15s ease;white-space:nowrap;z-index:100}
[data-tooltip]:hover::after{opacity:1}
.code-block pre{margin:0;border-radius:0 0 var(--r-lg) var(--r-lg);overflow:hidden}
.code-block pre code{display:block;padding:.9rem 1.05rem;overflow-x:auto;
  font-family:var(--mono);font-size:.83rem;line-height:1.65;background:#fff!important}
.md blockquote{border-left:3px solid var(--p-muted);margin:1.15rem 0;
  padding:.65rem 1.05rem;background:var(--p-light);border-radius:0 var(--r) var(--r) 0;color:var(--tx-2)}
.md blockquote p{margin-bottom:0;font-style:italic}
.md hr{border:none;border-top:1px solid var(--bdr);margin:1.9rem 0}
.md img{max-width:100%;border-radius:var(--r-lg);border:1px solid var(--bdr);
  box-shadow:var(--sh-md);margin:.4rem 0}
.heading-anchor{opacity:0;margin-left:.35rem;font-size:.76em;color:var(--tx-4);
  text-decoration:none;transition:opacity var(--ease);border-bottom:none!important}
h1:hover .heading-anchor,h2:hover .heading-anchor,h3:hover .heading-anchor{opacity:1}

/* ── callouts ── */
.callout{display:flex;gap:.78rem;padding:.82rem .98rem;border-radius:var(--r-lg);
  margin:1.15rem 0;border:1px solid;font-size:.885rem;line-height:1.55}
.callout-icon{font-size:.95rem;flex-shrink:0;margin-top:.06rem}
.callout-body{flex:1;min-width:0}
.callout-body>p{margin:0}
.callout-title{font-weight:600;font-size:.74rem;letter-spacing:.03em;
  text-transform:uppercase;margin-bottom:.28rem!important}
.callout-note  {background:hsl(200,60%,96%);border-color:hsl(200,50%,83%);color:hsl(200,30%,22%)}
.callout-tip   {background:hsl(145,50%,95%);border-color:hsl(145,45%,79%);color:hsl(145,30%,18%)}
.callout-warning{background:hsl(38,80%,95%);border-color:hsl(38,70%,79%);color:hsl(38,40%,20%)}
.callout-danger{background:hsl(0,65%,96%);border-color:hsl(0,55%,83%);color:hsl(0,35%,20%)}

/* ── abbr tooltips ── */
.md abbr{text-decoration:underline dotted var(--p-muted);cursor:help;position:relative}
.md abbr::after{content:attr(title);position:absolute;bottom:calc(100% + 7px);left:50%;
  transform:translateX(-50%);background:hsl(210,20%,12%);color:#fff;font-size:.76rem;
  padding:.28rem .62rem;border-radius:var(--r);pointer-events:none;opacity:0;
  transition:opacity .14s ease;font-style:normal;font-family:var(--font);font-weight:400;
  z-index:50;box-shadow:var(--sh-lg);max-width:210px;white-space:normal;text-align:center;line-height:1.4}
.md abbr::before{content:'';position:absolute;bottom:calc(100% + 2px);left:50%;
  transform:translateX(-50%);border:5px solid transparent;
  border-top-color:hsl(210,20%,12%);pointer-events:none;opacity:0;
  transition:opacity .14s ease;z-index:50}
.md abbr:hover::after,.md abbr:hover::before{opacity:1}

/* ── page nav ── */
.page-nav{display:flex;gap:.8rem;margin-top:2.8rem;padding-top:1.4rem;border-top:1px solid var(--bdr)}
.pnav-btn{flex:1;padding:.75rem .95rem;border:1px solid var(--bdr);border-radius:var(--r-lg);
  text-decoration:none;background:var(--bg-card);display:flex;flex-direction:column;gap:.17rem;
  transition:border-color var(--ease),box-shadow var(--ease)}
.pnav-btn:hover{border-color:var(--p-muted);box-shadow:var(--sh-sm)}
.pnav-btn.right{text-align:right}
.pnav-dir{font-size:.69rem;color:var(--tx-4);text-transform:uppercase;letter-spacing:.06em}
.pnav-title{font-size:.85rem;color:var(--p);font-weight:500}
.breadcrumb{font-size:.77rem;color:var(--tx-4);margin-bottom:.55rem;
  display:flex;align-items:center;gap:.32rem}
.breadcrumb span+span::before{content:'›';margin-right:.32rem}

/* ── mobile overlay ── */
#mob-overlay{position:fixed;inset:0;background:hsl(200 18% 8%/.42);z-index:180;display:none}
#mob-overlay.open{display:block}

/* ── footer ── */
footer{margin-left:var(--sb-w);padding:1.1rem 2.8rem;border-top:1px solid var(--bdr);
  background:var(--bg-sb);display:flex;align-items:center;justify-content:space-between;
  font-size:.77rem;color:var(--tx-4);flex-wrap:wrap;gap:.5rem}
footer a{color:var(--tx-3);text-decoration:none;border-bottom:1px solid var(--bdr)}
footer a:hover{color:var(--p)}

/* ── responsive ── */
@media(max-width:1100px){#toc{display:none}}
@media(max-width:768px){
  #hamburger{display:flex;align-items:center}
  #sidebar{transform:translateX(-100%);box-shadow:var(--sh-md)}
  #sidebar.open{transform:translateX(0)}
  #main{margin-left:0}
  footer{margin-left:0;padding:1rem 1.25rem}
  #content{padding:1.5rem 1.2rem 3.5rem}
  .kbd-wrap{display:none}
}`.trim();
}

function getClientJS() {
  const hotReload = IS_WATCH ? `
  /* Hot reload */
  (function() {
    var ws = new WebSocket('ws://' + window.location.hostname + ':35729');
    ws.onmessage = function(msg) { if (msg.data === 'reload') window.location.reload(); };
  })();` : '';

  return `
(function(){'use strict';
${hotReload}
/* sidebar collapsibles */
document.querySelectorAll('.sg-hdr').forEach(function(h){
  h.addEventListener('click',function(){h.closest('.sg').classList.toggle('closed');});
});
/* mobile sidebar */
var sb=document.getElementById('sidebar'),mob=document.getElementById('mob-overlay'),ham=document.getElementById('hamburger');
function closeSb(){sb.classList.remove('open');mob.classList.remove('open');}
ham&&ham.addEventListener('click',function(){sb.classList.toggle('open');mob.classList.toggle('open');});
mob&&mob.addEventListener('click',closeSb);
/* toc scroll-spy */
var tocItems=Array.from(document.querySelectorAll('.toc-item[data-id]'));
if(tocItems.length){
  var spy=new IntersectionObserver(function(entries){
    entries.forEach(function(e){
      var el=document.querySelector('.toc-item[data-id="'+e.target.id+'"]');
      if(el)el.classList.toggle('active',e.isIntersecting);
    });
  },{rootMargin:'-8% 0px -80% 0px'});
  tocItems.forEach(function(li){
    var h=document.getElementById(li.dataset.id);
    if(h)spy.observe(h);
    // Close search on TOC click
    li.addEventListener('click', closeSearch);
  });
}
/* copy buttons */
document.addEventListener('click', function(e) {
  var btn = e.target.closest('.copy-btn');
  if (!btn) return;
  var block = btn.closest('.code-block');
  if (!block) return;
  var codeEl = block.querySelector('code');
  if (!codeEl) return;
  var code = codeEl.textContent;

  function setFeedback(msg) {
    btn.classList.add('copied');
    btn.setAttribute('data-tooltip', msg);
    setTimeout(function() {
      btn.classList.remove('copied');
      btn.setAttribute('data-tooltip', 'Copy');
    }, 2000);
  }

  if (navigator.clipboard && window.isSecureContext) {
    navigator.clipboard.writeText(code).then(function() {
      setFeedback('Copied!');
    }).catch(function() {
      fallbackCopy(code, setFeedback);
    });
  } else {
    fallbackCopy(code, setFeedback);
  }
});

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
  } catch (err) {}
  document.body.removeChild(ta);
}
/* table overflow wrappers */
document.querySelectorAll('.md table').forEach(function(t){
  var w=document.createElement('div');w.className='table-wrap';
  t.parentNode.insertBefore(w,t);w.appendChild(t);
});

/* ── fuzzy search ── */
var overlay=document.getElementById('search-overlay'),input=document.getElementById('search-input'),
    hitsEl=document.getElementById('search-hits'),btn=document.getElementById('search-btn');
var idx=null,kbI=-1;

function openSearch(){
  overlay.classList.add('open');
  input.focus();
  input.select();
  if(!idx) loadIdx();
}
function closeSearch(){
  overlay.classList.remove('open');
  kbI=-1;
}

btn&&btn.addEventListener('click',openSearch);
overlay.addEventListener('click',function(e){if(e.target===overlay)closeSearch();});
document.querySelector('.sm-esc')&&document.querySelector('.sm-esc').addEventListener('click',closeSearch);

// Close on hit click (event delegation)
hitsEl.addEventListener('click', function(e){
  if(e.target.closest('.sh-hit')) closeSearch();
});

document.addEventListener('keydown',function(e){
  if((e.ctrlKey||e.metaKey)&&e.code==='KeyK'){e.preventDefault();openSearch();}
  if(e.key==='Escape'&&overlay.classList.contains('open'))closeSearch();
  if(overlay.classList.contains('open')){
    if(e.key==='ArrowDown'){e.preventDefault();shiftKb(1);}
    if(e.key==='ArrowUp'){e.preventDefault();shiftKb(-1);}
    if(e.key==='Enter'){e.preventDefault();activateKb();}
  }
});
function shiftKb(d){
  var els=hitsEl.querySelectorAll('.sh-hit');if(!els.length)return;
  els[kbI]&&els[kbI].classList.remove('kb-focus');
  kbI=Math.max(0,Math.min(els.length-1,kbI+d));
  els[kbI].classList.add('kb-focus');els[kbI].scrollIntoView({block:'nearest'});
}
function activateKb(){var el=hitsEl.querySelector('.sh-hit.kb-focus');if(el)el.click();}
function loadIdx(){
  fetch('${PATH_PREFIX}/search-index.json')
    .then(function(r){return r.json();})
    .then(function(data){
      idx=data;
      var q = sessionStorage.getItem('docs-search') || '';
      if(q){ input.value = q; runSearch(q); }
    })
    .catch(function(){idx=[];});
}
input.addEventListener('input',function(){
  kbI=-1;
  var q = input.value.trim();
  sessionStorage.setItem('docs-search', q);
  runSearch(q);
});

function score(str,q){
  str=str.toLowerCase();q=q.toLowerCase();
  if(str===q)return 5000;
  if(str.startsWith(q))return 3000-str.length;
  if(str.includes(q))return 2000-str.indexOf(q);
  var s=0,qi=0,last=-1;
  for(var i=0;i<str.length&&qi<q.length;i++){
    if(str[i]===q[qi]){s+=last===-1?10:(i-last===1?6:2);last=i;qi++;}
  }
  return qi===q.length?s:0;
}
function hl(text,q){
  if(!q)return text;
  var safe=q.replace(/[-\\[\\]{}()*+?.,\\\\^$|#\\s]/g,'\\\\$&');
  try{return text.replace(new RegExp('('+safe+')','gi'),'<mark>$1</mark>');}catch(e){return text;}
}
function runSearch(q){
  if(!q){hitsEl.innerHTML='';return;}
  if(!idx){hitsEl.innerHTML='<div class="sh-empty">Loading…</div>';return;}
  var scored=idx
    .map(function(item){var s=score(item.title,q);if(item.excerpt)s=Math.max(s,score(item.excerpt,q)*0.4);return{item:item,s:s};})
    .filter(function(x){return x.s>0;})
    .sort(function(a,b){return b.s-a.s;})
    .slice(0,10);
  if(!scored.length){
    hitsEl.innerHTML='<div class="sh-empty"><svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>No results for <strong>'+q+'</strong></div>';
    return;
  }
  var groups={};
  scored.forEach(function(x){
    var k=x.item.pageSlug;
    if(!groups[k])groups[k]={label:x.item.group,page:x.item.pageTitle,items:[]};
    groups[k].items.push(x);
  });
  var html='';
  var pageIco='<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>';
  var hIco='<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="4" y1="6" x2="20" y2="6"/><line x1="4" y1="12" x2="14" y2="12"/></svg>';
  Object.keys(groups).forEach(function(slug){
    var g=groups[slug];
    html+='<div class="sh-group-lbl">'+g.label+' \u2014 '+g.page+'</div>';
    g.items.forEach(function(x){
      var isH=x.item.type==='heading';
      var href=x.item.url+(isH&&x.item.id?'#'+x.item.id:'');
      var excerpt=x.item.excerpt?'<div class="sh-hit-excerpt">'+hl(x.item.excerpt,q)+'</div>':'';
      html+='<a class="sh-hit'+(isH?' is-h':'')+'" href="'+href+'">'
        +'<div class="sh-hit-icon">'+(isH?hIco:pageIco)+'</div>'
        +'<div class="sh-hit-body"><div class="sh-hit-title">'+hl(x.item.title,q)+'</div>'
        +'<div class="sh-hit-meta">'+g.page+(isH?' \u00b7 '+g.label:'')+'</div>'
        +excerpt+'</div></a>';
    });
  });
  hitsEl.innerHTML=html;
}
})();`.trim();
}

// ── HTML page template ─────────────────────────────────────────────────────────
function renderPage({ slug, title, description, bodyHtml, tocHtml }) {
  const idx   = allPages.findIndex(p => p.slug === slug);
  const prev  = idx > 0             ? allPages[idx - 1] : null;
  const next  = idx < allPages.length - 1 ? allPages[idx + 1] : null;
  const group = cfg.nav.find(g => g.pages.some(p => p.slug === slug));
  const { name = 'Docs', version = '', repo = '', baseUrl = '' } = cfg.site;

  const sidebarHtml = cfg.nav.map(g => {
    const links = g.pages.map(p =>
      `<a class="slink${p.slug===slug?' active':''}" href="${slugToHref(p.slug)}">${p.title}</a>`
    ).join('');
    return `<div class="sg">\n  <div class="sg-hdr"><span>${g.label}</span>`
      + `<svg class="sg-chev" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="6 9 12 15 18 9"/></svg></div>\n`
      + `  <div class="sg-items">${links}</div>\n</div>`;
  }).join('\n');

  const breadcrumb = group
    ? `<div class="breadcrumb"><span>${group.label}</span><span>${title}</span></div>`
    : '';

  const prevBtn = prev
    ? `<a class="pnav-btn" href="${slugToHref(prev.slug)}"><span class="pnav-dir">← Previous</span><span class="pnav-title">${prev.title}</span></a>`
    : '<div></div>';
  const nextBtn = next
    ? `<a class="pnav-btn right" href="${slugToHref(next.slug)}"><span class="pnav-dir">Next →</span><span class="pnav-title">${next.title}</span></a>`
    : '<div></div>';

  const canon  = baseUrl ? `\n<link rel="canonical" href="${baseUrl}/${slugToHref(slug)}">` : '';
  const ghLink = repo
    ? `<a href="${repo}" class="hdr-icon-link" aria-label="GitHub" target="_blank" rel="noopener">`
      + `<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12c0 4.42 2.87 8.17 6.84 9.49.5.09.68-.22.68-.48v-1.7C6.73 19.91 6.14 18 6.14 18c-.46-1.16-1.11-1.47-1.11-1.47-.91-.62.07-.61.07-.61 1 .07 1.53 1.03 1.53 1.03.9 1.52 2.34 1.08 2.91.83.09-.65.35-1.09.63-1.34-2.22-.25-4.55-1.11-4.55-4.94 0-1.09.39-1.98 1.03-2.68-.1-.25-.45-1.27.1-2.64 0 0 .84-.27 2.75 1.02A9.56 9.56 0 0 1 12 6.8c.85.004 1.71.11 2.51.33 1.91-1.29 2.75-1.02 2.75-1.02.55 1.37.2 2.39.1 2.64.64.7 1.03 1.59 1.03 2.68 0 3.84-2.34 4.68-4.57 4.93.36.31.68.92.68 1.85v2.74c0 .27.18.58.69.48A10.01 10.01 0 0 0 22 12c0-5.52-4.48-10-10-10z"/></svg></a>`
    : '';

  const firstSlug = allPages[0]?.slug ?? '';

  return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>${title} \u2014 ${name} Docs</title>
<meta name="description" content="${description || `${title} \u2014 ${name} documentation`}">${canon}
<meta property="og:title" content="${title} \u2014 ${name} Docs">
<meta property="og:description" content="${description || ''}">
<meta property="og:type" content="article">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=Newsreader:opsz,wght@6..72,300;6..72,400&family=DM+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>${getCSS()}</style>
</head>
<body>

<div id="mob-overlay"></div>

<div id="search-overlay" role="dialog" aria-modal="true" aria-label="Search documentation">
  <div id="search-modal">
    <div class="sm-input-row">
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
      <input id="search-input" type="text" placeholder="Search documentation\u2026" autocomplete="off" spellcheck="false" aria-label="Search">
      <span class="sm-esc" role="button" tabindex="0" aria-label="Close">esc</span>
    </div>
    <div id="search-hits" role="listbox" aria-label="Search results"></div>
    <div class="sm-footer"><kbd>\u2191</kbd><kbd>\u2193</kbd> navigate &nbsp;<kbd>\u21b5</kbd> open &nbsp;<kbd>esc</kbd> close</div>
  </div>
</div>

<header id="hdr">
  <button id="hamburger" aria-label="Open navigation">
    <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
  </button>
  <a href="${PATH_PREFIX}/${firstSlug}/" class="logo" aria-label="${name} docs home">
    <div class="logo-mark" aria-hidden="true">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>
    </div>
    <span class="logo-name"><b>${name}</b> Docs</span>
  </a>
  <span class="logo-ver">${version}</span>
  <div class="hdr-gap"></div>
  <button id="search-btn" aria-label="Search (Ctrl+K)">
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
    Search\u2026
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
  ${repo ? `<a href="${repo}" target="_blank" rel="noopener">GitHub \u2197</a>` : ''}
</footer>

<script>${getClientJS()}</script>
</body>
</html>`;
}

// ── Run build ──────────────────────────────────────────────────────────────────
async function build() {
  const t0 = Date.now();
  console.log('\n📖  Building docs…');
  ensureDir(OUT_DIR);

  const searchIndex = [];

  for (const page of allPages) {
    const src = mdFile(page.slug);
    const rawMd = fs.existsSync(src)
      ? fs.readFileSync(src, 'utf8')
      : `# ${page.title}\n\n> 📝 This page hasn’t been written yet.\n> Create \`${cfg.docsDir||'docs'}/${page.slug}.md\` to get started.\n`;

    const { data: fm, content: mdContent } = matter(rawMd);
    const title       = fm.title       || page.title;
    const description = fm.description || '';

    const bodyHtml = marked.parse(parseCallouts(mdContent));

    const tocItems = extractTOC(bodyHtml);
    const tocHtml  = tocItems.length >= 2
      ? `<div class="toc-lbl">On this page</div>\n<ul class="toc-list">\n`
        + tocItems.map(h =>
            `<li class="toc-item${h.level===3?' h3':''}" data-id="${h.id}"><a href="#${h.id}">${h.text}</a></li>`
          ).join('\n')
        + `\n</ul>`
      : '';

    write(slugToFile(page.slug), renderPage({ slug: page.slug, title, description, bodyHtml, tocHtml }));
    searchIndex.push(...buildPageIndex(page.slug, title, page.group, bodyHtml));
  }

  write(path.join(OUT_DIR, 'search-index.json'), JSON.stringify(searchIndex));

  const first = allPages[0];
  if (first) {
    const rootHref = `${PATH_PREFIX}/${first.slug}/`;
    write(path.join(OUT_DIR, 'index.html'),
      `<!DOCTYPE html><html><head><meta charset="UTF-8">` +
      `<meta http-equiv="refresh" content="0;url=${rootHref}">` +
      `<link rel="canonical" href="${rootHref}"></head>` +
      `<body><a href="${rootHref}">Redirecting…</a></body></html>`
    );
  }

  console.log(`✅  Done in ${Date.now()-t0}ms\n`);
}

// ── Watch mode ───────────────────────────────────────────────────────────────
if (IS_WATCH) {
  const chokidar = require('chokidar');
  const { WebSocketServer } = require('ws');

  const wss = new WebSocketServer({ port: 35729 });
  let clients = new Set();
  wss.on('connection', ws => {
    clients.add(ws);
    ws.on('close', () => clients.delete(ws));
  });

  const broadcastReload = () => {
    for (const client of clients) client.send('reload');
  };

  const watcher = chokidar.watch([DOCS_DIR, configPath], { ignoreInitial: true });

  watcher.on('all', async (event, filePath) => {
    console.log(`\n🔄  Change detected: ${path.relative(ROOT, filePath)}`);
    if (filePath === configPath) {
      cfg = getConfig();
      refreshPages();
    }
    await build();
    broadcastReload();
  });

  build().then(() => {
    console.log('👀  Watching for changes…');
  });
} else {
  build().catch(e => { console.error('\n❌ ', e.message); process.exit(1); });
}
