# docsite

A minimal static documentation site generator for your Django project.

## Setup

```bash
npm install
```

## Usage

```bash
npm run build           # Build once
npm run dev             # Build and watch for changes (with hot reload)
```

Reads `docs/*.md` + `docs.config.js` → writes to `dist/`.

## Output URLs

```
dist/introduction/index.html
dist/installation/index.html
dist/search-index.json   ← fuzzy search index (auto-generated)
dist/index.html          ← redirects to first page
```

Serve `dist/` from any static host (Netlify, GitHub Pages, S3, Nginx).

## Writing docs

Each `.md` file in `docs/` maps to one slug defined in `docs.config.js`.

### Frontmatter

```yaml
---
title: My Page Title
description: Used for <meta description> and OG tags.
---
```

### Callout blocks

```
:::note
Informational callout.
:::

:::tip
A helpful tip.
:::

:::warning
Something to be careful about.
:::

:::danger
A critical warning.
:::
```

### Inline tooltips

```html
<abbr title="Object-Relational Mapper">ORM</abbr>
```

### Everything else

Standard GitHub Flavored Markdown: tables, task lists `- [x]`,
fenced code blocks with syntax highlighting, blockquotes, strikethrough, etc.

## Search

`Ctrl+K` opens a fuzzy search modal. The search index is built at compile time
from page titles, headings, and content excerpts — no server required.

## Config reference (`docs.config.js`)

```js
module.exports = {
  site: {
    name: "MyApp",          // logo text
    version: "v2.4.0",      // shown in header
    repo: "https://...",    // GitHub icon link (optional)
    baseUrl: "",            // full published docs URL, e.g. "https://user.github.io/repo"
  },
  outDir:  "dist",          // output directory
  docsDir: "docs",          // markdown source directory
  pathPrefix: "/repo",      // optional repo subpath for GitHub Pages
  nav: [
    {
      label: "Getting Started",
      pages: [
        { slug: "introduction", title: "Introduction" },
        // slug → docs/introduction.md → dist/introduction.html
      ],
    },
  ],
};
```

### GitHub Pages

If you publish to `https://<username>.github.io/<repo>/`, set either:

- `pathPrefix: "/<repo>"` in `docs.config.js`, or
- `PATH_PREFIX="/<repo>"` in your build environment

Also set `site.baseUrl` to the full published URL if you want canonical tags:

```js
site: {
  baseUrl: "https://<username>.github.io/<repo>",
},
pathPrefix: "/<repo>",
```

The generator will then keep page links and assets relative, while search and canonical URLs use the correct prefixed path.
