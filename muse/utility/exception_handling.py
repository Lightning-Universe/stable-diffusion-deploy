import asyncio
from typing import List

from fastapi import HTTPException

from muse.utility.utils import TimeoutException


def supress_http_errors(response, data: List):
    """Update the client response to an Exception class if there are any errors without raising it."""
    n = len(data)
    if response.status == 408:
        return [TimeoutException()] * n
    try:
        response.raise_for_status()
    except Exception as e:
        return [e] * n
    return response


def raise_granular_exception(exception: Exception):
    """handle the exceptions coming from hitting the model servers."""
    if not isinstance(exception, Exception):
        return

    if isinstance(exception, HTTPException):
        raise exception

    if isinstance(exception, asyncio.TimeoutError):
        raise TimeoutException()

    if isinstance(exception, Exception):
        if exception.args[0] == "Server disconnected":
            raise HTTPException(500, "Model server disconnected")

    raise HTTPException(500, exception.args[0])
