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
      inline: false
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
      } else {
        const ext = path.extname(entry);
        const content = fs.readFileSync(srcPath, 'utf8');

        if (shouldMinify) {
          if (ext === '.css') {
            const minified = this.cleanCSS.minify(content);
            fs.writeFileSync(dstPath, minified.styles);
          } else if (ext === '.js') {
            const minified = await minify(content, {
              mangle: true,
              compress: true
            });
            fs.writeFileSync(dstPath, minified.code || content);
          } else {
            // Non-CSS/JS assets (images, etc)
            fs.writeFileSync(dstPath, fs.readFileSync(srcPath));
          }
        } else {
          fs.writeFileSync(dstPath, fs.readFileSync(srcPath));
        }
      }
    }
  }
}
