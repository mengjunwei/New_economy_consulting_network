from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from redis import StrictRedis
from flask_wtf.csrf import CSRFProtect
from flask_session import Session
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand


class Config(object):
    '''配置文件类'''
    SECRET_KEY = 'EjpNVSNQTyGi1VvWECj9TvC/+kq3oujee2kTfQUs8yCM6xX9Yjq52v54g+HVoknA'
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'mysql://root:mysql@127.0.0.1:3306/flask_necn_dev'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REDIS_HOST = '127.0.0.1'
    REDIS_PORT = 6379
    SESSION_TYPE = 'redis'
    SESSION_REDIS = StrictRedis(host=REDIS_HOST, port=REDIS_PORT)
    SESSION_USE_SIGNER = True
    PERMANENT_SESSION_LIFETIME = 3600 * 24


app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
redis_store = StrictRedis(host=Config.REDIS_HOST, port=Config.REDIS_PORT)
CSRFProtect(app)
Session(app)
manager = Manager(app)
Migrate(app, db)
manager.add_command('mysql', MigrateCommand)



@app.route('/')
def index():
    redis_store.set('name', 'it')
    name = redis_store.get('name')
    print(name)
    return 'in index'

if __name__ == '__main__':
    manager.run()