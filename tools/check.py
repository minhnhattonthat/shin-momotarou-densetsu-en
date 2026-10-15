"""One-command check: tests + text lint. The pre-commit hook runs this.

    python -X utf8 tools/check.py
"""
import subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    rc = subprocess.call([sys.executable, '-X', 'utf8', '-m', 'pytest', '-q', str(ROOT / 'tests')], cwd=ROOT)
    if rc:
        print('check: tests failed')
        return rc
    lint = ROOT / 'tools' / 'lint.py'
    if lint.exists():
        rc = subprocess.call([sys.executable, '-X', 'utf8', str(lint)], cwd=ROOT)
        if rc:
            print('check: lint failed')
            return rc
    print('check: OK')
    return 0


if __name__ == '__main__':
    sys.exit(main())
