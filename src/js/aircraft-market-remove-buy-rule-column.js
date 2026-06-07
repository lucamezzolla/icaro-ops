(() => {
  document.addEventListener("DOMContentLoaded", () => {
    removeBuyRuleColumnsFromAircraftMarketOnly();
    installBuyRuleColumnObserver();
  });

  function installBuyRuleColumnObserver() {
    const catalogContainer = document.querySelector("#aircraftCatalogList");

    if (!catalogContainer) {
      return;
    }

    const observer = new MutationObserver(() => {
      removeBuyRuleColumnsFromAircraftMarketOnly();
    });

    observer.observe(catalogContainer, {
      childList: true,
      subtree: true
    });
  }

  function removeBuyRuleColumnsFromAircraftMarketOnly() {
    const dialog = document.querySelector("#buyAircraftDialog");

    if (!dialog) {
      return;
    }

    dialog.querySelectorAll("table").forEach(table => {
      const index = findBuyRuleColumnIndex(table);

      if (index < 0) {
        return;
      }

      table.querySelectorAll("tr").forEach(row => {
        const cells = Array.from(row.children);

        if (cells[index]) {
          cells[index].remove();
        }
      });
    });
  }

  function findBuyRuleColumnIndex(table) {
    const headers = Array.from(table.querySelectorAll("thead th"));
    const headerIndex = headers.findIndex(header => normalize(header.textContent) === "BUY RULE");

    if (headerIndex >= 0) {
      return headerIndex;
    }

    const bodyRows = Array.from(table.querySelectorAll("tbody tr"));

    if (!bodyRows.length) {
      return -1;
    }

    const maxCells = Math.max(0, ...bodyRows.map(row => row.children.length));

    for (let index = 0; index < maxCells; index += 1) {
      const values = bodyRows
        .map(row => normalize(row.children[index]?.textContent || ""))
        .filter(Boolean);

      if (!values.length) {
        continue;
      }

      const buyRuleValues = values.filter(value =>
        value === "BUDGET ONLY" ||
        value === "NEED BUDGET"
      );

      if (buyRuleValues.length === values.length) {
        return index;
      }
    }

    return -1;
  }

  function normalize(value) {
    return String(value || "")
      .replace(/\s+/g, " ")
      .trim()
      .toUpperCase();
  }
})();
