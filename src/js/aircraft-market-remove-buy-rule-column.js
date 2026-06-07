(() => {
  document.addEventListener("DOMContentLoaded", () => {
    removeBuyRuleColumns();
    installBuyRuleColumnObserver();
  });

  function installBuyRuleColumnObserver() {
    const observer = new MutationObserver(() => {
      removeBuyRuleColumns();
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true
    });

    window.setInterval(removeBuyRuleColumns, 700);
  }

  function removeBuyRuleColumns() {
    document.querySelectorAll("table").forEach(table => {
      let index = findBuyRuleColumnIndex(table);

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
    const headers = Array.from(table.querySelectorAll("thead th, tr:first-child th"));

    const headerIndex = headers.findIndex(header =>
      normalize(header.textContent) === "BUY RULE"
    );

    if (headerIndex >= 0) {
      return headerIndex;
    }

    const rows = Array.from(table.querySelectorAll("tbody tr, tr"))
      .filter(row => row.querySelector("td"));

    if (!rows.length) {
      return -1;
    }

    const maxCells = Math.max(0, ...rows.map(row => row.children.length));

    for (let index = 0; index < maxCells; index += 1) {
      const values = rows
        .map(row => normalize(row.children[index]?.textContent || ""))
        .filter(Boolean);

      if (!values.length) {
        continue;
      }

      const buyRuleLike = values.filter(value =>
        value === "BUDGET ONLY" ||
        value === "OPEN MARKET" ||
        value === "AVAILABLE" ||
        value === "BUDGET"
      );

      if (buyRuleLike.length >= Math.max(1, Math.floor(values.length * 0.7))) {
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
