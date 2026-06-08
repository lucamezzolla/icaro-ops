<?php
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

    $path = str_replace('\\', '/', $path);
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
