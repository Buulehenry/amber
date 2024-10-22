from app import create_app, db, socketio
from flask_migrate import Migrate
import os
import logging
from logging.handlers import RotatingFileHandler

# Initialize the Flask application using the factory function
app = create_app()

# Initialize Flask-Migrate for database migrations
migrate = Migrate(app, db)

# Set up logging for production
if not app.debug and not app.testing:
    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/amber.log', maxBytes=10240, backupCount=10)
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    file_handler.setFormatter(formatter)
    app.logger.addHandler(file_handler)
    app.logger.info('Amber startup')

# Run the app with Socket.IO support for real-time notifications
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
