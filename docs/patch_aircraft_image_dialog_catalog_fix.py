#!/usr/bin/env python3
from pathlib import Path
import re

PROJECT = Path.cwd()

def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")

def write(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")

def require_file(rel: str) -> Path:
    path = PROJECT / rel
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {rel}")
    return path

def replace_or_fail(content: str, old: str, new: str, label: str) -> str:
    if old not in content:
        raise RuntimeError(f"Unable to patch {label}: expected block not found.")
    return content.replace(old, new, 1)

def ensure_line_after(content: str, needle: str, line: str) -> str:
    if line in content:
        return content
    if needle not in content:
        raise RuntimeError(f"Expected line not found: {needle!r}")
    return content.replace(needle, needle + line, 1)

def patch_aircraft_images_helper() -> None:
    path = PROJECT / "api/lib/aircraft-images.php"
    path.parent.mkdir(parents=True, exist_ok=True)

    helper = '''<?php
declare(strict_types=1);

/**
 * Aircraft image resolver.
 *
 * It connects DB aircraft models to PNG files placed in:
 *
 *   src/assets/aircraft/
 *
 * It supports:
 * - numbered files: 290_socata_tbm_700.png
 * - legacy files: c208b_grand_caravan_ex.png, concorde.png, airbus_a220_100.png
 * - existing aircraft_models.image_asset_path values
 */
function aircraft_image_asset_path_from_row(array $row): string
{
    $existing = normalize_aircraft_image_asset_path(trim((string)($row['image_asset_path'] ?? '')));

    if ($existing !== '' && aircraft_image_path_is_usable($existing)) {
        return $existing;
    }

    $modelId = (int)($row['aircraft_model_id'] ?? $row['id'] ?? $row['model_id'] ?? 0);

    if ($modelId > 0) {
        $byId = aircraft_image_asset_path_by_model_id($modelId);

        if ($byId !== '') {
            return $byId;
        }
    }

    return aircraft_image_asset_path_by_row_candidates($row);
}

function attach_aircraft_image_asset_path(array $row): array
{
    $row['image_asset_path'] = aircraft_image_asset_path_from_row($row);
    return $row;
}

/**
 * @param array<int,array<string,mixed>> $rows
 * @return array<int,array<string,mixed>>
 */
function attach_aircraft_image_asset_paths(array $rows): array
{
    return array_map('attach_aircraft_image_asset_path', $rows);
}

function aircraft_image_asset_path_by_model_id(int $modelId): string
{
    static $cache = [];

    if (array_key_exists($modelId, $cache)) {
        return $cache[$modelId];
    }

    $assetsDir = aircraft_image_assets_dir();
    $prefix = sprintf('%03d_', $modelId);

    if (!is_dir($assetsDir)) {
        $cache[$modelId] = '';
        return '';
    }

    $matches = glob($assetsDir . '/' . $prefix . '*.png') ?: [];
    natsort($matches);
    $matches = array_values($matches);

    if (!$matches) {
        $cache[$modelId] = '';
        return '';
    }

    $cache[$modelId] = aircraft_image_web_path_from_absolute($matches[0]);
    return $cache[$modelId];
}

function aircraft_image_asset_path_by_row_candidates(array $row): string
{
    static $allPngBasenames = null;

    $assetsDir = aircraft_image_assets_dir();

    if (!is_dir($assetsDir)) {
        return '';
    }

    if ($allPngBasenames === null) {
        $allPngBasenames = [];

        foreach ((glob($assetsDir . '/*.png') ?: []) as $file) {
            $allPngBasenames[basename($file)] = $file;
        }
    }

    $candidateNames = aircraft_image_candidate_basenames(
        (string)($row['manufacturer'] ?? ''),
        (string)($row['model_name'] ?? ''),
        (string)($row['model_code'] ?? ''),
        (string)($row['icao_type_code'] ?? '')
    );

    foreach ($candidateNames as $basename) {
        if (isset($allPngBasenames[$basename])) {
            return aircraft_image_web_path_from_absolute($allPngBasenames[$basename]);
        }
    }

    return '';
}

function aircraft_image_candidate_basenames(
    string $manufacturer,
    string $modelName,
    string $modelCode,
    string $icaoTypeCode
): array {
    $slugs = [];

    foreach ([$modelCode, $modelName, $manufacturer . ' ' . $modelName, $icaoTypeCode] as $value) {
        $slug = aircraft_image_slug($value);

        if ($slug !== '') {
            $slugs[] = $slug;
        }
    }

    $simplifiedModel = aircraft_image_slug(
        str_replace(
            [' Series ', ' series ', ' / ', '/', '-', ' '],
            [' ', ' ', ' ', ' ', '', '_'],
            $modelName
        )
    );

    if ($simplifiedModel !== '') {
        $slugs[] = $simplifiedModel;
        $slugs[] = aircraft_image_slug($manufacturer . ' ' . $simplifiedModel);
    }

    $candidateNames = [];

    foreach (array_values(array_unique($slugs)) as $slug) {
        $candidateNames[] = $slug . '.png';

        if (preg_match('/^[a-z0-9]+_([a-z0-9_]+)$/', $slug, $matches) === 1) {
            $candidateNames[] = $matches[1] . '.png';
        }
    }

    return array_values(array_unique($candidateNames));
}

function aircraft_image_slug(string $value): string
{
    $value = trim($value);

    if ($value === '') {
        return '';
    }

    $transliterated = iconv('UTF-8', 'ASCII//TRANSLIT//IGNORE', $value);

    if ($transliterated !== false) {
        $value = $transliterated;
    }

    $value = strtolower($value);
    $value = str_replace('&', ' and ', $value);
    $value = preg_replace('/[^a-z0-9]+/', '_', $value) ?? '';
    $value = trim($value, '_');
    $value = preg_replace('/_+/', '_', $value) ?? '';

    return $value;
}

function normalize_aircraft_image_asset_path(string $path): string
{
    $path = trim($path);

    if ($path === '') {
        return '';
    }

    if (preg_match('~^https?://~i', $path) === 1) {
        return $path;
    }

    $path = str_replace('\\\\', '/', $path);
    $path = ltrim($path, '/');

    if (str_starts_with($path, 'src/assets/aircraft/')) {
        return $path;
    }

    if (str_starts_with($path, 'assets/aircraft/')) {
        return 'src/' . $path;
    }

    if (!str_contains($path, '/')) {
        return 'src/assets/aircraft/' . $path;
    }

    return $path;
}

function aircraft_image_path_is_usable(string $path): bool
{
    if ($path === '') {
        return false;
    }

    if (preg_match('~^https?://~i', $path) === 1) {
        return true;
    }

    return is_file(aircraft_image_project_root() . '/' . ltrim($path, '/'));
}

function aircraft_image_web_path_from_absolute(string $absolutePath): string
{
    return 'src/assets/aircraft/' . basename($absolutePath);
}

function aircraft_image_assets_dir(): string
{
    return aircraft_image_project_root() . '/src/assets/aircraft';
}

function aircraft_image_project_root(): string
{
    return dirname(__DIR__, 2);
}
'''
    write(path, helper)

def patch_php_requires_and_catalog_filter() -> None:
    php_files = [
        "api/public/fleet/catalog.php",
        "api/public/fleet/detail.php",
        "api/public/fleet/model-detail.php",
        "api/public/fleet/my-aircraft.php",
    ]

    for rel in php_files:
        path = require_file(rel)
        content = read(path)
        content = ensure_line_after(
            content,
            "require __DIR__ . '/../../lib/bootstrap.php';\n",
            "require __DIR__ . '/../../lib/aircraft-images.php';\n"
        )
        write(path, content)

    replacements = {
        "api/public/fleet/my-aircraft.php": (
            "$aircraft = $stmt->fetchAll();",
            "$aircraft = attach_aircraft_image_asset_paths($stmt->fetchAll());"
        ),
        "api/public/fleet/detail.php": (
            "if (!$aircraft) {\n    json_response(['error' => 'AIRCRAFT_NOT_FOUND'], 404);\n}\n\n$flightStmt = $pdo->prepare(",
            "if (!$aircraft) {\n    json_response(['error' => 'AIRCRAFT_NOT_FOUND'], 404);\n}\n\n$aircraft = attach_aircraft_image_asset_path($aircraft);\n\n$flightStmt = $pdo->prepare("
        ),
        "api/public/fleet/model-detail.php": (
            "if (!$model) {\n    json_response(['error' => 'AIRCRAFT_MODEL_NOT_FOUND'], 404);\n}\n\njson_response(['model' => $model]);",
            "if (!$model) {\n    json_response(['error' => 'AIRCRAFT_MODEL_NOT_FOUND'], 404);\n}\n\n$model = attach_aircraft_image_asset_path($model);\n$model['purchase_rule'] = 'BUDGET_ONLY';\n$model['is_available_for_current_level'] = true;\n$model['unlock_status'] = 'AVAILABLE_FOR_DEVELOPMENT_TEST';\n$model['unlock_note'] = 'Development mode: all active aircraft are visible. Purchase is limited only by budget.';\n\njson_response(['model' => $model]);"
        ),
    }

    for rel, (old, new) in replacements.items():
        path = require_file(rel)
        content = read(path)
        if new not in content and old in content:
            content = content.replace(old, new, 1)
        write(path, content)

    catalog_path = require_file("api/public/fleet/catalog.php")
    catalog = read(catalog_path)

    if "WHERE COALESCE(is_active, 1) = 1" not in catalog:
        catalog = catalog.replace(
            "    FROM aircraft_models\n    ORDER BY",
            "    FROM aircraft_models\n    WHERE COALESCE(is_active, 1) = 1\n    ORDER BY",
            1
        )

    if "$aircraft[] = attach_aircraft_image_asset_path($row);" not in catalog:
        catalog = catalog.replace(
            "    $row['unlock_status'] = 'AVAILABLE_FOR_DEVELOPMENT_TEST';\n"
            "    $row['unlock_note'] = 'Development mode: all aircraft are visible. Purchase is limited only by budget.';\n\n"
            "    $aircraft[] = $row;\n",
            "    $row['unlock_status'] = 'AVAILABLE_FOR_DEVELOPMENT_TEST';\n"
            "    $row['unlock_note'] = 'Development mode: all active aircraft are visible. Purchase is limited only by budget.';\n"
            "    $row['is_available_for_current_level'] = true;\n\n"
            "    $aircraft[] = attach_aircraft_image_asset_path($row);\n",
            1
        )

    write(catalog_path, catalog)

def replace_function(content: str, function_name: str, new_function: str, before_function: str | None = None) -> str:
    pattern = rf"\nfunction {re.escape(function_name)}\([^{{]*\) \{{.*?\n\}}"
    match = re.search(pattern, content, flags=re.S)

    if match:
        return content[:match.start()] + "\n" + new_function.rstrip() + content[match.end():]

    if before_function:
        marker = f"\nfunction {before_function}("
        if marker not in content:
            raise RuntimeError(f"Unable to insert function {function_name}: marker {before_function} not found.")
        return content.replace(marker, "\n" + new_function.rstrip() + "\n" + marker, 1)

    raise RuntimeError(f"Function {function_name} not found.")

def patch_fleet_js() -> None:
    path = require_file("src/js/fleet.js")
    js = read(path)

    old = "    content.innerHTML = renderAircraftDetail(a, data.recent_flights || []);\n"
    new = "    content.innerHTML = renderAircraftDetail(a, data.recent_flights || []);\n    bindAircraftDetailImageButtons(content);\n"
    if new not in js:
        js = replace_or_fail(js, old, new, "src/js/fleet.js owned aircraft detail binding")

    old = '    const buyButton = content.querySelector("#buyModelFromDetailButton");\n'
    new = '    bindCatalogModelImageButtons(content);\n\n    const buyButton = content.querySelector("#buyModelFromDetailButton");\n'
    if new not in js:
        js = replace_or_fail(js, old, new, "src/js/fleet.js catalog image binding")

    js = replace_function(
        js,
        "aircraftDetailImageBlock",
        '''function aircraftDetailImageBlock(a) {
  const path = String(a.image_asset_path || "").trim();

  if (!path) {
    return "";
  }

  const aircraftName = `${a.manufacturer || ""} ${a.model_name || ""}`.trim() || "Aircraft";

  return `
    <button type="button" class="aircraft-detail-image-button" data-aircraft-image-inline="${escapeHtml(a.aircraft_id || "")}" title="Open larger image">
      <img src="${escapeHtml(path)}" alt="${escapeHtml(aircraftName)}">
    </button>
  `;
}''',
        before_function="openAircraftImage"
    )

    if "function bindAircraftDetailImageButtons" not in js:
        js = js.replace(
            "\nfunction openAircraftImage(aircraftId) {",
            '''
function bindAircraftDetailImageButtons(root = document) {
  root.querySelectorAll("[data-aircraft-image-inline]").forEach(button => {
    button.addEventListener("click", () => {
      const aircraftId = Number(button.dataset.aircraftImageInline);

      if (Number.isInteger(aircraftId) && aircraftId > 0) {
        openAircraftImage(aircraftId);
      }
    });
  });
}

function bindCatalogModelImageButtons(root = document) {
  root.querySelectorAll("[data-catalog-model-image-src]").forEach(button => {
    button.addEventListener("click", () => {
      openImagePreviewDialog(
        button.dataset.catalogModelImageTitle || "Aircraft",
        button.dataset.catalogModelImageSrc || "",
        button.dataset.catalogModelImageAlt || "Aircraft preview"
      );
    });
  });
}

function openImagePreviewDialog(title, src, alt) {
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
}
''' + "\nfunction openAircraftImage(aircraftId) {",
            1
        )

    js = replace_function(
        js,
        "openAircraftImage",
        '''function openAircraftImage(aircraftId) {
  const a = ownedAircraft.find(item => Number(item.aircraft_id) === Number(aircraftId));
  if (!a) return;

  const aircraftName = `${a.manufacturer || ""} ${a.model_name || ""}`.trim() || "Aircraft";
  openImagePreviewDialog(
    aircraftName,
    a.image_asset_path || "",
    aircraftName
  );
}''',
        before_function="openBuyDialog"
    )

    old = '${m.image_asset_path ? `<img src="${escapeHtml(m.image_asset_path)}" alt="${escapeHtml(m.manufacturer)} ${escapeHtml(m.model_name)}">` : `<p class="muted">No image available.</p>`}'
    new = '${m.image_asset_path ? `<button type="button" class="aircraft-detail-image-button" data-catalog-model-image-src="${escapeHtml(m.image_asset_path)}" data-catalog-model-image-title="${escapeHtml(m.manufacturer)} ${escapeHtml(m.model_name)}" data-catalog-model-image-alt="${escapeHtml(m.manufacturer)} ${escapeHtml(m.model_name)}" title="Open larger image"><img src="${escapeHtml(m.image_asset_path)}" alt="${escapeHtml(m.manufacturer)} ${escapeHtml(m.model_name)}"></button>` : `<p class="muted">No image available.</p>`}'
    if old in js and new not in js:
        js = js.replace(old, new, 1)

    write(path, js)

def patch_fleet_css() -> None:
    path = require_file("src/css/fleet.css")
    css = read(path)

    append = '''

/* Aircraft detail image enlargement */
.aircraft-detail-image-button {
  display: grid;
  place-items: center;
  width: 100%;
  padding: 0;
  border: 0;
  border-radius: 16px;
  background: transparent;
  cursor: zoom-in;
}

.aircraft-detail-image-button img {
  max-width: 100%;
  max-height: 360px;
  object-fit: contain;
  border-radius: 14px;
}

.aircraft-detail-image-button:hover img,
.aircraft-detail-image-button:focus-visible img {
  filter: brightness(1.08);
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

    if "Aircraft detail image enlargement" not in css:
        css += append

    write(path, css)

def main() -> None:
    patch_aircraft_images_helper()
    patch_php_requires_and_catalog_filter()
    patch_fleet_js()
    patch_fleet_css()

    print("Patch applied successfully.")
    print("Changed/created:")
    print("- api/lib/aircraft-images.php")
    print("- api/public/fleet/catalog.php")
    print("- api/public/fleet/detail.php")
    print("- api/public/fleet/model-detail.php")
    print("- api/public/fleet/my-aircraft.php")
    print("- src/js/fleet.js")
    print("- src/css/fleet.css")

if __name__ == "__main__":
    main()
