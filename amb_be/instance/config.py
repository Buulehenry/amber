import os

SECRET_KEY = os.getenv('SECRET_KEY', 'your-production-secret-key')
SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///instance_amber.db')

# Optional: Additional API keys or secrets
# GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
# TWILIO_API_KEY = os.getenv('TWILIO_API_KEY')
