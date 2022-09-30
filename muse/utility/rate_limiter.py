from typing import List, Tuple

from ratelimit import Rule

from muse.CONST import MUSE_LOAD_TESTING, RATE_LIMIT_KEY


# TODO: improve unique user (ip) detection logic. Use Session or JWT
async def auth_function(scope) -> Tuple[str, str]:
    if MUSE_LOAD_TESTING:
        return "", "load_test"

    ip = ""
    if scope["client"]:
        ip, port = tuple(scope["client"])

    for name, value in scope["headers"]:  # type: bytes, bytes
        if name == b"x-api-key":
            api_key = value.decode("utf8")
            if RATE_LIMIT_KEY == api_key:
                return ip, "internal"

    if ip == "127.0.0.1":
        return ip, "localhost"

    for name, value in scope["headers"]:  # type: bytes, bytes
        if name == b"x-real-ip":
            ip = value.decode("utf8")

    return ip, "default"


RULES: List[Rule] = [
    Rule(second=1, group="default"),  # global unique users
    Rule(minute=10, group="localhost"),  # 127.0.0.1
    Rule(minute=400, group="internal"),  # Slack Bot
    Rule(group="load_test"),  # No limit when load testing
]
