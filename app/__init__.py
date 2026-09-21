import os
import urllib.parse
from dotenv import load_dotenv
from flask_login import LoginManager

load_dotenv()

from werkzeug.middleware.proxy_fix import ProxyFix
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__, template_folder='templates', static_folder='static')
# Hỗ trợ reverse proxy trên Railway / Deploy để nhận diện đúng HTTPS và client IP
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

app.secret_key = os.getenv('SECRET_KEY', 'default_secret_key_food_ordering_2026')

use_local_db = os.getenv('USE_LOCAL_DB', 'false').lower() in ['true', '1']
database_url = os.getenv('DATABASE_URL') or os.getenv('MYSQL_URL')
if database_url and database_url.strip() and not use_local_db:
    database_url = database_url.strip()
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql+psycopg2://', 1)
    elif database_url.startswith('postgresql://'):
        database_url = database_url.replace('postgresql://', 'postgresql+psycopg2://', 1)
    elif database_url.startswith('mysql://'):
        database_url = database_url.replace('mysql://', 'mysql+pymysql://', 1)
    elif database_url.startswith('mysql2://'):
        database_url = database_url.replace('mysql2://', 'mysql+pymysql://', 1)
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
else:
    db_user = urllib.parse.quote_plus(os.getenv('DB_USER') or os.getenv('DB_USERNAME') or 'root')
    db_pass = urllib.parse.quote_plus(os.getenv('DB_PASSWORD', ''))
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '3306')
    db_name = os.getenv('DB_NAME', 'food_ordering_db')

    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"mysql+pymysql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}?charset=utf8mb4"
    )

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app=app)
login = LoginManager(app=app)
login.login_view = 'login_view'
login.login_message = 'Vui lòng đăng nhập để tiếp tục.'
login.login_message_category = 'warning'

from flask_sock import Sock

sock = Sock(app=app)



