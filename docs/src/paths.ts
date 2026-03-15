export function trimTrailingSlash(value: string = ''): string {
  return value.replace(/\/+$/, '');
}

export function normalizePathPrefix(value: string = ''): string {
  const trimmed = value.trim();

  if (!trimmed || trimmed === '/') {
    return '';
  }

  return `/${trimmed.replace(/^\/+|\/+$/g, '')}`;
}

export function getRelativeRootPrefix(slug: string): string {
  const depth = slug.split('/').filter(Boolean).length;
  return depth === 0 ? '.' : '../'.repeat(depth).slice(0, -1);
}

export function toRelativeDocHref(currentSlug: string, targetSlug: string): string {
  return `${getRelativeRootPrefix(currentSlug)}/${targetSlug}/`.replace(/\/+/g, '/');
}

export function toAbsoluteSitePath(pathPrefix: string, targetPath: string = ''): string {
  const normalizedPrefix = normalizePathPrefix(pathPrefix);
  const normalizedTarget = targetPath.replace(/^\/+/, '');

  if (!normalizedTarget) {
    return normalizedPrefix || '/';
  }

  return `${normalizedPrefix}/${normalizedTarget}`.replace(/\/+/g, '/');
}

export function toAbsoluteDocHref(pathPrefix: string, slug: string): string {
  return toAbsoluteSitePath(pathPrefix, `${slug}/`);
}

export function toAbsoluteUrl(baseUrl: string, sitePath: string): string {
  try {
    const origin = new URL(baseUrl).origin;
    return new URL(sitePath, origin).toString();
  } catch {
    return sitePath;
  }
}

export function buildCanonicalBaseUrl(baseUrl: string, pathPrefix: string): string {
  const trimmedBaseUrl = trimTrailingSlash(baseUrl);

  if (!trimmedBaseUrl) {
    return '';
  }

  try {
    const url = new URL(trimmedBaseUrl);
    const normalizedPrefix = normalizePathPrefix(pathPrefix);

    if (normalizedPrefix && (!url.pathname || url.pathname === '/')) {
      url.pathname = normalizedPrefix;
    }

    return trimTrailingSlash(url.toString());
  } catch {
    return trimmedBaseUrl;
  }
}

export function rewriteRootRelativeUrls(html: string, pathPrefix: string): string {
  return html.replace(
    /\b(href|src)=(["'])\/(?!\/)([^"']*)\2/g,
    (_, attr: string, quote: string, target: string) =>
      `${attr}=${quote}${toAbsoluteSitePath(pathPrefix, target)}${quote}`
  );
}
