from flask import request, current_app
from flask_babel import Babel, lazy_gettext as _l
from flask_login import LoginManager, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
csrf = CSRFProtect()
babel = Babel()

login_manage = LoginManager()
login_manage.login_view = 'auth.login'
login_manage.login_message = _l('请通过这个页面登陆！')


@login_manage.user_loader
def load_user(user_id):
    from todoism.models import User
    return User.query.get(int(user_id))


# 设置区域选择函数
@babel.localeselector
def get_locale():
    if current_user.is_authenticated and current_user.locale is not None:
        return current_user.locale

    locale = request.cookies.get('locale')
    if locale is not None:
        return locale
    # 如果最后也没有获得locale， 从客户端里面的语言偏好来获得。 需要传入TODOISM_LOCALES列表，
    # 与客户端语言偏好逐个匹配，返回最先匹配的结果。
    return request.accept_languages.best_match(current_app.config['TODOISM_LOCALES'])



