from functools import wraps

from flask import g, current_app, request
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired

from todoism.apis.v1.errors import api_abort, invalid_token, token_missing
from todoism.models import User


def generate_token(user):
    expiration = 3600
    s = Serializer(current_app.config['SECRET_KEY'], expires_in=expiration)
    token = s.dumps({'id': user.id}).decode('ascii')
    return token, expiration


# 用来验证令牌是否有效
def validate_token(token):
    s = Serializer(current_app.config['SECRET_KEY'])
    try:
        data = s.loads(token)
    except (BadSignature, SignatureExpired):
        return False
    user = User.query.get(data['id'])  # 使用令牌中的id来查询对应的用户对象
    if user is None:
        return False
    g.current_user = user   # 将用户储存到g上  g是Flask提供的全局对象
    return True


# 由于flask的request只支持解析Basic和Digest类型的授权字段，所以我们需要自己解析Authorization首部字段来获取令牌值
def get_token():
    if 'Authorization' in request.headers:
        try:
            token_type, token = request.headers['Authorization'].split(None, 1)
        except ValueError:
            token_type = token = None
    else:
        token_type = token = None
    return token_type, token


# 实现登陆保护装饰器  用来验证令牌（模仿 flask-login)
def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token_type, token = get_token()
        if request.method != 'OPTIONS':
            if token_type is None or token_type.lower() !='bearer':
                return api_abort(400, '令牌类型必须是bearer')
            if token is None:
                return token_missing()
            if not validate_token(token):
                return invalid_token()
        return f(*args, **kwargs)
    return decorated
