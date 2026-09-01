# -*- coding: utf-8 -*-
import datetime
import json
import logging
import sys

logger = logging.getLogger("damga_ops")
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)

def log_event(event: str, level: str = "INFO", **kwargs):
    payload = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "level": level.upper(),
        "event": event,
        **kwargs
    }
    msg = json.dumps(payload, ensure_ascii=False)
    if level.upper() == "ERROR":
        logger.error(msg)
    elif level.upper() == "WARNING":
        logger.warning(msg)
    else:
        logger.info(msg)
