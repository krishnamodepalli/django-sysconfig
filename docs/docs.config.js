const fs = require('fs');
const path = require('path');

// Extract version from pyproject.toml
let version = '0.0.1';
try {
  const pyproject = fs.readFileSync(path.resolve(__dirname, '../pyproject.toml'), 'utf8');
  const match = pyproject.match(/version\s*=\s*"([^"]+)"/);
  if (match) version = `v${match[1]}`;
} catch (e) {
  console.warn('Could not read version from pyproject.toml, falling back to default.');
}

/** @type {DocsConfig} */
module.exports = {
  site: {
    name: "django-sysconfig",
    tagline: "Magento-style system configuration for Django",
    version: version,
    repo: "https://github.com/krishnamodepalli/django-sysconfig",
    // Base URL for production (used in sitemap, canonical links)
    // e.g. "https://docs.sysconfig.dev" — no trailing slash
    baseUrl: "",
  },

  // Output directory (relative to this config file)
  outDir: "dist",

  // Docs source directory
  docsDir: "docs",

  nav: [
    {
      label: "Getting Started",
      pages: [
        { slug: "introduction",  title: "Introduction"  },
        { slug: "installation",  title: "Installation"  },
        { slug: "configuration", title: "Configuration" },
      ],
    },
  ],
};
