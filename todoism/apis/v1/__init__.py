from flask import Blueprint
from flask_cors import CORS

api_v1 = Blueprint('api_v1', __name__)

# 默认情况下，Flask-CORS会为蓝本下所有路由添加跨域请求支持，并且允许来自任意源的请求。
CORS(api_v1)


# 为了避免产生倒入循环依赖，在这里导入resources,为了让蓝本和对应的视图关联起来。
from todoism.apis.v1 import resources


