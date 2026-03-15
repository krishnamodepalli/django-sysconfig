export function initTables() {
  document.querySelectorAll('.md table').forEach(function (t) {
    if (t.parentNode.className === 'table-wrap') return;
    var w = document.createElement('div'); w.className = 'table-wrap';
    t.parentNode.insertBefore(w, t); w.appendChild(t);
  });
}
