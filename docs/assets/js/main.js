import { initSidebar } from './modules/sidebar.js';
import { initScrollSpy } from './modules/scrollspy.js';
import { initTables } from './modules/tables.js';
import { initCopyButtons } from './modules/copy-btn.js';
import { initSearch } from './modules/search.js';
import { initRouter } from './core/router.js';

(function () {
  'use strict';

  const { isWatch, pathPrefix } = window.DOCS_CONFIG || { isWatch: false, pathPrefix: '' };

  let searchController;

  function reinit() {
    initTables();
    initScrollSpy(searchController ? searchController.closeSearch : null);
  }

  function bootstrap() {
    initSidebar();
    initCopyButtons();
    searchController = initSearch(pathPrefix);
    initRouter(reinit);

    // Initial call
    reinit();

    // Hot reload
    if (isWatch) {
      (function () {
        var ws = new WebSocket('ws://' + window.location.hostname + ':35729');
        ws.onmessage = function (msg) { if (msg.data === 'reload') window.location.reload(); };
      })();
    }
  }

  // Ensure DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bootstrap);
  } else {
    bootstrap();
  }
})();
