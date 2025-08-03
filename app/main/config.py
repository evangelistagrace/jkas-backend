"""Config settings for for development, testing and production environments."""
import os
import sqlalchemy
from pathlib import Path
import urllib
import setting
# import pyodbc

SQL_SERVER = os.environ.get('SQL_SERVER')
SQL_PORT = os.environ.get('SQL_PORT')
SQL_DATABASE = os.environ.get('SQL_DATABASE')
SQL_UID = os.environ.get('SQL_UID')
SQL_PASSWORD = os.environ.get('SQL_PASSWORD')
MYSQL_HOST = os.environ.get('MYSQL_HOST')
MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE')

# params = urllib.parse.quote_plus("DRIVER={SQL Server};SERVER="+SQL_SERVER+";DATABASE="+SQL_DATABASE+";UID="+SQL_UID+";PWD="+SQL_PASSWORD+";")
# engine = create_engine("mssql+pyodbc:///?odbc_connect=%s" % params)

# SQLITE_DEV = 'mssql+pyodbc://'+SQL_UID+':'+SQL_PASSWORD+'@'+SQL_SERVER+':'+SQL_PORT+'/'+SQL_DATABASE+'?driver=SQL+Server'
# SQLITE_DEV = 'mssql+pymssql://'+SQL_UID+':'+SQL_PASSWORD+'@'+SQL_SERVER+':'+SQL_PORT+'/'+SQL_DATABASE+'?charset=utf8'
# ODBC Driver 17 for SQL Server
params = urllib.parse.quote_plus(
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=" + SQL_SERVER + ";"
    "DATABASE=" + SQL_DATABASE + ";"
    "UID=" + SQL_UID + ";"
    "PWD=" + SQL_PASSWORD + ";"
    "Connection Timeout=30;"
    "Command Timeout=60;"
    "Mars_Connection=yes;"
)

SQLITE_DEV = "mssql+pyodbc:///?odbc_connect=%s" % params
SQLITE_PROD = "mssql+pyodbc:///?odbc_connect=%s" % params
SQLITE_TEST = "mssql+pyodbc:///?odbc_connect=%s" % params

# SQLITE_DEV = 'mysql://root@'+MYSQL_HOST+'/'+MYSQL_DATABASE
# SQLITE_TEST = 'mysql://root@'+MYSQL_HOST+'/'+MYSQL_DATABASE
# SQLITE_PROD = 'mysql://root@'+MYSQL_HOST+'/'+MYSQL_DATABASE

class Config:
    """Base configuration."""

    SECRET_KEY = os.environ.get("SECRET_KEY","open sessame")
    BCRYPT_LOG_ROUNDS = 4
    TOKEN_EXPIRE_HOURS = 456
    TOKEN_EXPIRE_MINUTES = 1440
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PRESERVE_CONTEXT_ON_EXCEPTION = False
    SWAGGER_UI_DOC_EXPANSION = "list"
    RESTX_MASK_SWAGGER = False
    JSON_SORT_KEYS = False

class TestingConfig(Config):
    """Testing configuration."""

    TESTING = True
    engine = sqlalchemy.create_engine(SQLITE_TEST)
    SQLALCHEMY_DATABASE_URI = SQLITE_TEST

class DevelopmentConfig(Config):
    """Development configuration."""

    TOKEN_EXPIRE_HOURS = 456
    TOKEN_EXPIRE_MINUTES = 1440
    engine = sqlalchemy.create_engine(SQLITE_DEV)
    SQLALCHEMY_DATABASE_URI = SQLITE_DEV
    PRESERVE_CONTEXT_ON_EXCEPTION = True
    
class ProductionConfig(Config):
    """Production configuration."""

    TOKEN_EXPIRE_HOURS = 456
    TOKEN_EXPIRE_MINUTES = 1440
    BCRYPT_LOG_ROUNDS = 13
    engine = sqlalchemy.create_engine(SQLITE_PROD)
    SQLALCHEMY_DATABASE_URI = SQLITE_PROD
    PRESERVE_CONTEXT_ON_EXCEPTION = True

ENV_CONFIG_DICT = dict(
    development=DevelopmentConfig, testing=TestingConfig, production=ProductionConfig
)

def get_config(config_name):
    """Retrieve environment configuration settings."""
    return ENV_CONFIG_DICT.get(config_name, DevelopmentConfig)