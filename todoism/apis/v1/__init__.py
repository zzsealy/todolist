from flask import Blueprint

api_v1 = Blueprint('api_v1', __name__)

# 为了避免产生倒入循环依赖，在这里导入resources,为了让蓝本和对应的视图关联起来。
from todoism.apis.v1 import resources