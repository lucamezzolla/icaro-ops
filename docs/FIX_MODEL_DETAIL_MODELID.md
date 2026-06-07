# Fix model-detail modelId support

This patch fixes the aircraft market Details button when the frontend calls:

```text
api/public/fleet/model-detail.php?modelId=<id>
```

The endpoint already had a resolver able to read `modelId`, `id`, `model_code` and `icao`, but the main code path still used only:

```php
filter_input(INPUT_GET, 'id', FILTER_VALIDATE_INT)
```

So `modelId=46` was rejected with `INVALID_MODEL_ID`.

The patched endpoint now initializes `$pdo` first and resolves the model id through:

```php
$modelId = resolve_aircraft_model_id_from_request($pdo);
```

Validation command:

```bash
php -l api/public/fleet/model-detail.php
```

Expected result:

```text
No syntax errors detected in api/public/fleet/model-detail.php
```
