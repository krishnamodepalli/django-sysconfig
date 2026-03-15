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
import { DocsConfig, PageMetadata, SearchEntry } from './types.js';

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

    // Initialize directories
    if (!fs.existsSync(outDir)) {
      fs.mkdirSync(outDir, { recursive: true });
    }

    // Prepare pages
    this.allPages = this.config.nav.flatMap(g =>
      g.pages.map(p => ({ ...p, group: g.label }))
    );

    // Copy and minify assets
    const assetManager = new AssetManager(this.root, outDir);
    await assetManager.copyAssets(shouldMinify);

    const searchIndex: SearchEntry[] = [];

    for (const page of this.allPages) {
      const srcPath = path.join(docsDir, `${page.slug}.md`);
      const rawMd = fs.existsSync(srcPath)
        ? fs.readFileSync(srcPath, 'utf8')
        : `# ${page.title}\n\n> 📝 This page hasn't been written yet.\n`;

      const { data: fm, content: mdContent } = matter(rawMd);
      const title = fm.title || page.title;
      const description = fm.description || '';

      const bodyHtml = this.renderer.render(mdContent, pathPrefix);
      const tocItems = this.indexer.extractTOC(bodyHtml);

      const tocHtml = tocItems.length >= 2
        ? `<div class="toc-lbl">On this page</div>\n<ul class="toc-list">\n`
          + tocItems.map(h =>
              `<li class="toc-item${h.level===3?' h3':''}" data-id="${h.id}"><a href="#${h.id}">${h.text}</a></li>`
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
    }

    // Write search index
    fs.writeFileSync(path.join(outDir, 'search-index.json'), JSON.stringify(searchIndex));

    // Write root redirect
    const first = this.allPages[0];
    if (first) {
      const rootHref = `${pathPrefix}/${first.slug}/`;
      let redirectHtml = `<!DOCTYPE html><html><head><meta charset="UTF-8">` +
        `<meta http-equiv="refresh" content="0;url=${rootHref}">` +
        `<link rel="canonical" href="${rootHref}"></head>` +
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
}
