from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from flask_mail import Message
from app import db, mail
from app.models import User
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import jwt
from datetime import datetime, timedelta
import os

# Define the Blueprint for users
users_bp = Blueprint('users', __name__)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

# Helper function to send email
def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request',
                  sender=os.getenv('MAIL_DEFAULT_SENDER'),
                  recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
{request.url_root}reset_password/{token}
If you did not make this request, simply ignore this email and no changes will be made.
'''
    mail.send(msg)

# Register a new user
@limiter.limit("5 per minute")  # Limit to 5 requests per minute
@users_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Email and password are required'}), 400

    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'Email already registered'}), 400

    # Hash the password and create the user
    hashed_password = generate_password_hash(data['password'])
    new_user = User(email=data['email'], username=data.get('username'), password_hash=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User registered successfully'}), 201

# User login and JWT generation
@limiter.limit("5 per minute")  # Limit to 5 requests per minute
@users_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Email and password are required'}), 400

    user = User.query.filter_by(email=data['email']).first()

    if user and check_password_hash(user.password_hash, data['password']):
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
        return jsonify({
            'access_token': access_token,
            'refresh_token': refresh_token,
            'message': 'Login successful'
        }), 200
    else:
        return jsonify({'message': 'Invalid credentials'}), 401

# Refresh JWT token
@users_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh_token():
    current_user = get_jwt_identity()
    new_access_token = create_access_token(identity=current_user)
    return jsonify({'access_token': new_access_token}), 200

# Get the current user's details
@users_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user:
        return jsonify({'message': 'User not found'}), 404

    user_data = {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'is_admin': user.is_admin,
        'created_at': user.created_at
    }

    return jsonify(user_data), 200

# Request password reset
@limiter.limit("3 per hour")  # Limit to 3 password reset requests per hour
@users_bp.route('/reset_password', methods=['POST'])
def request_password_reset():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()

    if user:
        send_reset_email(user)
    return jsonify({'message': 'If your email exists, you will receive a password reset email shortly.'}), 200

# Reset password
@users_bp.route('/reset_password/<token>', methods=['POST'])
def reset_password(token):
    user = User.verify_reset_token(token)
    if not user:
        return jsonify({'message': 'Invalid or expired token'}), 400

    data = request.get_json()
    if not data or not data.get('password'):
        return jsonify({'message': 'Password is required'}), 400

    user.password_hash = generate_password_hash(data['password'])
    db.session.commit()

    return jsonify({'message': 'Password has been updated'}), 200

# Admin: Get all users (Admin only)
@users_bp.route('/users', methods=['GET'])
@jwt_required()
def get_all_users():
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    if not current_user or not current_user.is_admin:
        return jsonify({'message': 'Admin access required'}), 403

    users = User.query.all()
    users_data = [
        {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_admin': user.is_admin,
            'created_at': user.created_at
        }
        for user in users
    ]
    return jsonify(users_data), 200

# Admin: Delete a user (Admin only)
@users_bp.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    if not current_user or not current_user.is_admin:
        return jsonify({'message': 'Admin access required'}), 403

    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404

    db.session.delete(user)
    db.session.commit()

    return jsonify({'message': 'User deleted successfully'}), 200
