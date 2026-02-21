import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    database_url = os.environ.get('DATABASE_URL') or 'postgresql://galia_user:dev_password@localhost:5432/galia_db'
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_DATABASE_URI = database_url
    
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:5173,http://localhost:5174,http://localhost:5175').split(',')
    
    FUDO_API_BASE_URL = os.environ.get('FUDO_API_BASE_URL', 'https://integrations.fu.do/fudo/v1')
    FUDO_CLIENT_ID = os.environ.get('FUDO_CLIENT_ID')
    FUDO_CLIENT_SECRET = os.environ.get('FUDO_CLIENT_SECRET')
    FUDO_WEBHOOK_SECRET = os.environ.get('FUDO_WEBHOOK_SECRET')
    FUDO_SYNC_ENABLED = os.environ.get('FUDO_SYNC_ENABLED', 'False').lower() == 'true'

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = True

class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_SAMESITE = 'None'
    SQLALCHEMY_ECHO = False

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
