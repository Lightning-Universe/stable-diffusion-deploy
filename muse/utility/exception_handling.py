from fastapi import HTTPException


def raise_granular_exception(exception: Exception):
    """handle the exceptions coming from hitting the model servers."""
    if not isinstance(exception, Exception):
        return

    if isinstance(exception, HTTPException):
        raise exception

    if isinstance(exception, Exception):
        if exception.args[0] == "Server disconnected":
            raise HTTPException(500, "Model server disconnected")

    raise HTTPException(500, exception.args[0])
