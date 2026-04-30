import { defineConfig } from "vitepress";

export default defineConfig({
  lang: "en-US",
  title: "django-sysconfig",
  description:
    "Schema-driven, database-backed runtime configuration for Django. Define typed fields in code, store values in the database, manage through a clean admin UI.",

  srcDir: "./docs",
  cleanUrls: true,
  lastUpdated: true,

  // ── Sitemap ────────────────────────────────────────────────────────────────
  sitemap: {
    hostname: "https://krishnamodepalli.github.io/django-sysconfig",
  },

  // ── Global <head> tags ─────────────────────────────────────────────────────
  head: [
    // Open Graph
    ["meta", { property: "og:type", content: "website" }],
    ["meta", { property: "og:site_name", content: "django-sysconfig" }],
    [
      "meta",
      {
        property: "og:image",
        content:
          "https://krishnamodepalli.github.io/django-sysconfig/og-image.png",
      },
    ],
    // Twitter / X card
    ["meta", { name: "twitter:card", content: "summary_large_image" }],
    [
      "meta",
      {
        name: "twitter:image",
        content:
          "https://krishnamodepalli.github.io/django-sysconfig/og-image.png",
      },
    ],
    // Misc
    ["meta", { name: "theme-color", content: "#646cff" }],
    ["link", { rel: "icon", type: "image/svg+xml", href: "/favicon.svg" }],
  ],

  // ── Per-page <head> injection (dynamic SEO) ────────────────────────────────
  transformHead({ pageData, siteData }) {
    const head: [string, Record<string, string>][] = [];

    const pageTitle = pageData.frontmatter.title
      ? `${pageData.frontmatter.title} | django-sysconfig`
      : siteData.title;

    const pageDescription =
      pageData.frontmatter.description || siteData.description;

    // OG per page
    head.push(["meta", { property: "og:title", content: pageTitle }]);
    head.push([
      "meta",
      { property: "og:description", content: pageDescription },
    ]);

    // Twitter per page
    head.push(["meta", { name: "twitter:title", content: pageTitle }]);
    head.push([
      "meta",
      { name: "twitter:description", content: pageDescription },
    ]);

    // Description meta
    head.push(["meta", { name: "description", content: pageDescription }]);

    // JSON-LD structured data
    const jsonLd = {
      "@context": "https://schema.org",
      "@type": "SoftwareApplication",
      name: "django-sysconfig",
      applicationCategory: "DeveloperApplication",
      operatingSystem: "Any",
      description: siteData.description,
      url: "https://krishnamodepalli.github.io/django-sysconfig",
      downloadUrl: "https://pypi.org/project/django-sysconfig/",
      author: {
        "@type": "Person",
        name: "Krishna Modepalli",
        url: "https://github.com/krishnamodepalli",
      },
      license: "https://opensource.org/licenses/MIT",
      programmingLanguage: "Python",
    };
    head.push([
      "script",
      { type: "application/ld+json" },
      JSON.stringify(jsonLd) as unknown as string,
    ]);

    return head;
  },

  // ── Theme config ───────────────────────────────────────────────────────────
  themeConfig: {
    siteTitle: "django-sysconfig",

    nav: [
      { text: "Introduction", link: "/introduction" },
      {
        text: "Guides",
        items: [
          { text: "Defining Configuration", link: "/guides/defining-config" },
          { text: "Reading & Writing", link: "/guides/reading-writing" },
          { text: "Admin UI", link: "/guides/admin-ui" },
          { text: "Encryption", link: "/guides/encryption" },
          { text: "Caching", link: "/guides/caching" },
          { text: "on_save Callbacks", link: "/guides/on-save-callbacks" },
        ],
      },
      // { text: "Changelog", link: "/changelog" },
    ],

    sidebar: [
      {
        text: "Getting Started",
        items: [
          { text: "Introduction", link: "/introduction" },
          { text: "Installation", link: "/installation" },
          { text: "Quick Start", link: "/quickstart" },
          { text: "Getting Started", link: "/getting-started" },
          { text: "How It Works", link: "/how-it-works" },
        ],
      },
      {
        text: "Guides",
        collapsed: false,
        items: [
          { text: "Defining Configuration", link: "/guides/defining-config" },
          { text: "Reading & Writing Values", link: "/guides/reading-writing" },
          { text: "Admin UI", link: "/guides/admin-ui" },
          { text: "Encryption", link: "/guides/encryption" },
          { text: "Caching", link: "/guides/caching" },
          { text: "on_save Callbacks", link: "/guides/on-save-callbacks" },
        ],
      },
      {
        text: "CLI",
        items: [
          { text: "Management Command", link: "/cli/management-command" },
        ],
      },
      {
        text: "Reference",
        collapsed: true,
        items: [
          { text: "Field Types", link: "/reference/field-types" },
          { text: "Validators", link: "/reference/validators" },
          { text: "Accessor API", link: "/reference/accessor-api" },
          { text: "Exceptions", link: "/reference/exceptions" },
          { text: "Registry API", link: "/reference/registry-api" },
        ],
      },
      {
        text: "Extending",
        collapsed: true,
        items: [
          {
            text: "Custom Field Types",
            link: "/extending/custom-field-types",
          },
          {
            text: "Custom Validators",
            link: "/extending/custom-validators",
          },
        ],
      },
      {
        text: "Community",
        items: [
          { text: "Why django-sysconfig", link: "/comparison" },
          { text: "Contributing", link: "/contributing" },
          { text: "FAQ", link: "/faq" },
          // { text: "Changelog", link: "/changelog" },
        ],
      },
    ],

    socialLinks: [
      {
        icon: "github",
        link: "https://github.com/krishnamodepalli/django-sysconfig",
      },
      {
        icon: {
          svg: '<svg role="img" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><title>PyPI</title><path d="M14.25.18l.9.2.73.26.59.3.45.32.34.34.25.34.16.33.1.3.04.26.02.2-.01.13V8.5l-.05.63-.13.55-.21.46-.26.38-.3.31-.33.25-.35.19-.35.14-.33.1-.3.07-.26.04-.21.02H8.77l-.69.05-.59.14-.5.22-.41.27-.33.32-.27.35-.2.36-.15.37-.1.35-.07.32-.04.27-.02.21v3.06H3.17l-.21-.03-.28-.07-.32-.12-.35-.18-.36-.26-.36-.36-.35-.46-.32-.59-.28-.73-.21-.88-.14-1.05-.05-1.23.06-1.22.16-1.04.24-.87.32-.71.36-.57.4-.44.42-.33.42-.24.4-.16.36-.1.32-.05.24-.01h.16l.06.01h8.16v-.83H6.18l-.01-2.75-.02-.37.05-.34.11-.31.17-.28.25-.26.31-.23.38-.2.44-.18.51-.15.58-.12.64-.1.71-.06.77-.04.84-.02 1.27.05zm-6.3 1.98l-.23.33-.08.41.08.41.23.34.33.22.41.09.41-.09.33-.22.23-.34.08-.41-.08-.41-.23-.33-.33-.22-.41-.09-.41.09zm13.09 3.95l.28.06.32.12.35.18.36.27.36.35.35.47.32.59.28.73.21.88.14 1.04.05 1.23-.06 1.23-.16 1.04-.24.86-.32.71-.36.57-.4.45-.42.33-.42.24-.4.16-.36.09-.32.05-.24.02-.16-.01h-8.22v.82h5.84l.01 2.76.02.36-.05.34-.11.31-.17.29-.25.25-.31.24-.38.2-.44.17-.51.15-.58.13-.64.09-.71.07-.77.04-.84.01-1.27-.04-1.07-.14-.9-.2-.73-.25-.59-.3-.45-.33-.34-.34-.25-.34-.16-.33-.1-.3-.04-.25-.02-.2.01-.13v-5.34l.05-.64.13-.54.21-.46.26-.38.3-.32.33-.24.35-.2.35-.14.33-.1.3-.06.26-.04.21-.02.13-.01h5.84l.69-.05.59-.14.5-.21.41-.28.33-.32.27-.35.2-.36.15-.36.1-.35.07-.32.04-.28.02-.21V6.07h2.09l.14.01zm-6.47 14.25l-.23.33-.08.41.08.41.23.33.33.23.41.08.41-.08.33-.23.23-.33.08-.41-.08-.41-.23-.33-.33-.23-.41-.08-.41.08z"/></svg>',
        },
        link: "https://pypi.org/project/django-sysconfig/",
        ariaLabel: "View on PyPI",
      },
    ],

    search: {
      provider: "local",
    },

    editLink: {
      pattern:
        "https://github.com/krishnamodepalli/django-sysconfig/edit/develop/docs/docs/:path",
      text: "Edit this page on GitHub",
    },

    lastUpdated: {
      text: "Last updated",
      formatOptions: {
        dateStyle: "medium",
      },
    },

    outline: {
      level: [2, 3],
      label: "On this page",
    },

    footer: {
      message: "Released under the MIT License.",
      copyright: "Copyright © 2024 Krishna Modepalli",
    },

    docFooter: {
      prev: "Previous",
      next: "Next",
    },
  },

  // ── Markdown ───────────────────────────────────────────────────────────────
  markdown: {
    theme: {
      light: "github-light",
      dark: "github-dark",
    },
    lineNumbers: false,
  },
});
