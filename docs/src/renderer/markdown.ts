import { marked } from 'marked';
import hljs from 'highlight.js';
import { rewriteRootRelativeUrls } from '../paths.js';

const CALLOUTS: Record<string, { icon: string; label: string }> = {
  note:    { icon: '💡', label: 'Note'    },
  tip:     { icon: '✅', label: 'Tip'     },
  warning: { icon: '⚠️',  label: 'Warning' },
  danger:  { icon: '🚨', label: 'Danger'  },
};

export class MarkdownRenderer {
  private renderer: marked.Renderer;

  constructor() {
    this.renderer = this.createRenderer();
  }

  private createRenderer(): marked.Renderer {
    const renderer = new marked.Renderer();

    renderer.heading = (token) => {
      const text = this.renderer.parser.parseInline(token.tokens);
      const raw = token.text.replace(/<[^>]*>/g, '');
      const id  = raw.toLowerCase().replace(/[^\w\s-]/g,'').trim().replace(/\s+/g,'-');
      return `<h${token.depth} id="${id}">${text}<a class="heading-anchor" href="#${id}" aria-hidden="true" tabindex="-1">#</a></h${token.depth}>\n`;
    };

    renderer.code = ({ text, lang }) => {
      const language = (lang || 'plaintext').split(/\s/)[0];
      let hl: string;
      try {
        hl = hljs.getLanguage(language)
          ? hljs.highlight(text, { language }).value
          : hljs.highlightAuto(text).value;
      } catch {
        hl = text.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
      }
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
    };

    return renderer;
  }

  render(md: string, _slug: string, pathPrefix: string = ''): string {
    const withCallouts = this.parseCallouts(md);
    this.renderer = this.createRenderer();

    const html = marked.parse(withCallouts, { renderer: this.renderer, gfm: true, breaks: false }) as string;
    return rewriteRootRelativeUrls(html, pathPrefix);
  }

  private parseCallouts(md: string): string {
    return md.replace(/^:::(\w+)[^\n]*\n([\s\S]*?)^:::/gm, (_, type, body) => {
      const t = type.toLowerCase();
      if (!CALLOUTS[t]) return _;
      const { icon, label } = CALLOUTS[t];
      const inner = marked.parse(body.trim()) as string;
      return (
        `\n<div class="callout callout-${t}" role="note">\n` +
        `  <span class="callout-icon" aria-hidden="true">${icon}</span>\n` +
        `  <div class="callout-body"><p class="callout-title">${label}</p>${inner}</div>\n` +
        `</div>\n`
      );
    });
  }
}
