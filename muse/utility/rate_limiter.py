from typing import List, Tuple

from ratelimit import Rule
from ratelimit.auths.ip import client_ip


async def auth_function(scope) -> Tuple[str, str]:
    if scope["client"]:
        ip, port = tuple(scope["client"])
    if ip == "127.0.0.1":
        return ip, "localhost"

    user_unique_id, user_group = await client_ip(scope)
    if user_unique_id.endswith("litng.ai"):
        user_group = "internal"
    return user_unique_id, user_group


RULES: List[Rule] = [Rule(second=1, group="default"), Rule(minute=10, group="localhost"), Rule(group="internal")]
