from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
import jwt
from time import time

db = SQLAlchemy()

# User Model
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    posts = db.relationship('Post', backref='user', lazy=True)
    comments = db.relationship('Comment', backref='user', lazy=True)
    written_reviews = db.relationship('Review', foreign_keys='Review.user_id', backref='reviewer', lazy=True)
    received_reviews = db.relationship('Review', foreign_keys='Review.reviewed_user_id', backref='reviewed_user', lazy=True)

    # Password hashing
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # Generate JWT access token
    def generate_jwt(self, expires_in=3600):
        return create_access_token(identity=self.id, expires_delta=timedelta(seconds=expires_in))

    # Generate password reset token
    def get_reset_token(self, expires_in=600):
        return jwt.encode({'reset_password': self.id, 'exp': time() + expires_in}, 
                          current_app.config['SECRET_KEY'], algorithm='HS256')

    @staticmethod
    def verify_reset_token(token):
        try:
            user_id = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])['reset_password']
        except:
            return None
        return User.query.get(user_id)

    def __repr__(self):
        return f'<User {self.username}>'

# Base Post Model (Polymorphic)
class Post(db.Model):
    __tablename__ = 'posts'

    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(255), nullable=False)
    location = db.Column(db.String(255), nullable=False)
    contact_info = db.Column(db.String(255), nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    post_type = db.Column(db.String(50))  # For polymorphic identity
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    image = db.Column(db.String(255), nullable=True)  # To store image filename

    __mapper_args__ = {
        'polymorphic_identity': 'post',
        'polymorphic_on': post_type
    }

    comments = db.relationship('Comment', backref='post', lazy=True)

    def __repr__(self):
        return f'<Post {self.id}, Type: {self.post_type}>'

# Found Post Model (inherits from Post)
class FoundPost(Post):
    id = db.Column(db.Integer, db.ForeignKey('posts.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'found'
    }

# Lost Post Model (inherits from Post)
class LostPost(Post):
    id = db.Column(db.Integer, db.ForeignKey('posts.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'lost'
    }

# Looking Post Model (inherits from Post)
class LookingPost(Post):
    id = db.Column(db.Integer, db.ForeignKey('posts.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'looking'
    }

# Stolen Post Model (inherits from Post)
class StolenPost(Post):
    id = db.Column(db.Integer, db.ForeignKey('posts.id'), primary_key=True)
    vehicle_details = db.Column(db.String(255), nullable=True)  # Additional field for vehicle info

    __mapper_args__ = {
        'polymorphic_identity': 'stolen'
    }

# Comment Model
class Comment(db.Model):
    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(255), nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)

    def __repr__(self):
        return f'<Comment {self.id} on Post {self.post_id}>'

# Review Model (for rating/reviewing users)
class Review(db.Model):
    __tablename__ = 'reviews'

    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer, nullable=False)  # Rating between 1 and 5
    review = db.Column(db.String(255), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Reviewer
    reviewed_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # The person being reviewed

    reviewer = db.relationship('User', foreign_keys=[user_id], backref='written_reviews')
    reviewed_user = db.relationship('User', foreign_keys=[reviewed_user_id], backref='received_reviews')

    def __repr__(self):
        return f'<Review {self.id} - Rating: {self.rating}>'
