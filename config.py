import os
from datetime import timedelta
import secrets  # Add this for better secret key generation

class Config:
    # Generate a secure secret key
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    
    # SQL Server Connection String for SQLEXPRESS (named instance)
   # Naya Code (Isse replace karein
   # Naya Code (Isse replace karein):
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
    'mssql+pyodbc://./SQLEXPRESS/WoplaDB?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 300,
        'pool_pre_ping': True,
    }
    
    # Session settings
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    
    # App settings
    APP_NAME = "Wopla Admin Dashboard"
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload
    
    # Email settings
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # Default admin credentials
    SUPER_ADMIN_EMAIL = 'admin@wopla.com'
    SUPER_ADMIN_PASSWORD = 'Admin@123'