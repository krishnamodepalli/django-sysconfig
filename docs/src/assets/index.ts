import fs from 'node:fs';
import path from 'node:path';

export class AssetManager {
  private root: string;
  private outDir: string;

  constructor(root: string, outDir: string) {
    this.root = root;
    this.outDir = outDir;
  }

  copyAssets() {
    const src = path.resolve(this.root, 'assets');
    const dst = path.resolve(this.outDir, 'assets');

    if (!fs.existsSync(src)) return;

    this.copyRecursive(src, dst);
  }

  private copyRecursive(src: string, dst: string) {
    if (!fs.existsSync(dst)) {
      fs.mkdirSync(dst, { recursive: true });
    }

    const entries = fs.readdirSync(src);

    for (const entry of entries) {
      const srcPath = path.join(src, entry);
      const dstPath = path.join(dst, entry);

      if (fs.statSync(srcPath).isDirectory()) {
        this.copyRecursive(srcPath, dstPath);
      } else {
        fs.writeFileSync(dstPath, fs.readFileSync(srcPath));
      }
    }
  }
}
