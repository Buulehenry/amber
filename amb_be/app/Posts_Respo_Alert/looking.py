from flask import Blueprint, request, jsonify, current_app, send_from_directory
from werkzeug.utils import secure_filename
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import LookingPost, User, Comment
import os

# Define the blueprint for looking posts
looking_bp = Blueprint('looking', __name__)

# Helper function to save images
def save_image(image):
    filename = secure_filename(image.filename)
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    image.save(filepath)
    return filename

# Serve uploaded images
@looking_bp.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)

# Helper function to validate post data
def validate_post_data(data):
    errors = []
    if not data.get('description'):
        errors.append('Description is required.')
    if not data.get('location'):
        errors.append('Location is required.')
    if not data.get('contact_info'):
        errors.append('Contact information is required.')
    return errors

# Create a new Looking Post with image upload
@looking_bp.route('/looking', methods=['POST'])
@jwt_required()
def create_looking_post():
    try:
        data = request.form  # Use form data to handle image upload
        image = request.files.get('image')  # Handle image upload if present

        # Validate input data
        errors = validate_post_data(data)
        if errors:
            return jsonify({'errors': errors}), 400

        # Save the image if it exists
        image_filename = None
        if image:
            image_filename = save_image(image)

        # Get the current user from the JWT
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        if not user:
            return jsonify({'message': 'User not found'}), 404

        # Create the looking post
        new_post = LookingPost(
            description=data.get('description'),
            location=data.get('location'),
            contact_info=data.get('contact_info'),
            user_id=user.id,
            image=image_filename  # Store the image filename in the post
        )
        db.session.add(new_post)
        db.session.commit()

        return jsonify({'message': 'Looking post created successfully', 'image': image_filename}), 201
    except Exception as e:
        return jsonify({'message': f'An error occurred: {str(e)}'}), 500

# Get all Looking Posts
@looking_bp.route('/looking', methods=['GET'])
def get_all_looking_posts():
    try:
        posts = LookingPost.query.all()
        posts_data = [
            {
                'id': post.id,
                'description': post.description,
                'location': post.location,
                'contact_info': post.contact_info,
                'image': post.image,
                'date_posted': post.date_posted,
                'username': post.user.username
            }
            for post in posts
        ]
        return jsonify(posts_data), 200
    except Exception as e:
        return jsonify({'message': f'An error occurred: {str(e)}'}), 500

# Get a specific Looking Post by ID
@looking_bp.route('/looking/<int:post_id>', methods=['GET'])
def get_looking_post(post_id):
    try:
        post = LookingPost.query.get(post_id)

        if not post:
            return jsonify({'message': 'Post not found'}), 404

        post_data = {
            'id': post.id,
            'description': post.description,
            'location': post.location,
            'contact_info': post.contact_info,
            'image': post.image,
            'date_posted': post.date_posted,
            'username': post.user.username
        }
        return jsonify(post_data), 200
    except Exception as e:
        return jsonify({'message': f'An error occurred: {str(e)}'}), 500

# Search and filter Looking Posts by keyword and location
@looking_bp.route('/looking/search', methods=['GET'])
def search_looking_posts():
    try:
        # Get query parameters
        keyword = request.args.get('keyword', '').lower()
        location = request.args.get('location', '').lower()

        # Search for posts based on keyword and location
        query = LookingPost.query
        if keyword:
            query = query.filter(LookingPost.description.ilike(f'%{keyword}%'))
        if location:
            query = query.filter(LookingPost.location.ilike(f'%{location}%'))

        posts = query.all()
        posts_data = [
            {
                'id': post.id,
                'description': post.description,
                'location': post.location,
                'contact_info': post.contact_info,
                'image': post.image,
                'date_posted': post.date_posted,
                'username': post.user.username
            }
            for post in posts
        ]
        return jsonify(posts_data), 200
    except Exception as e:
        return jsonify({'message': f'An error occurred: {str(e)}'}), 500

# Update a Looking Post (only the creator can update)
@looking_bp.route('/looking/<int:post_id>', methods=['PUT'])
@jwt_required()
def update_looking_post(post_id):
    try:
        post = LookingPost.query.get(post_id)

        if not post:
            return jsonify({'message': 'Post not found'}), 404

        user_id = get_jwt_identity()
        if post.user_id != user_id:
            return jsonify({'message': 'Unauthorized to update this post'}), 403

        data = request.form  # Use form data to handle image upload
        image = request.files.get('image')  # Handle image upload if present

        # Validate input data
        errors = validate_post_data(data)
        if errors:
            return jsonify({'errors': errors}), 400

        # Update post details
        post.description = data.get('description', post.description)
        post.location = data.get('location', post.location)
        post.contact_info = data.get('contact_info', post.contact_info)

        # If a new image is uploaded, save it and update the image field
        if image:
            image_filename = save_image(image)
            post.image = image_filename

        db.session.commit()
        return jsonify({'message': 'Looking post updated successfully'}), 200
    except Exception as e:
        return jsonify({'message': f'An error occurred: {str(e)}'}), 500

# Delete a Looking Post (only the creator can delete)
@looking_bp.route('/looking/<int:post_id>', methods=['DELETE'])
@jwt_required()
def delete_looking_post(post_id):
    try:
        post = LookingPost.query.get(post_id)

        if not post:
            return jsonify({'message': 'Post not found'}), 404

        user_id = get_jwt_identity()
        if post.user_id != user_id:
            return jsonify({'message': 'Unauthorized to delete this post'}), 403

        db.session.delete(post)
        db.session.commit()
        return jsonify({'message': 'Looking post deleted successfully'}), 200
    except Exception as e:
        return jsonify({'message': f'An error occurred: {str(e)}'}), 500

# Add a comment to a Looking Post
@looking_bp.route('/looking/<int:post_id>/comment', methods=['POST'])
@jwt_required()
def add_comment(post_id):
    try:
        data = request.get_json()
        content = data.get('content')

        if not content:
            return jsonify({'message': 'Comment content is required'}), 400

        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        post = LookingPost.query.get(post_id)
        if not post:
            return jsonify({'message': 'Post not found'}), 404

        comment = Comment(content=content, user_id=user.id, post_id=post.id)
        db.session.add(comment)
        db.session.commit()

        return jsonify({'message': 'Comment added successfully'}), 201
    except Exception as e:
        return jsonify({'message': f'An error occurred: {str(e)}'}), 500

# Get comments for a Looking Post
@looking_bp.route('/looking/<int:post_id>/comments', methods=['GET'])
def get_comments(post_id):
    try:
        post = LookingPost.query.get(post_id)

        if not post:
            return jsonify({'message': 'Post not found'}), 404

        comments = Comment.query.filter_by(post_id=post_id).all()
        comments_data = [
            {
                'id': comment.id,
                'content': comment.content,
                'date_posted': comment.date_posted,
                'username': comment.user.username
            }
            for comment in comments
        ]

        return jsonify(comments_data), 200
    except Exception as e:
        return jsonify({'message': f'An error occurred: {str(e)}'}), 500
