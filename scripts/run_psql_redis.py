import subprocess
from pathlib import Path

CONTAINERS_DIR = Path("/home/franco/Escritorio/Docker composes").resolve()


def run_docker_compose(compose_yml: str):
    subprocess.run(["sudo", "docker", "compose", "-f", compose_yml, "up", "-d"], cwd=CONTAINERS_DIR)


if __name__ == "__main__":
    run_docker_compose("postgres-compose.yml")
    run_docker_compose("redis-compose.yml")
