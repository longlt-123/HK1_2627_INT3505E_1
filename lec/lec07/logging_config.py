import json
import logging
import sys
import time
from uuid import uuid4

from flask import g, has_request_context, request


class JsonFormatter(logging.Formatter):
    converter = time.gmtime

    def format(self, record):
        data = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%SZ"),
            "level": record.levelname, "event": record.getMessage(),
        }
        if has_request_context():
            data["request_id"] = getattr(g, "request_id", "-")
        for name in ("status", "latency_ms", "method", "path"):
            if hasattr(record, name):
                data[name] = getattr(record, name)
        if record.exc_info:
            data["exception"] = self.formatException(record.exc_info)
        return json.dumps(data, ensure_ascii=False)


def configure_logging(app):
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    app.logger.handlers = [handler]
    app.logger.setLevel(app.config["LOG_LEVEL"])

    @app.before_request
    def start_request():
        g.started_at = time.perf_counter()
        g.request_id = uuid4().hex

    @app.after_request
    def finish_request(response):
        response.headers["X-Request-Id"] = g.request_id
        app.logger.info("request_completed", extra={
            "status": response.status_code,
            "latency_ms": round((time.perf_counter() - g.started_at) * 1000, 2),
            "method": request.method, "path": request.path,
        })
        return response
