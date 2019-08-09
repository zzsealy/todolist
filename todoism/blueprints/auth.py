from faker import Faker
from flask import render_template, redirect, url_for, Blueprint,request,  jsonify
from flask_login import login_user, logout_user, login_required, current_user

from todoism.extensions import db
from todoism.models import User, Item

auth_bp = Blueprint('auth', __name__)
fake = Faker()


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('todo.app'))    # 如果已经登陆

    if request.method == 'POST':
        data = request.get_json()  # 获得的数据转换成json
        username = data['username']
        password = data['password']

        user = User.query.filter_by(username=username).first()
        if user is not None and user.validate_password(password):
            login_user(user)
            return jsonify(massage='登陆成功！')
        return jsonify(message = '无效的账号和密码！')
    return render_template('_login.html')   # 返回的事局部模版


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return jsonify(message="退出登录！")


@auth_bp.route('/register')
def register():   # 注册页面
    # 生成一个一个随机账户作为测试用户
    username = fake.user_name()
    # 确定生成的虚拟用户不在数据库表中
    while User.query.filter_by(username=username).first() is not None:
        username = fake.user_name()
    password = fake.word()
    user = User(username=username)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    item = Item(body='明天晚上吃烤肉！', author=user)
    item2 = Item(body='帮助一个不认识的人！', author=user)
    item3 = Item(body='今天晚上跑五公里！', author=user)
    item4 = Item(body='明天下午打篮球！', done=True, author=user)
    db.session.add_all([item, item2, item3, item4])
    db.session.commit()
    # 使用jsonify函数返回json格式的数据。

    return jsonify(username=username, password=password, message='生成成功！')
