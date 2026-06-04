<?php
declare(strict_types=1);

/*
 * Copy this file to:
 *
 *   api/config.local.php
 *
 * Then adjust the values for your local MySQL installation.
 * Do NOT commit api/config.local.php.
 */

return [
    'db' => [
        'host' => '127.0.0.1',
        'port' => 3306,
        'database' => 'icaro_ops',
        'username' => 'icaro_ops_app',
        'password' => 'change-me',
        'charset' => 'utf8mb4',
    ],
];
