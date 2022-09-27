import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from rich.progress import track

NUM_USERS = 400
SERVER = "https://gmpfx-01gdzqrj90xwpvvew1kw1bv2s5.litng-ai-03.litng.ai"
REQUEST_TIMEOUT = 200

data = {"dream": "A purple cloud with Lightning", "high_quality": False}
data = json.dumps(data)

if __name__ == "__main__":
    threads = []
    with ThreadPoolExecutor(max_workers=100) as pool:
        for i in range(NUM_USERS):
            threads.append(pool.submit(requests.post, f"{SERVER}/api/predict", data=data, timeout=REQUEST_TIMEOUT))

        failures = []
        t0 = time.time()
        for e in track(as_completed(threads)):
            try:
                e.result().raise_for_status()
            except Exception as e:
                failures.append(e.args[0])

    t1 = time.time()
    print(f"time taken:{t1 - t0}")
    print(f"total failures: {len(failures)}")
    print(f"unique failures: {set(failures)}")
