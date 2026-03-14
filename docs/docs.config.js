/** @type {DocsConfig} */
module.exports = {
  site: {
    name: "django-sysconfig",
    tagline: "Magento-style system configuration for Django",
    version: "v0.0.1",
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
