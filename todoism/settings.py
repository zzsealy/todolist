import os


basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


class BaseConfig(object):
    TODOISM_LOCALES = ['zh_Hans_CN', 'en_US']  # 定义中文和英语语言支持
    TODOISM_ITEM_PER_PAGE = 20      # 每页显示数

    BABEL_DEFAULT_LOCALE = TODOISM_LOCALES[0]    # 默认设置是中文。
    SECRET_KEY = os.getenv('SECRET_KEY', 'sajfiojasiofhiahr')

    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///' + os.path.join(basedir, 'data.db'))
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DevelopmentConfig(BaseConfig):
    pass


class ProductionConfig(BaseConfig):
    pass


class TestingConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///'
    WTF_CSRF_ENABLED = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig
}