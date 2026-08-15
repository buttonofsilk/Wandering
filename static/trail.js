document.addEventListener('DOMContentLoaded', function () {
  var toggle = document.querySelector('.trail-toggle');
  var panel = document.getElementById('trail-panel');

  if (!toggle || !panel) return;

  toggle.addEventListener('click', function (e) {
    e.stopPropagation();
    panel.classList.toggle('open');
  });

  document.addEventListener('click', function (e) {
    if (!panel.contains(e.target) && !toggle.contains(e.target)) {
      panel.classList.remove('open');
    }
  });
});
