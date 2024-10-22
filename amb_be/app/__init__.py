import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail
from flask_socketio import SocketIO
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate
from config import Config

# Initialize extensions
db = SQLAlchemy()
jwt = JWTManager()
csrf = CSRFProtect()
mail = Mail()
socketio = SocketIO()
limiter = Limiter(key_func=get_remote_address)
migrate = Migrate()

def create_app(config_class=Config):
    # Initialize Flask app
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions with the app
    db.init_app(app)
    jwt.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)
    socketio.init_app(app)
    limiter.init_app(app)
    migrate.init_app(app, db)

    # Import and register blueprints
    from app.users import users_bp
    from app.posts_respo_alert import found_bp, lost_bp, looking_bp, stolen_bp
    from app.admins import admins_bp

    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(found_bp, url_prefix='/api')
    app.register_blueprint(lost_bp, url_prefix='/api')
    app.register_blueprint(looking_bp, url_prefix='/api')
    app.register_blueprint(stolen_bp, url_prefix='/api')
    app.register_blueprint(admins_bp, url_prefix='/api/admin')

    # Enforce HTTPS in production
    if not app.debug and not app.testing:
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

        @app.before_request
        def enforce_https():
            if not request.is_secure:
                return redirect(request.url.replace("http://", "https://"))

    # Set up logging for production
    if not app.debug and not app.testing:
        import logging
        from logging.handlers import RotatingFileHandler
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/amber.log', maxBytes=10240, backupCount=10)
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.info('Amber startup')

    return app


