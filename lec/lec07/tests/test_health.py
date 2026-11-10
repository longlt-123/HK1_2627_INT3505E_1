import json
import logging
from unittest.mock import patch

from sqlalchemy.exc import OperationalError

from lec.lec07.extensions import db
from lec.lec07.logging_config import JsonFormatter


def test_health_and_readiness(client):
    assert client.get("/healthz").json == {"status": "ok"}
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json == {"status": "ok", "checks": {"db": "ok"}}


def test_database_failure_does_not_break_liveness(client):
    with patch.object(db.session, "execute", side_effect=OperationalError("SELECT 1", {}, Exception("offline"))):
        assert client.get("/healthz").status_code == 200
        response = client.get("/ready")
        assert response.status_code == 503
        assert response.json == {"status": "degraded", "checks": {"db": "err"}}


def test_logging_contains_status_and_latency(client):
    response = client.get("/healthz")
    assert len(response.headers["X-Request-Id"]) == 32
    record = logging.LogRecord("test", logging.INFO, "", 0, "request_completed", (), None)
    record.status = 200
    record.latency_ms = 1.5
    payload = json.loads(JsonFormatter().format(record))
    assert payload["status"] == 200
    assert payload["latency_ms"] == 1.5
