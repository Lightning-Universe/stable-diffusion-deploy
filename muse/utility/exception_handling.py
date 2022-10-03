import asyncio

import aiohttp.client_exceptions
from fastapi import HTTPException

from muse.utility.utils import TimeoutException


def raise_granular_exception(exception: Exception):
    """handle the exceptions coming from hitting the model servers."""
    if not isinstance(exception, Exception):
        return

    if isinstance(exception, HTTPException):
        raise exception

    if isinstance(exception, aiohttp.client_exceptions.ServerDisconnectedError):
        raise HTTPException(500, "Worker server Disconnected")

    if isinstance(exception, aiohttp.client_exceptions.ClientError):
        raise HTTPException(500, "Worker Server error")

    if isinstance(exception, asyncio.TimeoutError):
        raise TimeoutException()

    if isinstance(exception, Exception):
        if exception.args[0] == "Server disconnected":
            raise HTTPException(500, "Worker server disconnected")

    raise HTTPException(500, exception.args[0])
