DEFAULT_WORKERS = 1
DEFAULT_TIMEOUT = 30
DEFAULT_BACKLOG = 1024
DEFAULT_BACKPRESURE = 1024

if __name__ == "__main__":
    import argparse

    from granian.constants import Interfaces, Loops
    from granian.server import Server

    from src.common.infrastructure.core import settings

    args = argparse.ArgumentParser()

    args.add_argument("-d", "--dev", action="store_true", default=None)
    args.add_argument("-p", "--prod", action="store_true", default=None)
    # args.add_argument("--workers", type=int, default=DEFAULT_WORKERS)
    args.add_argument("--workers-kill-timeout", type=int, default=DEFAULT_TIMEOUT)
    args.add_argument("--backlog", type=int, default=DEFAULT_BACKLOG)
    args.add_argument("--backpressure", type=int, default=DEFAULT_BACKPRESURE)

    parsed = dict(args.parse_args().__dict__)

    if not parsed["dev"] and not parsed["prod"]:
        raise ValueError('Must specify either "dev" or "prod"')

    if parsed["dev"] and parsed["prod"]:
        raise ValueError('Cannot specify both "dev" and "prod"')

    if not settings.DOMAIN:
        raise ValueError("DOMAIN environment variable not set")

    HOST = settings.DOMAIN.split(":")[1].replace("//", "").replace("//", "")
    PORT = int(settings.DOMAIN.split(":")[-1])
    WORKERS = settings.WORKERS
    WORKERS_KILL_TIMEOUT = parsed["workers_kill_timeout"]
    BACKLOG = parsed["backlog"]
    BACKPRESSURE = parsed["backpressure"]
    LOOP = Loops.uvloop if parsed["prod"] else Loops.auto

    a = Server(
        target="main:app",
        address=HOST,
        port=PORT,
        interface=Interfaces.ASGI,
        workers=WORKERS,
        workers_kill_timeout=WORKERS_KILL_TIMEOUT,
        loop=Loops.uvloop,
        backlog=BACKLOG,
        backpressure=BACKPRESSURE,
    )

    a.serve()
