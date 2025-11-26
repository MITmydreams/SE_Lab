import os

class Config:
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://fxk1234:1234@localhost/emoji'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.urandom(24)
# 将 user,password,database 替换为你的数据库用户名，密码，数据库名