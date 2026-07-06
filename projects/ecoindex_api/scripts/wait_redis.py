"""Dev helper: resolve a reachable Redis host for local development."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time

from redis import Redis
from redis.exceptions import ConnectionError

CONTAINER = "ecoindex-dev-redis"
DEFAULT_GATEWAY_HOST = "172.17.0.1"


def candidate_hosts() -> list[str]:
    if os.path.exists("/.dockerenv"):
        hosts = [DEFAULT_GATEWAY_HOST, "localhost", "127.0.0.1"]
    else:
        hosts = ["localhost", "127.0.0.1", DEFAULT_GATEWAY_HOST]
    try:
        data = json.loads(
            subprocess.check_output(
                ["docker", "inspect", CONTAINER],
                stderr=subprocess.DEVNULL,
            )
        )[0]
        networks = data.get("NetworkSettings", {}).get("Networks", {})
        if networks:
            ip = next(iter(networks.values()))["IPAddress"]
            hosts.append(ip)
    except (
        subprocess.CalledProcessError,
        StopIteration,
        KeyError,
        IndexError,
        json.JSONDecodeError,
    ):
        pass
    return list(dict.fromkeys(hosts))


def ping(host: str) -> bool:
    try:
        return Redis(host=host, socket_connect_timeout=1).ping()
    except ConnectionError:
        return False


def resolve_host() -> str:
    for host in candidate_hosts():
        if ping(host):
            return host
    raise RuntimeError("Redis is not reachable")


def main() -> None:
    for _ in range(50):
        try:
            print(resolve_host())
            return
        except RuntimeError:
            time.sleep(0.2)
    raise SystemExit("Redis is not ready")


if __name__ == "__main__":
    main()
