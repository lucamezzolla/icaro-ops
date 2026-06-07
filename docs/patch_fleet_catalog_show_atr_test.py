#!/usr/bin/env python3
from pathlib import Path

path = Path("api/public/fleet/catalog.php")
text = path.read_text(encoding="utf-8")

text = text.replace(
"""$starterModelCodes = [
    'C208B_GRAND_CARAVAN_EX',
];""",
"""$starterModelCodes = [
    'C208B_GRAND_CARAVAN_EX',
    'ATR42_600',
];"""
)

text = text.replace(
"$currentQualifiedPilots = count_qualified_pilots($pdo, $companyId, 'C208_TYPE');\n\n",
""
)

old_loop = """foreach ($stmt->fetchAll() as $row) {
    $requiredAfterPurchase = ($currentFleetCount + 1) * 2;

    $row['currency_code'] = $company['currency_code'];
    $row['current_qualified_pilots'] = $currentQualifiedPilots;
    $row['required_pilots_after_purchase'] = $requiredAfterPurchase;
    $row['pilot_coverage_ok_after_purchase'] = $currentQualifiedPilots >= $requiredAfterPurchase;
    $row['unlock_status'] = 'AVAILABLE_FOR_CURRENT_LEVEL';
    $row['unlock_note'] = 'Available for the current early-game operating level.';

    $aircraft[] = $row;
}"""

new_loop = """foreach ($stmt->fetchAll() as $row) {
    $requiredAfterPurchase = ($currentFleetCount + 1) * 2;
    $requiredLicense = required_pilot_type_license((string)$row['model_code']);
    $currentQualifiedPilots = count_qualified_pilots($pdo, $companyId, $requiredLicense);

    $row['currency_code'] = $company['currency_code'];
    $row['required_license'] = $requiredLicense;
    $row['current_qualified_pilots'] = $currentQualifiedPilots;
    $row['required_pilots_after_purchase'] = $requiredAfterPurchase;
    $row['pilot_coverage_ok_after_purchase'] = $currentQualifiedPilots >= $requiredAfterPurchase;
    $row['unlock_status'] = 'AVAILABLE_FOR_DEVELOPMENT_TEST';
    $row['unlock_note'] = 'Temporarily visible for ATR purchase testing.';

    $aircraft[] = $row;
}"""

if old_loop not in text:
    raise SystemExit("Could not find catalog foreach block. Send me api/public/fleet/catalog.php")

text = text.replace(old_loop, new_loop)

if "function required_pilot_type_license(" not in text:
    marker = "function count_qualified_pilots("
    helper = """
function required_pilot_type_license(string $modelCode): ?string
{
    return match ($modelCode) {
        'C208B_GRAND_CARAVAN_EX' => 'C208_TYPE',
        'DHC6_TWIN_OTTER_400' => 'DHC6_TYPE',
        'ATR42_600' => 'ATR42_TYPE',
        default => null,
    };
}

"""
    text = text.replace(marker, helper + marker, 1)

text = text.replace(
"function count_qualified_pilots(PDO $pdo, int $companyId, string $typeRating): int",
"function count_qualified_pilots(PDO $pdo, int $companyId, ?string $typeRating): int"
)

old_count = """function count_qualified_pilots(PDO $pdo, int $companyId, ?string $typeRating): int
{
    $stmt = $pdo->prepare("
        SELECT COUNT(DISTINCT s.id)
        FROM company_staff s
        WHERE s.company_id = :company_id
          AND s.staff_role = 'PILOT'
          AND s.employment_status = 'ACTIVE'
          AND EXISTS (
            SELECT 1
            FROM company_staff_licenses l
            WHERE l.company_staff_id = s.id
              AND l.license_code = 'CPL'
          )
          AND EXISTS (
            SELECT 1
            FROM company_staff_licenses l
            WHERE l.company_staff_id = s.id
              AND l.license_code = :type_rating
          )
    ");
    $stmt->execute([
        'company_id' => $companyId,
        'type_rating' => $typeRating,
    ]);

    return (int)$stmt->fetchColumn();
}"""

new_count = """function count_qualified_pilots(PDO $pdo, int $companyId, ?string $typeRating): int
{
    $sql = "
        SELECT COUNT(DISTINCT s.id)
        FROM company_staff s
        WHERE s.company_id = :company_id
          AND s.staff_role = 'PILOT'
          AND s.employment_status = 'ACTIVE'
          AND EXISTS (
            SELECT 1
            FROM company_staff_licenses l
            WHERE l.company_staff_id = s.id
              AND l.license_code = 'CPL'
          )
    ";

    $params = ['company_id' => $companyId];

    if ($typeRating !== null) {
        $sql .= "
          AND EXISTS (
            SELECT 1
            FROM company_staff_licenses l
            WHERE l.company_staff_id = s.id
              AND l.license_code = :type_rating
          )
        ";
        $params['type_rating'] = $typeRating;
    }

    $stmt = $pdo->prepare($sql);
    $stmt->execute($params);

    return (int)$stmt->fetchColumn();
}"""

if old_count in text:
    text = text.replace(old_count, new_count)

path.write_text(text, encoding="utf-8")
print("OK: Fleet catalog now shows ATR for development test and uses per-model pilot coverage.")
