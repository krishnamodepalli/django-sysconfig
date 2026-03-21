import fs from 'node:fs';
import path from 'node:path';
import CleanCSS from 'clean-css';
import { minify } from 'terser';

export class AssetManager {
  private root: string;
  private outDir: string;
  private cleanCSS: CleanCSS;

  constructor(root: string, outDir: string) {
    this.root = root;
    this.outDir = outDir;
    this.cleanCSS = new CleanCSS({
      level: 2,
      inline: false,
    });
  }

  async copyAssets(shouldMinify: boolean = false) {
    const src = path.resolve(this.root, 'assets');
    const dst = path.resolve(this.outDir, 'assets');

    if (!fs.existsSync(src)) return;

    await this.processRecursive(src, dst, shouldMinify);
  }

  private async processRecursive(src: string, dst: string, shouldMinify: boolean) {
    if (!fs.existsSync(dst)) {
      fs.mkdirSync(dst, { recursive: true });
    }

    const entries = fs.readdirSync(src);

    for (const entry of entries) {
      const srcPath = path.join(src, entry);
      const dstPath = path.join(dst, entry);

      if (fs.statSync(srcPath).isDirectory()) {
        await this.processRecursive(srcPath, dstPath, shouldMinify);
        continue;
      }

      const ext = path.extname(entry);

      if (ext === '.css') {
        this.copyCss(srcPath, dstPath, shouldMinify);
        continue;
      }

      if (ext === '.js' && shouldMinify) {
        const content = fs.readFileSync(srcPath, 'utf8');
        const minified = await minify(content, {
          module: true,
          mangle: true,
          compress: true,
        });
        fs.writeFileSync(dstPath, minified.code || content);
        continue;
      }

      fs.copyFileSync(srcPath, dstPath);
    }
  }

  private copyCss(srcPath: string, dstPath: string, shouldMinify: boolean) {
    const content = fs.readFileSync(srcPath, 'utf8');

    if (!shouldMinify) {
      fs.writeFileSync(dstPath, content);
      return;
    }

    const minified = new CleanCSS({
      level: 2,
      inline: ['local'],
      rebase: false,
    }).minify({
      [srcPath]: {
        styles: content,
      },
    });

    fs.writeFileSync(dstPath, minified.styles || content);
  }
}
