import os
import uuid

ENABLE_TRACKERS = bool(int(os.environ.get("MUSE_ENABLE_TRACKERS", 0)))
MUSE_LOAD_TESTING = os.environ.get("MUSE_LOAD_TESTING", False)
INFERENCE_REQUEST_TIMEOUT = os.environ.get("INFERENCE_REQUEST_TIMEOUT", 160)
KEEP_ALIVE_TIMEOUT = os.environ.get("KEEP_ALIVE_TIMEOUT", 160)
RATE_LIMIT_KEY = os.environ.get("RATE_LIMIT_KEY", str(uuid.uuid4().hex))
SENTRY_API_KEY = os.environ.get("SENTRY_API_KEY", None)
MUSE_SYSTEM_PASSWORD = os.environ.get("MUSE_SYSTEM_PASSWORD", "").encode("utf-8")
IMAGE_SIZE = 512

NSFW_PROMPTS = [
    "nudity",
    "porn",
    "sex",
    "hentai",
    "fetish pornography",
    "violence",
    "gore",
    "murder",
    "blood",
    "guns",
    "profanity",
    "racist",
    "homophobic",
    "sexist",
    "swastika",  # Nazi Symbol
    "penis",
    "anus",
    "buttocks",
    "breasts",
    "dildo",
    "genitals",
    "nipples",
    "vagina",
    "rectum",
]
