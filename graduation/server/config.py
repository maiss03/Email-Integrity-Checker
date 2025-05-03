import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(basedir, 'instance', 'email_platform.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_TOKEN_LOCATION = ['headers']
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 5,
        'pool_timeout': 30,
        'pool_recycle': 1800,
        'max_overflow': 10
    }


    MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY")
    MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN")
    MAILGUN_BASE_URL = f"https://api.eu.mailgun.net/v3/{MAILGUN_DOMAIN}/messages"

    LDAP_SERVER = os.getenv("LDAP_SERVER")
    LDAP_PORT = int(os.getenv("LDAP_PORT", 636))
    LDAP_BASE_DN = os.getenv("LDAP_BASE_DN")
    LDAP_USER_DN = f"CN=Users,{LDAP_BASE_DN}"
    LDAP_ADMIN_USER = os.getenv("LDAP_ADMIN_USER")
    LDAP_ADMIN_PASSWORD = os.getenv("LDAP_ADMIN_PASSWORD")
    LDAP_ADMIN_CN = os.getenv("LDAP_ADMIN_CN")
