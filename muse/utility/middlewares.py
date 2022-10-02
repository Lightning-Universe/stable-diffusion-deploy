import time

from fastapi.requests import Request
from sqlmodel import Session

from muse.db.backend import engine
from muse.db.models import RequestMonitor


async def request_monitor_middleware(app, request: Request, call_next):
    if not request.scope["path"] == "/api/predict":
        return await call_next(request)

    with Session(engine) as session:
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        app.last_process_time = process_time
        print(response.headers)
        worker_process_time = float(response.headers["X-Process-Time"])
        load_balancer_process_time = process_time

        prompt = await request.json()["dream"]
        request_monitor = RequestMonitor(
            prompt=prompt,
            model_server_process_time=worker_process_time,
            load_balancer_process_time=load_balancer_process_time,
        )
        session.add(request_monitor)
        session.commit()

    return await response
