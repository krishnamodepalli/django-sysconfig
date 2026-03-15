import path from 'node:path';
import fs from 'node:fs';
import { DocsConfig } from './types.js';
import { normalizePathPrefix, trimTrailingSlash } from './paths.js';

export class ConfigLoader {
  private root: string;

  constructor(root: string) {
    this.root = root;
  }

  async load(): Promise<DocsConfig> {
    const configPath = path.resolve(this.root, 'docs.config.js');

    if (!fs.existsSync(configPath)) {
      throw new Error(`Config file not found at ${configPath}`);
    }

    const module = await import(`file://${configPath}?t=${Date.now()}`);
    const cfg: DocsConfig = module.default;
    const baseUrl = trimTrailingSlash(cfg.site.baseUrl ?? '');
    const pathPrefix = normalizePathPrefix(
      process.env.PATH_PREFIX ?? cfg.pathPrefix ?? this.inferPathPrefix(baseUrl)
    );

    return {
      ...cfg,
      site: {
        ...cfg.site,
        baseUrl,
      },
      outDir: cfg.outDir ?? 'dist',
      docsDir: cfg.docsDir ?? 'docs',
      pathPrefix,
    };
  }

  private inferPathPrefix(baseUrl: string): string {
    if (!baseUrl) {
      return '';
    }

    try {
      return normalizePathPrefix(new URL(baseUrl).pathname);
    } catch {
      return '';
    }
  }

  getAbsolutePaths(cfg: DocsConfig) {
    return {
      docsDir: path.resolve(this.root, cfg.docsDir!),
      outDir: path.resolve(this.root, cfg.outDir!),
    };
  }
}
