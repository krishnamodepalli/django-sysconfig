/**
 * Fuzzy Search Utilities
 */

export function lev(a, b) {
  if (a.length < b.length) { var tmp = a; a = b; b = tmp; }
  if (b.length === 0) return a.length;
  var prev = Array.from({ length: b.length + 1 }, function (_, i) { return i; });
  for (var i = 0; i < a.length; i++) {
    var curr = [i + 1];
    for (var j = 0; j < b.length; j++) {
      curr.push(Math.min(prev[j + 1] + 1, curr[j] + 1, prev[j] + (a[i] === b[j] ? 0 : 1)));
    }
    prev = curr;
  }
  return prev[b.length];
}

export function score(target, query) {
  if (!target || !query) return 0;
  var t = target.toLowerCase(), q = query.toLowerCase();
  if (t === q) return 10000;
  var idxMatch = t.indexOf(q);
  if (idxMatch !== -1) {
    var s = 5000;
    if (idxMatch === 0) s += 2000;
    else if (t[idxMatch - 1] === ' ' || t[idxMatch - 1] === '.') s += 1500;
    return s + (q.length * 20) - idxMatch;
  }
  var qTokens = q.split(/\s+/).filter(function (x) { return x.length > 1; });
  if (!qTokens.length) return 0;
  var tTokens = t.split(/[^a-z0-9]+/).filter(Boolean);
  if (q.length >= 2 && q.length <= 4) {
    var acronym = tTokens.map(function (tt) { return tt[0]; }).join('').slice(0, q.length);
    if (acronym === q) return 8000;
  }
  var total = 0, matches = 0;
  qTokens.forEach(function (qt) {
    var best = 0;
    tTokens.forEach(function (tt) {
      if (tt === qt) { best = Math.max(best, 1000); }
      else if (tt.indexOf(qt) === 0) { best = Math.max(best, 800); }
      else if (tt.indexOf(qt) !== -1) { best = Math.max(best, 400); }
      else if (qt.length > 2) {
        var d = lev(tt, qt);
        if (d === 1) best = Math.max(best, 300);
      }
    });
    if (best > 0) { total += best; matches++; }
  });
  if (matches === 0) return 0;
  return (total / qTokens.length) * (matches / qTokens.length);
}

export function hl(text, q) {
  if (!q) return text;
  var tokens = q.toLowerCase().split(/\s+/).filter(function (x) { return x.length > 1; });
  if (!tokens.length) return text;
  var out = text;
  tokens.forEach(function (t) {
    var safe = t.replace(/[-\[\]{}()*+?.,\\^$|#\s]/g, '\\$&');
    try { out = out.replace(new RegExp('(' + safe + ')', 'gi'), '<mark>$1</mark>'); } catch (e) { }
  });
  return out;
}
