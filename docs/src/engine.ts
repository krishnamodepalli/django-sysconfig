import fs from 'node:fs';
import path from 'node:path';
import matter from 'gray-matter';
import chokidar from 'chokidar';
import { WebSocketServer, WebSocket } from 'ws';
import { minify as minifyHtml } from 'html-minifier-terser';

import { ConfigLoader } from './config.js';
import { MarkdownRenderer } from './renderer/markdown.js';
import { renderPage } from './renderer/template.js';
import { Indexer } from './indexer/index.js';
import { AssetManager } from './assets/index.js';
import { DocsConfig, GeneratedPage, PageMetadata, SearchEntry } from './types.js';
import {
  buildCanonicalBaseUrl,
  toAbsoluteDocHref,
  toAbsoluteSitePath,
  toAbsoluteUrl,
  toRelativeDocHref,
} from './paths.js';

export class DocsiteEngine {
  private root: string;
  private configLoader: ConfigLoader;
  private renderer: MarkdownRenderer;
  private indexer: Indexer;
  private config!: DocsConfig;
  private allPages: PageMetadata[] = [];
  private isWatch: boolean = false;
  private wss?: WebSocketServer;
  private clients = new Set<WebSocket>();

  constructor(root: string) {
    this.root = root;
    this.configLoader = new ConfigLoader(root);
    this.renderer = new MarkdownRenderer();
    this.indexer = new Indexer();
  }

  async build(isWatch = false) {
    this.isWatch = isWatch;
    const shouldMinify = !isWatch;
    const t0 = Date.now();
    console.log(`\n📖  Building docs${shouldMinify ? ' (minified)' : ''}...`);

    this.config = await this.configLoader.load();
    const { docsDir, outDir } = this.configLoader.getAbsolutePaths(this.config);
    const pathPrefix = this.config.pathPrefix || '';
    const canonicalBaseUrl = buildCanonicalBaseUrl(this.config.site.baseUrl || '', pathPrefix);

    if (!fs.existsSync(outDir)) {
      fs.mkdirSync(outDir, { recursive: true });
    }

    this.allPages = this.config.nav.flatMap(g =>
      g.pages.map(p => ({ ...p, group: g.label }))
    );

    const assetManager = new AssetManager(this.root, outDir);
    await assetManager.copyAssets(shouldMinify);

    const searchIndex: SearchEntry[] = [];
    const generatedPages: GeneratedPage[] = [];

    for (const page of this.allPages) {
      const srcPath = path.join(docsDir, `${page.slug}.md`);
      const rawMd = fs.existsSync(srcPath)
        ? fs.readFileSync(srcPath, 'utf8')
        : `# ${page.title}\n\n> 📝 This page hasn't been written yet.\n`;

      const { data: fm, content: mdContent } = matter(rawMd);
      const title = fm.title || page.title;
      const description =
        this.extractDescription(mdContent) ||
        fm.description ||
        this.config.site.tagline ||
        `${title} — ${this.config.site.name} documentation`;

      const bodyHtml = this.renderer.render(mdContent, page.slug, pathPrefix);
      const tocItems = this.indexer.extractTOC(bodyHtml);

      const tocHtml = tocItems.length >= 2
        ? `<div class="toc-lbl">On this page</div>\n<ul class="toc-list">\n`
          + tocItems.map(h =>
              `<li class="toc-item${h.level===3?' h3':''}" data-id="${h.id}" title="${h.text}"><a href="#${h.id}">${h.text}</a></li>`
            ).join('\n')
          + `\n</ul>`
        : '';

      let html = renderPage({
        slug: page.slug,
        title,
        description,
        bodyHtml,
        tocHtml,
        cfg: this.config,
        allPages: this.allPages,
        isWatch: this.isWatch
      });

      if (shouldMinify) {
        html = await minifyHtml(html, {
          collapseWhitespace: true,
          removeComments: true,
          minifyCSS: true,
          minifyJS: true
        });
      }

      const pageOutDir = path.join(outDir, page.slug);
      if (!fs.existsSync(pageOutDir)) {
        fs.mkdirSync(pageOutDir, { recursive: true });
      }
      fs.writeFileSync(path.join(pageOutDir, 'index.html'), html);

      searchIndex.push(...this.indexer.buildPageIndex(page.slug, title, page.group, bodyHtml, pathPrefix));
      generatedPages.push({
        slug: page.slug,
        title,
        description,
        url: this.buildPageUrl(page.slug, canonicalBaseUrl, pathPrefix),
      });
    }

    fs.writeFileSync(path.join(outDir, 'search-index.json'), JSON.stringify(searchIndex));
    this.writeSitemap(outDir, generatedPages, canonicalBaseUrl);
    this.writeStructuredData(outDir, generatedPages, canonicalBaseUrl, pathPrefix);

    const first = this.allPages[0];
    if (first) {
      const rootHref = toRelativeDocHref('', first.slug);
      const canonicalHref = canonicalBaseUrl
        ? this.buildPageUrl(first.slug, canonicalBaseUrl, pathPrefix)
        : rootHref;
      let redirectHtml = `<!DOCTYPE html><html><head><meta charset="UTF-8">` +
        `<meta http-equiv="refresh" content="0;url=${rootHref}">` +
        `<link rel="canonical" href="${canonicalHref}"></head>` +
        `<body><a href="${rootHref}">Redirecting...</a></body></html>`;

      if (shouldMinify) {
        redirectHtml = await minifyHtml(redirectHtml, { collapseWhitespace: true });
      }
      fs.writeFileSync(path.join(outDir, 'index.html'), redirectHtml);
    }

    console.log(`✅  Done in ${Date.now() - t0}ms`);
  }

  async watch() {
    await this.build(true);

    this.wss = new WebSocketServer({ port: 35729 });
    this.wss.on('connection', ws => {
      this.clients.add(ws);
      ws.on('close', () => this.clients.delete(ws));
    });

    const { docsDir } = this.configLoader.getAbsolutePaths(this.config);
    const configPath = path.resolve(this.root, 'docs.config.js');

    const watcher = chokidar.watch([docsDir, configPath], { ignoreInitial: true });

    watcher.on('all', async (event, filePath) => {
      console.log(`\n🔄  Change detected: ${path.relative(this.root, filePath)}`);
      try {
        await this.build(true);
        this.broadcastReload();
      } catch (err: any) {
        console.error(`\n❌  Build failed: ${err.message}`);
      }
    });

    console.log('👀  Watching for changes...');
  }

  private broadcastReload() {
    for (const client of this.clients) {
      if (client.readyState === WebSocket.OPEN) {
        client.send('reload');
      }
    }
  }

  private extractDescription(markdown: string): string {
    const withoutCode = markdown.replace(/```[\s\S]*?```/g, '');
    const withoutCallouts = withoutCode.replace(/^:::\w+[^\n]*\n[\s\S]*?^:::/gm, '');
    const blocks = withoutCallouts.split(/\n\s*\n/).map(block => block.trim()).filter(Boolean);

    for (const block of blocks) {
      if (/^(#|>|[-*]\s|\d+\.\s|\|)/m.test(block)) {
        continue;
      }

      const text = block
        .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
        .replace(/`([^`]+)`/g, '$1')
        .replace(/[*_~]/g, '')
        .replace(/<[^>]+>/g, '')
        .replace(/\s+/g, ' ')
        .trim();

      if (text) {
        return text.slice(0, 160);
      }
    }

    return '';
  }

  private buildPageUrl(slug: string, canonicalBaseUrl: string, pathPrefix: string): string {
    const pagePath = toAbsoluteDocHref(pathPrefix, slug);
    return canonicalBaseUrl ? toAbsoluteUrl(canonicalBaseUrl, pagePath) : pagePath;
  }

  private writeSitemap(outDir: string, pages: GeneratedPage[], canonicalBaseUrl: string) {
    if (!canonicalBaseUrl) {
      return;
    }

    const urls = pages
      .map(page => `<url><loc>${page.url}</loc></url>`)
      .join('');
    const sitemap = `<?xml version="1.0" encoding="UTF-8"?>` +
      `<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">${urls}</urlset>`;
    fs.writeFileSync(path.join(outDir, 'sitemap.xml'), sitemap);
  }

  private writeStructuredData(
    outDir: string,
    pages: GeneratedPage[],
    canonicalBaseUrl: string,
    pathPrefix: string
  ) {
    const siteUrl = canonicalBaseUrl || toAbsoluteSitePath(pathPrefix);
    const ogImagePath = this.config.site.ogImage || toAbsoluteSitePath(pathPrefix, 'assets/images/og-banner.svg');
    const ogImageUrl = canonicalBaseUrl ? toAbsoluteUrl(canonicalBaseUrl, ogImagePath) : ogImagePath;
    const payload = {
      '@context': 'https://schema.org',
      '@graph': [
        {
          '@type': 'WebSite',
          name: this.config.site.name,
          description: this.config.site.tagline,
          url: siteUrl,
          image: ogImageUrl,
        },
        ...pages.map(page => ({
          '@type': 'TechArticle',
          headline: page.title,
          description: page.description,
          url: page.url,
          image: ogImageUrl,
        })),
      ],
    };

    fs.writeFileSync(
      path.join(outDir, 'structured-data.jsonld'),
      JSON.stringify(payload, null, 2)
    );
  }
}
