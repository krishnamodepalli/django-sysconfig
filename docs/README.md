# docsite

A minimal static documentation site generator for your Django project.

## Setup

```bash
npm install
```

## Usage

```bash
node build.js           # Build once
node build.js --watch   # Build and watch for changes (with hot reload)
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
    baseUrl: "",            // for canonical URLs, e.g. "https://docs.myapp.dev"
  },
  outDir:  "dist",          // output directory
  docsDir: "docs",          // markdown source directory
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
