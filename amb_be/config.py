import os
from datetime import timedelta

class Config:
    # General Flask Settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret-key')  # Always use a secure, random secret key
    DEBUG = False
    TESTING = False

    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///amber.db')  # Default to SQLite, or use DATABASE_URL from environment
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT Configuration
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-jwt-secret-key')  # Secret key for JWT
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)  # Access tokens expire in 1 hour
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)  # Refresh tokens expire in 7 days

    # Flask-WTF CSRF Protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SECRET_KEY = os.getenv('CSRF_SECRET_KEY', 'your-csrf-secret-key')  # Secret key for CSRF protection

    # Email Settings (Flask-Mail)
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.googlemail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', 'your-email@gmail.com')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', 'your-email-password')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@amber.com')

    # Flask-Limiter Configuration (Rate Limiting)
    RATELIMIT_HEADERS_ENABLED = True  # Show rate limit headers in responses

    # File Upload Configuration
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file upload size
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')  # Default folder for uploaded files

    # Logging Configuration
    LOG_TO_STDOUT = os.getenv('LOG_TO_STDOUT')  # Log to stdout for Heroku or Docker environments

    # Socket.IO Configuration (Real-time notifications)
    SOCKETIO_MESSAGE_QUEUE = os.getenv('SOCKETIO_MESSAGE_QUEUE', None)  # Use a message queue (e.g., Redis) for scalability

    # Flask Session Configuration (optional)
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False

    # Additional Configurations (if necessary)...


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv('DEV_DATABASE_URL', 'sqlite:///amber-dev.db')  # Development database


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.getenv('TEST_DATABASE_URL', 'sqlite:///amber-test.db')
    WTF_CSRF_ENABLED = False  # Disable CSRF for testing purposes
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=5)  # Shorter expiry for testing


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')  # In production, ensure DATABASE_URL is set
    LOG_TO_STDOUT = True  # Log to stdout in production (e.g., for Heroku)


# A dictionary to easily select configurations
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': Config
}
