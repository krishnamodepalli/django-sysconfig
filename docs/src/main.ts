import { DocsiteEngine } from './engine.js';

const root = process.cwd();
const engine = new DocsiteEngine(root);

const args = process.argv.slice(2);
const isWatch = args.includes('--watch');

if (isWatch) {
  engine.watch().catch(err => {
    console.error(`\n❌ Fatal error: ${err.message}`);
    process.exit(1);
  });
} else {
  engine.build().catch(err => {
    console.error(`\n❌ Fatal error: ${err.message}`);
    process.exit(1);
  });
}
