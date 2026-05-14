"""Structured JSON logger setup for the SF Case Intent Processor."""

import json
import logging
import sys
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Add optional case-level fields if present
        if hasattr(record, "case_id"):
            log_obj["case_id"] = record.case_id
        if hasattr(record, "cid"):
            log_obj["cid"] = record.cid
        if hasattr(record, "intent_name"):
            log_obj["intent_name"] = record.intent_name
        return json.dumps(log_obj, ensure_ascii=False)


def setup_logger(name: str = "sf_case_processor", level: str = "INFO") -> logging.Logger:
    """Configure and return a logger with JSON formatting."""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Avoid duplicate handlers on repeated calls
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)

    return logger
