import { SearchEntry, TOCItem } from '../types.js';

export class Indexer {
  extractTOC(html: string): TOCItem[] {
    const items: TOCItem[] = [];
    const re = /<h([23]) id="([^"]+)">(.+?)<a class="heading-anchor"/g;
    let m;
    while ((m = re.exec(html)) !== null) {
      items.push({
        level: +m[1],
        id: m[2],
        text: m[3].replace(/<[^>]*>/g, '').trim()
      });
    }
    return items;
  }

  buildPageIndex(slug: string, title: string, group: string, html: string, pathPrefix: string): SearchEntry[] {
    const url = `${pathPrefix}/${slug}/`;
    const entries: SearchEntry[] = [];
    const cleanText = this.stripHtml(html);

    entries.push({
      type: 'page',
      pageSlug: slug,
      pageTitle: title,
      group,
      url,
      id: null,
      title,
      excerpt: cleanText.slice(0, 180),
    });

    const re = /<h[23] id="([^"]+)">(.+?)<a class="heading-anchor"/g;
    let m;
    while ((m = re.exec(html)) !== null) {
      const id = m[1];
      const hText = m[2].replace(/<[^>]*>/g, '').trim();
      const after = html.slice(m.index + m[0].length, m.index + m[0].length + 800);
      const excerpt = this.stripHtml(after).slice(0, 150);

      entries.push({
        type: 'heading',
        pageSlug: slug,
        pageTitle: title,
        group,
        url,
        id,
        title: hText,
        excerpt
      });
    }
    return entries;
  }

  private stripHtml(html: string): string {
    return html.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim();
  }
}
