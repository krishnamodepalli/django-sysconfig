import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Extract version from pyproject.toml
let version = '0.0.1';
try {
  const pyproject = fs.readFileSync(path.resolve(__dirname, '../pyproject.toml'), 'utf8');
  const match = pyproject.match(/version\s*=\s*"([^"]+)"/);
  if (match) version = `v${match[1]}`;
} catch (e) {
  console.warn('Could not read version from pyproject.toml, falling back to default.');
}

/** @type {import('./src/types.js').DocsConfig} */
export default {
  site: {
    name: "django-sysconfig",
    tagline: "Magento-style system configuration for Django",
    version: version,
    repo: "https://github.com/krishnamodepalli/django-sysconfig",
    // Base URL for production (used in sitemap, canonical links)
    // e.g. "https://docs.sysconfig.dev" — no trailing slash
    baseUrl: "https://krishnamodepalli.github.io/django-sysconfig",
    ogImage: "/django-sysconfig/assets/images/og-banner.svg",
  },

  // Output directory (relative to this config file)
  outDir: "dist",

  // Docs source directory
  docsDir: "docs",

  // Optional repository subpath for GitHub Pages deployments.
  // Example: "/django-sysconfig" for https://<user>.github.io/django-sysconfig/
  // You can also set PATH_PREFIX in CI instead of hard-coding this here.
  pathPrefix: "",

  nav: [
    {
      label: "Getting Started",
      pages: [
        { slug: "quick-start",  title: "Quick Start"  },
        { slug: "introduction",  title: "Introduction"  },
        { slug: "installation",  title: "Installation"  },
        { slug: "configuration", title: "Configuration" },
      ],
    },
  ],
};
