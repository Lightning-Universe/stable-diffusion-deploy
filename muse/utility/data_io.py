import json
import os
import queue
import random
import sys
from typing import Any, List, Optional

import numpy as np
from fastapi import HTTPException
from lightning_app.storage.drive import Drive
from pydantic import BaseModel

OPEN_PROMPTS = None


def exit_threads(executor):
    print("\nWrapping up, please wait...")

    py_version = sys.version_info
    if (py_version.major == 3) and (py_version.minor < 9):
        # py versions less than 3.9
        # Executor#shutdown does not accept
        # cancel_futures keyword
        # manually shutdown
        # code taken from https://github.com/python/cpython/blob/3.9/Lib/concurrent/futures/thread.py#L210

        # prevent new tasks from being submitted
        executor.shutdown(wait=False)
        while True:
            # cancel all waiting tasks
            try:
                work_item = executor._work_queue.get_nowait()

            except queue.Empty:
                break

            if work_item is not None:
                work_item.future.cancel()

    else:
        executor.shutdown(cancel_futures=True)

    sys.exit(0)


def load_secret_from_env_or_drive(name: str, drive: Drive) -> Optional[str]:
    def get_secret_from_drive():
        try:
            drive.get(name)
            with open(name) as f:
                return f.read()
        except BaseException as e:
            print(e)
            return None

    return os.environ.get(name) or get_secret_from_drive()


def save_secret_to_drive(name: str, value: str, drive: Drive) -> None:
    with open(name, "w") as f:
        f.write(value)
    return drive.put(name)


def get_item(name: str, drive: Drive) -> Optional[Any]:
    try:
        drive.get(name)
        with open(name) as f:
            return json.loads(f.read())
    except BaseException as e:
        print(e)
        return None


def save_item(name: str, value: Any, drive: Drive) -> None:
    with open(name, "w") as f:
        f.write(json.dumps(value))
    return drive.put(name)


class TimeoutException(HTTPException):
    def __init__(self, status_code=408, detail="Request timed out.", *args, **kwargs):
        super().__init__(status_code=status_code, detail=detail, *args, **kwargs)


class LimitBacklogException(HTTPException):
    def __init__(self, status_code=408, detail="Model Server has too much backlog.", *args, **kwargs):
        super().__init__(status_code=status_code, detail=detail, *args, **kwargs)


class Data(BaseModel):
    prompt: str
    high_quality: bool = False


class DataBatch(BaseModel):
    batch: List[Data]


class SysInfo(BaseModel):
    num_workers: int
    servers: List[str]
    num_requests: int
    process_time: int
    global_request_count: int


def random_prompt() -> str:
    global OPEN_PROMPTS
    if OPEN_PROMPTS is None:
        OPEN_PROMPTS = np.loadtxt(
            "https://pl-public-data.s3.amazonaws.com/dream_stable_diffusion/1k-prompts.csv",
            usecols=0,
            skiprows=1,
            delimiter=",",
            dtype=str,
            converters=_remove_initial_quotes,
            encoding="utf-8",
        )
    return random.choice(OPEN_PROMPTS)


def _remove_initial_quotes(prompt):
    if prompt.startswith('"'):
        return prompt[1:]
    return prompt
