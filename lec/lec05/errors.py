from flask import jsonify
from werkzeug.exceptions import HTTPException
from sqlalchemy.exc import IntegrityError
from models import db


class APIError(Exception):
    def __init__(self, code, message, status=400):
        self.code, self.message, self.status = code, message, status


def register_errors(app):
    @app.errorhandler(APIError)
    def api_error(error):
        return jsonify(error={"code": error.code, "message": error.message}), error.status

    @app.errorhandler(HTTPException)
    def http_error(error):
        return jsonify(error={"code": error.name.lower().replace(" ", "_"),
                              "message": error.description}), error.code

    @app.errorhandler(IntegrityError)
    def integrity_error(error):
        db.session.rollback()
        return jsonify(error={"code": "conflict", "message": "Dữ liệu trùng hoặc vi phạm ràng buộc database."}), 409
