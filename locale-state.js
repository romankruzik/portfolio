(function () {
  var STORAGE_KEY = 'kruzik-locale-state';

  function captureState() {
    var openTiles = [];
    document.querySelectorAll('.cs-tile.is-open').forEach(function (tile) {
      if (tile.id) openTiles.push(tile.id);
    });

    var openExpIndex = null;
    document.querySelectorAll('.exp-item--expandable').forEach(function (item, index) {
      if (item.classList.contains('is-open')) openExpIndex = index;
    });

    return {
      scrollY: window.scrollY,
      openTiles: openTiles,
      openExpIndex: openExpIndex
    };
  }

  function restoreState(state) {
    state.openTiles.forEach(function (id) {
      var tile = document.getElementById(id);
      if (!tile) return;
      tile.classList.add('is-open');
      var toggle = tile.querySelector('.cs-tile-head');
      if (toggle) toggle.setAttribute('aria-expanded', 'true');
    });

    if (state.openExpIndex !== null) {
      var expItems = document.querySelectorAll('.exp-item--expandable');
      var item = expItems[state.openExpIndex];
      if (item) {
        item.classList.add('is-open');
        item.setAttribute('aria-expanded', 'true');
      }
    }
  }

  function restoreScroll(y) {
    function apply() {
      window.scrollTo(0, y);
    }
    apply();
    requestAnimationFrame(function () {
      apply();
      requestAnimationFrame(apply);
    });
  }

  function bindLangSwitchers() {
    document.querySelectorAll('.lang-switch__link:not(.is-active)').forEach(function (link) {
      link.addEventListener('click', function () {
        try {
          sessionStorage.setItem(STORAGE_KEY, JSON.stringify(captureState()));
        } catch (e) {}
      });
    });
  }

  try {
    var raw = sessionStorage.getItem(STORAGE_KEY);
    if (raw) {
      sessionStorage.removeItem(STORAGE_KEY);
      var state = JSON.parse(raw);
      document.addEventListener('DOMContentLoaded', function () {
        restoreState(state);
        restoreScroll(state.scrollY);
      });
    }
  } catch (e) {}

  document.addEventListener('DOMContentLoaded', bindLangSwitchers);
})();
