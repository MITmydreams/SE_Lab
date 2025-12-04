import os

class Config:
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://fxk1234:1234@localhost/emoji'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.urandom(24)

EMOJI_TYPE_MAP = {
    1: 'thinking',
    2: 'smile',
    3: 'relaxed',
    4: 'smile_with_heart_eyes',
    5: 'neutral',
    6: 'sad',
    7: 'confused',
    8: 'painful',
    9: 'speechless',
    10: 'angry'
}