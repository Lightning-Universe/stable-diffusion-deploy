import asyncio
import logging

import aiohttp.client_exceptions
from fastapi import HTTPException

from muse.utility.data_io import TimeoutException


def raise_granular_exception(exception: Exception):
    """Handle the exceptions coming from hitting the model servers."""
    if not isinstance(exception, Exception):
        return

    if isinstance(exception, HTTPException):
        raise exception

    if isinstance(exception, aiohttp.client_exceptions.ServerDisconnectedError):
        raise HTTPException(500, "Worker Server Disconnected")

    if isinstance(exception, aiohttp.client_exceptions.ClientError):
        logging.exception(exception)
        raise HTTPException(500, "Worker Server error")

    if isinstance(exception, asyncio.TimeoutError):
        raise TimeoutException()

    if isinstance(exception, Exception):
        if exception.args[0] == "Server disconnected":
            raise HTTPException(500, "Worker Server disconnected")

    logging.exception(exception)
    raise HTTPException(500, exception.args[0])
