#!/usr/bin/env python3
from pathlib import Path

PROJECT = Path.cwd()
FLEET_JS = PROJECT / "src/js/fleet.js"
FLEET_CSS = PROJECT / "src/css/fleet.css"

def read(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")
    return path.read_text(encoding="utf-8")

def write(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")

def ensure_before(js: str, before_name: str, block: str, sentinel: str) -> str:
    if sentinel in js:
        return js
    for marker in ("\nasync function " + before_name + "(", "\nfunction " + before_name + "("):
        if marker in js:
            return js.replace(marker, "\n" + block.rstrip() + "\n" + marker, 1)
    return js.rstrip() + "\n\n" + block.rstrip() + "\n"

def patch_js() -> None:
    js = read(FLEET_JS)

    preview_function = '''function openImagePreviewDialog(title, src, alt) {
  const path = String(src || "").trim();

  if (!path) {
    showFleetError("No image is available for this aircraft model yet.");
    return;
  }

  const dialog = document.querySelector("#aircraftImageDialog");
  document.querySelector("#aircraftImageTitle").textContent = title || "Aircraft";

  const img = document.querySelector("#aircraftImagePreview");
  img.src = path;
  img.alt = alt || title || "Aircraft preview";

  dialog.showModal();
}'''
    js = ensure_before(js, "openAircraftImage", preview_function, "function openImagePreviewDialog(")

    bind_function = '''function bindCatalogModelImageButtons(root = document) {
  root.querySelectorAll("[data-catalog-model-image-src]").forEach(button => {
    button.addEventListener("click", () => {
      openImagePreviewDialog(
        button.dataset.catalogModelImageTitle || "Aircraft",
        button.dataset.catalogModelImageSrc || "",
        button.dataset.catalogModelImageAlt || "Aircraft preview"
      );
    });
  });
}'''
    js = ensure_before(js, "openAircraftImage", bind_function, "function bindCatalogModelImageButtons(")

    old = '${m.image_asset_path ? `<img src="${escapeHtml(m.image_asset_path)}" alt="${escapeHtml(m.manufacturer)} ${escapeHtml(m.model_name)}">` : `<p class="muted">No image available.</p>`}'
    new = '${m.image_asset_path ? `<button type="button" class="aircraft-detail-image-zoom-trigger" data-catalog-model-image-src="${escapeHtml(m.image_asset_path)}" data-catalog-model-image-title="${escapeHtml(m.manufacturer)} ${escapeHtml(m.model_name)}" data-catalog-model-image-alt="${escapeHtml(m.manufacturer)} ${escapeHtml(m.model_name)}" title="Open larger image" aria-label="Open larger image for ${escapeHtml(m.manufacturer)} ${escapeHtml(m.model_name)}"><img src="${escapeHtml(m.image_asset_path)}" alt="${escapeHtml(m.manufacturer)} ${escapeHtml(m.model_name)}"></button>` : `<p class="muted">No image available.</p>`}'
    if old in js:
        js = js.replace(old, new, 1)

    if "bindCatalogModelImageButtons(content);" not in js:
        markers = [
            '    const buyButton = content.querySelector("#buyModelFromDetailButton");\n',
            '    setCatalogModelDetailBuyFooter(m, detailDialog);\n',
            '  } catch (error) {\n'
        ]
        for marker in markers:
            if marker in js:
                js = js.replace(marker, "    bindCatalogModelImageButtons(content);\n\n" + marker, 1)
                break

    write(FLEET_JS, js)

def patch_css() -> None:
    css = read(FLEET_CSS)

    css = css.replace("  filter: brightness(1.08);\n", "")
    css = css.replace("  box-shadow: 0 18px 34px rgba(0, 0, 0, .28);\n", "")

    append = '''
/* Aircraft detail image hover/click preview without color change */
.aircraft-detail-image-zoom-trigger {
  display: grid;
  place-items: center;
  width: 100%;
  padding: 0;
  border: 0;
  border-radius: 16px;
  background: transparent;
  cursor: zoom-in;
  overflow: hidden;
}

.aircraft-detail-image-zoom-trigger img {
  max-width: 100%;
  max-height: 360px;
  object-fit: contain;
  border-radius: 14px;
  transition: transform .18s ease;
}

.aircraft-detail-image-zoom-trigger:hover img,
.aircraft-detail-image-zoom-trigger:focus-visible img {
  transform: scale(1.045);
}

.aircraft-detail-image-zoom-trigger:focus-visible {
  outline: 2px solid rgba(255,255,255,.45);
  outline-offset: 4px;
}

.image-dialog-body {
  display: grid;
  place-items: center;
}

#aircraftImagePreview {
  width: auto;
  max-width: 100%;
  max-height: 72vh;
  object-fit: contain;
  border-radius: 16px;
}
'''
    if "Aircraft detail image hover/click preview without color change" not in css:
        css += "\n" + append

    write(FLEET_CSS, css)

def main() -> None:
    patch_js()
    patch_css()
    print("Patched: catalog model detail image is clickable too, and hover no longer changes color/brightness/shadow.")

if __name__ == "__main__":
    main()
