from flask import jsonify
from marshmallow import ValidationError
from werkzeug.exceptions import HTTPException

from .extensions import db


class ApiError(Exception):
    def __init__(self, error, detail, status=400):
        super().__init__(detail)
        self.error = error
        self.detail = detail
        self.status = status


def register_error_handlers(app):
    @app.errorhandler(ApiError)
    def api_error(error):
        db.session.rollback()
        return jsonify(error=error.error, detail=error.detail), error.status

    @app.errorhandler(ValidationError)
    def validation_error(error):
        db.session.rollback()
        return jsonify(error="validation_error", detail=error.messages), 422

    @app.errorhandler(HTTPException)
    def http_error(error):
        db.session.rollback()
        response = error.get_response()
        response.data = app.json.dumps({
            "error": error.name.lower().replace(" ", "_"),
            "detail": error.description,
        })
        response.content_type = "application/json"
        return response

    @app.errorhandler(Exception)
    def unhandled_error(error):
        db.session.rollback()
        app.logger.exception("unhandled_error")
        return jsonify(error="internal_error", detail="An unexpected error occurred."), 500
