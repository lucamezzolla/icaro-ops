#!/usr/bin/env python3
from pathlib import Path

PROJECT = Path.cwd()
FLEET_JS = PROJECT / "src/js/fleet.js"
FLEET_CSS = PROJECT / "src/css/fleet.css"

def read(path):
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")
    return path.read_text(encoding="utf-8")

def write(path, content):
    path.write_text(content, encoding="utf-8")

def find_function_span(content, function_name):
    markers = ["async function " + function_name + "(", "function " + function_name + "("]
    start = -1
    for marker in markers:
        start = content.find(marker)
        if start >= 0:
            break
    if start < 0:
        return None
    brace = content.find("{", start)
    if brace < 0:
        return None

    depth = 0
    i = brace
    in_string = None
    escape = False
    in_line_comment = False
    in_block_comment = False
    template_depth = 0

    while i < len(content):
        ch = content[i]
        nxt = content[i + 1] if i + 1 < len(content) else ""
        if in_line_comment:
            if ch == "\n":
                in_line_comment = False
            i += 1
            continue
        if in_block_comment:
            if ch == "*" and nxt == "/":
                in_block_comment = False
                i += 2
                continue
            i += 1
            continue
        if in_string:
            if escape:
                escape = False
                i += 1
                continue
            if ch == "\\":
                escape = True
                i += 1
                continue
            if in_string == "`":
                if ch == "$" and nxt == "{":
                    template_depth += 1
                    i += 2
                    continue
                if ch == "}" and template_depth > 0:
                    template_depth -= 1
                    i += 1
                    continue
                if ch == "`" and template_depth == 0:
                    in_string = None
                    i += 1
                    continue
            elif ch == in_string:
                in_string = None
                i += 1
                continue
            i += 1
            continue
        if ch == "/" and nxt == "/":
            in_line_comment = True
            i += 2
            continue
        if ch == "/" and nxt == "*":
            in_block_comment = True
            i += 2
            continue
        if ch in ("'", '"', "`"):
            in_string = ch
            i += 1
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return start, i + 1
        i += 1
    return None

def replace_function(content, function_name, replacement):
    span = find_function_span(content, function_name)
    if not span:
        raise RuntimeError(f"Function not found or not parseable: {function_name}")
    start, end = span
    return content[:start] + replacement.rstrip() + content[end:]

def insert_before_first_function(content, block, sentinel, function_names):
    if sentinel in content:
        return content
    for function_name in function_names:
        for marker in ("\nasync function " + function_name + "(", "\nfunction " + function_name + "("):
            if marker in content:
                return content.replace(marker, "\n" + block.rstrip() + "\n" + marker, 1)
    return content.rstrip() + "\n\n" + block.rstrip() + "\n"

def patch_filter_focus(js):
    replacement = r'''function wireAircraftMarketFilters(root) {
  const search = root.querySelector("#aircraftMarketSearch");
  const manufacturer = root.querySelector("#aircraftMarketManufacturer");
  const engine = root.querySelector("#aircraftMarketEngine");
  const maxPrice = root.querySelector("#aircraftMarketMaxPrice");
  const clear = root.querySelector("#aircraftMarketClearFilters");

  const refreshKeepingFocus = sourceElement => {
    const activeId = sourceElement?.id || document.activeElement?.id || "";
    const selectionStart = sourceElement && "selectionStart" in sourceElement ? sourceElement.selectionStart : null;
    const selectionEnd = sourceElement && "selectionEnd" in sourceElement ? sourceElement.selectionEnd : null;

    renderCatalog(catalogAircraft);

    if (!activeId) {
      return;
    }

    requestAnimationFrame(() => {
      const next = document.querySelector(`#${CSS.escape(activeId)}`);

      if (!next) {
        return;
      }

      next.focus({ preventScroll: true });

      if (selectionStart !== null && selectionEnd !== null && typeof next.setSelectionRange === "function") {
        next.setSelectionRange(selectionStart, selectionEnd);
      }
    });
  };

  search?.addEventListener("input", () => {
    catalogFilterState.search = search.value;
    refreshKeepingFocus(search);
  });

  manufacturer?.addEventListener("change", () => {
    catalogFilterState.manufacturer = manufacturer.value;
    refreshKeepingFocus(manufacturer);
  });

  engine?.addEventListener("change", () => {
    catalogFilterState.engineType = engine.value;
    refreshKeepingFocus(engine);
  });

  maxPrice?.addEventListener("input", () => {
    catalogFilterState.maxPrice = maxPrice.value;
    refreshKeepingFocus(maxPrice);
  });

  clear?.addEventListener("click", () => {
    catalogFilterState = {
      search: "",
      manufacturer: "",
      engineType: "",
      maxPrice: ""
    };

    renderCatalog(catalogAircraft);

    requestAnimationFrame(() => {
      document.querySelector("#aircraftMarketSearch")?.focus({ preventScroll: true });
    });
  });
}'''
    return replace_function(js, "wireAircraftMarketFilters", replacement)

def patch_buy_footer(js):
    helper = r'''function setCatalogModelDetailBuyFooter(model, detailDialog) {
  const footer = document.querySelector("#aircraftDetailDialog .dialog-footer");

  if (!footer) {
    return;
  }

  const modelId = Number(model.aircraft_model_id || model.id || 0);
  const canBuy = Boolean(model.is_available_for_current_level) && Number.isInteger(modelId) && modelId > 0;

  footer.innerHTML = `
    <div class="dialog-footer-actions">
      <button
        type="button"
        class="primary-button aircraft-buy-footer-button"
        id="buyModelFromDetailButton"
        ${canBuy ? "" : "disabled"}
        title="${canBuy ? "Buy this aircraft" : "This aircraft cannot be bought right now"}"
      >
        <span aria-hidden="true">💰</span>
        <span>Buy this aircraft</span>
      </button>
    </div>
    <button value="close">Close</button>
  `;

  const buyButton = footer.querySelector("#buyModelFromDetailButton");

  if (buyButton && canBuy) {
    buyButton.addEventListener("click", async () => {
      const purchased = await buyAircraft(modelId);

      if (purchased) {
        detailDialog.close();
      }
    });
  }
}'''
    js = insert_before_first_function(js, helper, "function setCatalogModelDetailBuyFooter(", ["buyAircraft", "closeDialogIfOpen", "chooseDeliveryAirport"])

    inline_block = '''      <div class="dialog-action-bar">
        <button type="button" ${m.is_available_for_current_level ? "" : "disabled"} id="buyModelFromDetailButton">
          Buy this aircraft
        </button>
      </div>
'''
    js = js.replace(inline_block, "")

    listener_block = '''    const buyButton = content.querySelector("#buyModelFromDetailButton");
    if (buyButton && m.is_available_for_current_level) {
      buyButton.addEventListener("click", async () => {
        const purchased = await buyAircraft(Number(m.aircraft_model_id || m.id));

        if (purchased) {
          detailDialog.close();
        }
      });
    }
'''
    if listener_block in js:
        js = js.replace(listener_block, "    setCatalogModelDetailBuyFooter(m, detailDialog);\n", 1)
    elif "setCatalogModelDetailBuyFooter(m, detailDialog);" not in js:
        marker = "    title.textContent = `${m.manufacturer} ${m.model_name}`;\n"
        if marker in js:
            js = js.replace(marker, marker + "    setCatalogModelDetailBuyFooter(m, detailDialog);\n", 1)
        else:
            raise RuntimeError("Unable to place the footer Buy button call in openCatalogModelDetail().")
    return js

def patch_js():
    js = read(FLEET_JS)
    js = patch_filter_focus(js)
    js = patch_buy_footer(js)
    write(FLEET_JS, js)

def patch_css():
    css = read(FLEET_CSS)
    append = r'''
/* Aircraft market focus and catalog detail footer buy button */
.aircraft-buy-footer-button {
  display: inline-flex;
  align-items: center;
  gap: .45rem;
  font-weight: 800;
}

.aircraft-market-filter-panel input:focus,
.aircraft-market-filter-panel select:focus {
  outline: 2px solid rgba(255,255,255,.35);
  outline-offset: 2px;
}
'''
    if "Aircraft market focus and catalog detail footer buy button" not in css:
        css += "\n" + append
    write(FLEET_CSS, css)

def main():
    patch_js()
    patch_css()
    print("Patched: aircraft market filters keep focus and Buy button moved to footer.")

if __name__ == "__main__":
    main()
