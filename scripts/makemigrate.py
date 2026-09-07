import sys
from pathlib import Path

from alembic.command import revision
from alembic.config import Config

ROOT_DIR = Path(__file__).resolve().parent.parent


def main() -> None:
    message = None
    if len(sys.argv) > 1:
        message = sys.argv[1]

    revision(
        config=Config(str(ROOT_DIR / "alembic.ini")),
        autogenerate=True,
        message=message,
    )


if __name__ == "__main__":
    main()
