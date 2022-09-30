import os
import uuid

LOAD_TESTING = os.environ.get("MUSE_LOAD_TESTING", False)
INFERENCE_REQUEST_TIMEOUT = os.environ.get("INFERENCE_REQUEST_TIMEOUT", 160)
KEEP_ALIVE_TIMEOUT = os.environ.get("KEEP_ALIVE_TIMEOUT", 160)
RATE_LIMIT_KEY = os.environ.get("RATE_LIMIT_KEY", str(uuid.uuid4().hex))
SENTRY_API_KEY = os.environ.get("SENTRY_API_KEY", None)
IMAGE_SIZE = 512
