from flask import Blueprint, jsonify
from .user_data import get_user

bp = Blueprint('v2', __name__)

@bp.route('/users/<int:user_id>', methods=['GET'])
def get_user_endpoint(user_id):
    user = get_user(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify({
        'id': user_id,
        'first_name': user['first_name'],
        'last_name': user['last_name'],
        'email': user['email']
    })
