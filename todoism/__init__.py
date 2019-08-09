import flask

import os

import click
from flask import Flask, render_template, jsonify
from flask_login import current_user

from todoism.apis.v1 import api_v1
from todoism.blueprints.auth import auth_bp
from todoism.blueprints.home import home_bp
from todoism.blueprints.todo import todo_bp
from todoism.extensions import db, login_manage, csrf, babel
from todoism.models import User, Item
from todoism.settings import config


def create_app(config_name=None):
    if config_name is None:
        config_name = os.getenv('FLASK_CONFIG', 'development')

    app = Flask('todoism')
    app.config.from_object(config[config_name])

    register_extensions(app)
    register_blueprints(app)
    register_commands(app)
    register_errors(app)
    register_template_context(app)
    return app


def register_extensions(app):
    db.init_app(app)
    login_manage.init_app(app)
    csrf.init_app(app)
    csrf.exempt(api_v1)  # csrf 设置了全局SCRF保护，但是api_v1不需要，因为api不进行cookie用户认证。
    babel.init_app(app)


def register_blueprints(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(todo_bp)
    app.register_blueprint(home_bp)
    app.register_blueprint(api_v1, url_prefix='/api/v1')  # url_prefix 为蓝本设置前缀。
    # app.register_blueprint(api_v1, url_prefix='/v1', subdomain='api') # 设置子域。


def register_template_context(app):  # 注册上下文
    @app.context_processor
    def make_template_context():
        if current_user.is_authenticated:  # 如果登陆
            active_items = Item.query.with_parent(current_user).filter_by(done=False).count()
        else:
            active_items = None
        return dict(active_items=active_items)

'''
@api_v1.route('/')
def index():
    return jsonify(message='hello world!')
'''


def register_errors(app):
    @app.errorhandler(400)
    def bad_request(e):
        return render_template('errors.html', code=400, info='Bad Request'), 400

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors.html', code=403, info='forbidden'), 403

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors.html', code=404, info='page not found'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors.html', code=500, info='Server Errors'), 500


def register_commands(app):
    @app.cli.command()
    @click.option('--drop', is_flag=True, help='Creat after drop')
    def initdb(drop):
        if drop:
            click.confirm('这个操作将要删除数据库， 你确定要继续吗？')
            db.drop_all()
            click.echo('删除了数据库！')
        db.create_all()
        click.echo('初始化数据库！')
