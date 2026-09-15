from flask import Flask, jsonify, request
from uuid import uuid4

app = Flask(__name__)
STUDENTS = []

@app.route("/students", methods=["POST"])
def create_student():
    body = request.get_json(silent=True) or {}
    name = body.get("name")
    id = body.get("id", str(uuid4()))
    gpa = body.get("gpa", 0.0)
    if not name:
        return jsonify({"error": "name là bắt buộc"}), 400

    student = {
        "id": id,
        "name": name,
        "gpa": gpa
    }
    STUDENTS.append(student)
    return jsonify({"id": id, "name": name, "gpa": gpa}), 201