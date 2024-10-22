from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import User, Post, Comment, Review, db
from sqlalchemy import func
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Define the Blueprint for admins
admins_bp = Blueprint('admins', __name__)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

# Helper function to check if the user is an admin
def is_admin(user_id):
    user = User.query.get(user_id)
    return user.is_admin if user else False

# Admin: View user analytics (number of users, posts, comments, etc.)
@admins_bp.route('/analytics', methods=['GET'])
@jwt_required()
def admin_analytics():
    current_user_id = get_jwt_identity()

    # Ensure only admins can access this route
    if not is_admin(current_user_id):
        return jsonify({'message': 'Admin access required'}), 403

    try:
        # Total numbers
        total_users = User.query.count()
        total_posts = Post.query.count()
        total_comments = Comment.query.count()

        # Users registered per day
        users_per_day = db.session.query(
            func.date(User.created_at).label('date'),
            func.count(User.id).label('total')
        ).group_by(func.date(User.created_at)).all()

        # Posts created per day
        posts_per_day = db.session.query(
            func.date(Post.date_posted).label('date'),
            func.count(Post.id).label('total')
        ).group_by(func.date(Post.date_posted)).all()

        # Comments created per day
        comments_per_day = db.session.query(
            func.date(Comment.date_posted).label('date'),
            func.count(Comment.id).label('total')
        ).group_by(func.date(Comment.date_posted)).all()

        # Detailed user actions: actions grouped by user and date
        user_activity = db.session.query(
            User.username,
            func.date(Post.date_posted).label('post_date'),
            func.date(Comment.date_posted).label('comment_date'),
            func.count(Post.id).label('total_posts'),
            func.count(Comment.id).label('total_comments')
        ).outerjoin(Post, Post.user_id == User.id).outerjoin(Comment, Comment.user_id == User.id)\
            .group_by(User.username, func.date(Post.date_posted), func.date(Comment.date_posted)).all()

        # Build the analytics response
        analytics = {
            'total_users': total_users,
            'total_posts': total_posts,
            'total_comments': total_comments,
            'users_per_day': [{'date': str(u.date), 'total': u.total} for u in users_per_day],
            'posts_per_day': [{'date': str(p.date), 'total': p.total} for p in posts_per_day],
            'comments_per_day': [{'date': str(c.date), 'total': c.total} for c in comments_per_day],
            'user_activity': [
                {
                    'username': ua.username,
                    'post_date': str(ua.post_date) if ua.post_date else None,
                    'comment_date': str(ua.comment_date) if ua.comment_date else None,
                    'total_posts': ua.total_posts,
                    'total_comments': ua.total_comments
                }
                for ua in user_activity
            ]
        }

        return jsonify(analytics), 200

    except Exception as e:
        return jsonify({'message': f'An error occurred: {str(e)}'}), 500

# Admin: Get all users
@admins_bp.route('/users', methods=['GET'])
@jwt_required()
def get_all_users():
    current_user_id = get_jwt_identity()

    # Ensure only admins can access this route
    if not is_admin(current_user_id):
        return jsonify({'message': 'Admin access required'}), 403

    try:
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

    except Exception as e:
        return jsonify({'message': f'An error occurred: {str(e)}'}), 500

# Admin: Create a new user
@limiter.limit("5 per minute")  # Limit to 5 requests per minute
@admins_bp.route('/users', methods=['POST'])
@jwt_required()
def create_user():
    current_user_id = get_jwt_identity()

    # Ensure only admins can access this route
    if not is_admin(current_user_id):
        return jsonify({'message': 'Admin access required'}), 403

    data = request.get_json()
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Email and password are required'}), 400

    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'Email already registered'}), 400

    hashed_password = generate_password_hash(data['password'])
    new_user = User(email=data['email'], username=data.get('username'), password_hash=hashed_password, is_admin=data.get('is_admin', False))
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User created successfully'}), 201

# Admin: Update a user
@admins_bp.route('/users/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    current_user_id = get_jwt_identity()

    # Ensure only admins can access this route
    if not is_admin(current_user_id):
        return jsonify({'message': 'Admin access required'}), 403

    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404

    data = request.get_json()
    user.username = data.get('username', user.username)
    user.email = data.get('email', user.email)
    user.is_admin = data.get('is_admin', user.is_admin)

    db.session.commit()

    return jsonify({'message': 'User updated successfully'}), 200

# Admin: Delete a user
@admins_bp.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    current_user_id = get_jwt_identity()

    # Ensure only admins can access this route
    if not is_admin(current_user_id):
        return jsonify({'message': 'Admin access required'}), 403

    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404

    db.session.delete(user)
    db.session.commit()

    return jsonify({'message': 'User deleted successfully'}), 200

# Admin: Get a specific user by ID
@admins_bp.route('/users/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    current_user_id = get_jwt_identity()

    # Ensure only admins can access this route
    if not is_admin(current_user_id):
        return jsonify({'message': 'Admin access required'}), 403

    user = User.query.get(user_id)
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

# Admin: View detailed activity logs for a specific user (e.g., posts, comments)
@admins_bp.route('/users/<int:user_id>/activity', methods=['GET'])
@jwt_required()
def get_user_activity(user_id):
    current_user_id = get_jwt_identity()

    # Ensure only admins can access this route
    if not is_admin(current_user_id):
        return jsonify({'message': 'Admin access required'}), 403

    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404

    posts = Post.query.filter_by(user_id=user.id).all()
    comments = Comment.query.filter_by(user_id=user.id).all()

    activity = {
        'posts': [{'id': post.id, 'description': post.description, 'date_posted': post.date_posted} for post in posts],
        'comments': [{'id': comment.id, 'content': comment.content, 'date_posted': comment.date_posted} for comment in comments]
    }

    return jsonify(activity), 200
