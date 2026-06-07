from pathlib import Path
import shutil

root = Path.cwd()
target = root / 'api/public/staff/candidates.php'
source = root / 'api/public/staff/candidates.php'

# This patch ZIP already contains the corrected candidates.php at the same path.
# Keep a timestamp-free backup only once for easier rollback during local tests.
backup = root / 'api/public/staff/candidates.php.before_staff_pdo_model_search_fix'

if not target.exists():
    raise SystemExit('Missing api/public/staff/candidates.php')

if not backup.exists():
    shutil.copy2(target, backup)

# File is overwritten by unzip before this script is run; this script exists to keep
# the workflow consistent and to create the local backup.
print('Staff candidates API patch applied. Backup:', backup)
