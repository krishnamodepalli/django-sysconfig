export interface SiteConfig {
  name: string;
  tagline: string;
  version: string;
  repo?: string;
  baseUrl?: string;
}

export interface NavPage {
  slug: string;
  title: string;
}

export interface NavGroup {
  label: string;
  pages: NavPage[];
}

export interface DocsConfig {
  site: SiteConfig;
  outDir?: string;
  docsDir?: string;
  pathPrefix?: string;
  nav: NavGroup[];
}

export interface PageMetadata {
  slug: string;
  title: string;
  description?: string;
  group: string;
}

export interface TOCItem {
  level: number;
  id: string;
  text: string;
}

export interface SearchEntry {
  type: 'page' | 'heading';
  pageSlug: string;
  pageTitle: string;
  group: string;
  url: string;
  id: string | null;
  title: string;
  excerpt: string;
}
