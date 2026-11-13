"""Fail if tracked release files contain common private artifacts."""
import subprocess
from pathlib import Path


def violations(paths):
    bad = []
    for name in paths:
        p = Path(name)
        lower = name.lower()
        if (set(p.parts) & {'backups', 'private_imports', '.optpoke', '.venv', 'node_modules', 'sprites'}
            or p.suffix.lower() in {'.db', '.sqlite', '.sqlite3', '.xlsx', '.xlsm', '.xls', '.zip', '.png', '.jpg'}
            or p.name.startswith('.env') or '.db-' in lower
            or (p.suffix == '.json' and any(x in lower for x in ('backup', 'respaldo')))):
            bad.append(name)
    return bad


if __name__ == '__main__':
    files = subprocess.check_output(['git', 'ls-files', '-z']).decode().split('\0')
    bad = violations(filter(None, files))
    if bad:
        raise SystemExit('Archivos no publicables: ' + ', '.join(bad))
    print('Revisión de archivos versionados: OK (no sustituye revisión manual de contenido).')
