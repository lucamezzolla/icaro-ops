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

def find_function_span(content: str, function_name: str):
    markers = [
        "async function " + function_name + "(",
        "function " + function_name + "(",
    ]

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

def replace_function(content: str, function_name: str, replacement: str) -> str:
    span = find_function_span(content, function_name)
    if not span:
        return content

    start, end = span
    return content[:start] + replacement.rstrip() + content[end:]

def insert_before_function(content: str, before_function: str, block: str, sentinel: str) -> str:
    if sentinel in content:
        return content

    for marker in ("\nasync function " + before_function + "(", "\nfunction " + before_function + "("):
        if marker in content:
            return content.replace(marker, "\n" + block.rstrip() + "\n" + marker, 1)

    return content.rstrip() + "\n\n" + block.rstrip() + "\n"

def ensure_owned_detail_image_block(js: str) -> str:
    # Ensure owned aircraft detail actually renders the image block.
    if "${aircraftDetailImageBlock(a)}" not in js:
        old = "function renderAircraftDetail(a, recentFlights) {\n  return `\n    <div class=\"detail-grid\">"
        new = "function renderAircraftDetail(a, recentFlights) {\n  return `\n    ${aircraftDetailImageBlock(a)}\n    <div class=\"detail-grid\">"
        if old in js:
            js = js.replace(old, new, 1)

    # Ensure click handlers are bound after aircraft detail is rendered.
    bind_line = "    bindAircraftDetailImageButtons(content);\n"
    if bind_line not in js:
        old = "    content.innerHTML = renderAircraftDetail(a, data.recent_flights || []);\n"
        if old in js:
            js = js.replace(old, old + bind_line, 1)

    return js

def patch_js() -> None:
    js = read(FLEET_JS)
    js = ensure_owned_detail_image_block(js)

    image_block = '''function aircraftDetailImageBlock(a) {
  const path = String(a.image_asset_path || "").trim();

  if (!path) {
    return "";
  }

  const aircraftName = `${a.manufacturer || ""} ${a.model_name || ""}`.trim() || "Aircraft";
  const aircraftId = Number(a.aircraft_id || 0);

  return `
    <div class="model-image-wrap owned-aircraft-image-wrap">
      <button
        type="button"
        class="aircraft-detail-image-zoom-trigger"
        data-aircraft-image-inline="${escapeHtml(aircraftId)}"
        title="Open larger image"
        aria-label="Open larger image for ${escapeHtml(aircraftName)}"
      >
        <img src="${escapeHtml(path)}" alt="${escapeHtml(aircraftName)}">
      </button>
    </div>
  `;
}'''
    if "function aircraftDetailImageBlock(" in js:
        js = replace_function(js, "aircraftDetailImageBlock", image_block)
    else:
        js = insert_before_function(js, "openAircraftImage", image_block, "function aircraftDetailImageBlock(")

    bind_function = '''function bindAircraftDetailImageButtons(root = document) {
  root.querySelectorAll("[data-aircraft-image-inline]").forEach(button => {
    button.addEventListener("click", () => {
      const aircraftId = Number(button.dataset.aircraftImageInline);

      if (Number.isInteger(aircraftId) && aircraftId > 0) {
        openAircraftImage(aircraftId);
      }
    });
  });
}'''
    js = insert_before_function(js, "openAircraftImage", bind_function, "function bindAircraftDetailImageButtons(")

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
    js = insert_before_function(js, "openAircraftImage", preview_function, "function openImagePreviewDialog(")

    open_aircraft_image = '''function openAircraftImage(aircraftId) {
  const a = ownedAircraft.find(item => Number(item.aircraft_id) === Number(aircraftId));
  if (!a) return;

  const aircraftName = `${a.manufacturer || ""} ${a.model_name || ""}`.trim() || "Aircraft";

  openImagePreviewDialog(
    aircraftName,
    a.image_asset_path || "",
    aircraftName
  );
}'''
    js = replace_function(js, "openAircraftImage", open_aircraft_image)

    write(FLEET_JS, js)

def patch_css() -> None:
    css = read(FLEET_CSS)

    append = '''
/* Owned aircraft detail image: hover hint + enlarged preview dialog */
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
  transition:
    transform .18s ease,
    filter .18s ease,
    box-shadow .18s ease;
}

.aircraft-detail-image-zoom-trigger:hover img,
.aircraft-detail-image-zoom-trigger:focus-visible img {
  transform: scale(1.045);
  filter: brightness(1.08);
  box-shadow: 0 18px 34px rgba(0, 0, 0, .28);
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

    if "Owned aircraft detail image: hover hint + enlarged preview dialog" not in css:
        css += "\n" + append

    write(FLEET_CSS, css)

def main() -> None:
    patch_js()
    patch_css()
    print("Patched: owned aircraft image now zooms slightly on hover and opens the larger image dialog on click.")

if __name__ == "__main__":
    main()
