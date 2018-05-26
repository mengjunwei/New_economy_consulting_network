import logging
from redis import StrictRedis


class Config(object):
    '''配置文件类'''
    SECRET_KEY = 'EjpNVSNQTyGi1VvWECj9TvC/+kq3oujee2kTfQUs8yCM6xX9Yjq52v54g+HVoknA'
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = ''
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REDIS_HOST = '127.0.0.1'
    REDIS_PORT = 6379
    SESSION_TYPE = 'redis'
    SESSION_REDIS = StrictRedis(host=REDIS_HOST, port=REDIS_PORT)
    SESSION_USE_SIGNER = True
    PERMANENT_SESSION_LIFETIME = 3600 * 24


class DevelopmentConfig(Config):
    '''开发环境配置'''
    SQLALCHEMY_DATABASE_URI = 'mysql://root:mysql@127.0.0.1:3306/flask_necn_dev'
    LOG_LEVEL = logging.DEBUG


class ProductionConfig(Config):
    '''生产环境配置'''
    SQLALCHEMY_DATABASE_URI = 'mysql://root:mysql@127.0.0.1:3306/flask_necn_pro'
    DEBUG = False
    LOG_LEVEL = logging.ERROR


class UnittestConfig(Config):
    '''开发环境配置'''
    SQLALCHEMY_DATABASE_URI = 'mysql://root:mysql@127.0.0.1:3306/flask_necn_unit'
    LOG_LEVEL = logging.DEBUG


configs = {
    'dev': DevelopmentConfig,
    'pro': ProductionConfig,
    'unit': UnittestConfig
}