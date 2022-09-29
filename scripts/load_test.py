import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from rich.progress import track

# TODO: implement argparse

NUM_USERS = 10
SERVER = "https://gmpfx-01gdzqrj90xwpvvew1kw1bv2s5.litng-ai-03.litng.ai"
REQUEST_TIMEOUT = 160

data = {"dream": "A purple cloud with Lightning", "high_quality": False}
data = json.dumps(data)
headers = {
    "accept": "application/json",
    "x-api-key": os.environ.get("RATE_LIMIT_KEY", ""),
    # Already added when you pass json= but not when you pass data=
    "Content-Type": "application/json",
}

if __name__ == "__main__":
    print(f"Spawning {NUM_USERS} users")
    threads = []
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=NUM_USERS) as pool:
        for i in range(NUM_USERS):
            threads.append(
                pool.submit(requests.post, f"{SERVER}/api/predict", data=data, headers=headers, timeout=REQUEST_TIMEOUT)
            )

        failures = []
        for e in track(as_completed(threads), total=len(threads)):
            try:
                e.result().raise_for_status()
            except Exception as e:
                failures.append(e.args[0])

    t1 = time.time()
    print(f"time taken:{t1 - t0}")
    print(f"total failures: {len(failures)}")
    print(f"unique failures: {set(failures)}")
