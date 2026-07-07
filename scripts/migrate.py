"""Run database migrations using Alembic.

Usage:
    python scripts/migrate.py          # upgrade to latest
    python scripts/migrate.py downgrade  # downgrade one step
"""

import sys
from pathlib import Path

import alembic.config

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    argv = ["-c", str(ROOT / "alembic.ini"), "upgrade", "head"]

    if len(sys.argv) > 1 and sys.argv[1] == "downgrade":
        argv = ["-c", str(ROOT / "alembic.ini"), "downgrade", "-1"]

    alembic.config.main(argv=argv)


if __name__ == "__main__":
    main()
