import path from 'node:path';
import fs from 'node:fs';
import { DocsConfig } from './types.js';

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

    // Use dynamic import for the JS config file
    // We append a cache-buster if we were in a watch mode context,
    // but for the engine we'll handle re-loading at a higher level if needed.
    const module = await import(`file://${configPath}?t=${Date.now()}`);
    const cfg: DocsConfig = module.default;

    return {
      ...cfg,
      outDir: cfg.outDir || 'dist',
      docsDir: cfg.docsDir || 'docs',
      pathPrefix: process.env.PATH_PREFIX || cfg.pathPrefix || '',
    };
  }

  getAbsolutePaths(cfg: DocsConfig) {
    return {
      docsDir: path.resolve(this.root, cfg.docsDir!),
      outDir: path.resolve(this.root, cfg.outDir!),
    };
  }
}
