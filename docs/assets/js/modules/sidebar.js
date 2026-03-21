export function initSidebar() {
  document.querySelectorAll('.sg-hdr').forEach(function (h) {
    h.onclick = function () { h.closest('.sg').classList.toggle('closed'); };
  });

  var sb = document.getElementById('sidebar'),
    mob = document.getElementById('mob-overlay'),
    ham = document.getElementById('hamburger');

  function closeSb() { sb.classList.remove('open'); mob.classList.remove('open'); }
  if (ham) ham.onclick = function () { sb.classList.toggle('open'); mob.classList.toggle('open'); };
  if (mob) mob.onclick = closeSb;
}
