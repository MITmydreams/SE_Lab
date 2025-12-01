from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config
import os

# 获取项目根目录的绝对路径
base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
static_folder = os.path.join(base_dir, 'static')
app = Flask(__name__, static_folder=static_folder)
app.config.from_object(Config)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

from app import routes, models
