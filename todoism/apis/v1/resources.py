from flask import jsonify, request, current_app, url_for, g
from flask.views import MethodView

from todoism.apis.v1 import api_v1
from todoism.apis.v1.auth import auth_required, generate_token
from todoism.apis.v1.errors import api_abort, ValidationError
from todoism.apis.v1.schemas import user_schema, item_schema, items_schema
from todoism.extensions import db
from todoism.models import User, Item


def get_item_body():
    data = request.get_json()
    body = data.get('body')
    if body is None or str(body).strip() == '':
        # 如果数据不存在要返回400响应，但因为这个函数是由视图方法调用的，所以不能直接使用api_abort
        # 只能通过抛出异常的方法处理，在脚本中定义了错误类，使用Flask提供的errorhandler装饰器，加载api_abort函数
        raise ValidationError('事项是空的或者是无效值。')
    return body


class IndexAPI(MethodView):

    def get(self):
        return jsonify({
            "api_version": "1.0",
            "api_base_url": "http://example.com/api/v1",
            "current_user_url": "http://example.com/api/v1/user",
            "authentication_url": "http://example.com/api/v1/token",
            "item_url": "http://example.com/api/v1/items/{item_id }",
            "current_user_items_url": "http://example.com/api/v1/user/items{?page,per_page}",
            "current_user_active_items_url": "http://example.com/api/v1/user/items/active{?page,per_page}",
            "current_user_completed_items_url": "http://example.com/api/v1/user/items/completed{?page,per_page}",
        })


class AuthTokenAPI(MethodView):

    def post(self):
        """必须实现下面三个值，还有一个是scope，代表允许的权限范围，由api提供方自己定义。"""
        grant_type = request.form.get('grant_type')
        username = request.form.get('username')
        password = request.form.get('password')

        if grant_type is None or grant_type.lower() != 'password':
            return api_abort(code=400, message='授权类型必须是密码。')

        user = User.query.filter_by(username=username).first()
        if user is None or not user.validate_password(password):
            return api_abort(code=400, message='无效的账户密码')

        token, expiration = generate_token(user)

        response = jsonify({
            'access_token': token,  # access_token 令牌
            'token_type': 'Bearer', # 认证类型
            'expires_in': expiration # 过期时间
        })
        response.headers['Cache-Control'] = 'no-store'
        response.headers['Pragma'] = 'no-cache'
        return response


# 每个事项条目的所有api
class ItemAPI(MethodView):
    # decorators 由MethodView提供， 使用这个值可以为整个资源类的所有视图方法附加装饰器
    decorators = [auth_required]

    def get(self, item_id):
        '''获取条目'''
        item = Item.query.get_or_404(item_id)
        if g.current_user != item.author:
            return api_abort(403)
        return jsonify(item_schema(item))

    def put(self, item_id):
        """编辑条目"""
        item = Item.query.get_or_404(item_id)
        if g.current_user != item.author:
            return api_abort(403)
        item.body = get_item_body()
        db.session.commit()
        # 也可以返回创建修改资源后的新的资源，或者一个message，这里只返回了空白204。
        return '', 204

    def patch(self, item_id):
        """修改条目完成状态"""
        item = Item.query.get_or_404(item_id)
        if g.current_user != item.author:
            return api_abort(403)
        item.done = not item.done
        db.session.commit()
        return '', 204

    def delete(self, item_id):
        """删除条目"""
        item =  Item.query.get_or_404(item_id)
        if g.current_user != item.author:
            return api_abort(403)
        db.session.delete(item)
        db.session.commit()
        return '', 204


class UserAPI(MethodView):
    decorators = [auth_required]

    def get(self):
        return jsonify(user_schema(g.current_user))


class ItemsAPI(MethodView):
    decorators = [auth_required]

    def get(self):
        """获得当前用户的所有条目。"""
        page = request.args.get('page', 1, type=int)
        per_page = current_app.config['TODOISM_ITEM_PER_PAGE']
        pagination = Item.query.with_parent(g.current_user).paginate(page, per_page)
        items = pagination.items
        current = url_for('.items', page=page, _external=True)
        prev = None
        if pagination.has_prev:
            prev = url_for('.items', page=page - 1, _external=True)
        next = None
        if pagination.has_next:
            next = url_for('.items', page=page + 1, _external=True)
        return jsonify(items_schema(items, current, prev, next, pagination))

    def post(self):
        """创建新条目."""
        item = Item(body=get_item_body(), author=g.current_user)
        db.session.add(item )
        db.session.commit()
        response = jsonify(item_schema(item))
        response.status_code = 201
        response.headers['Location'] = url_for('.item', item_id=item.id, _external=True)
        return response


class ActiveItemsAPI(MethodView):
    decorators = [auth_required]

    def get(self):
        """获得用户所有未完成的事项"""
        page = request.args.get('page', 1, type=int)
        pagination = Item.query.with_parent(g.current_user).filter_by(done=False).paginate(
            page, per_page=5)
        items = pagination.items
        current = url_for('.items', page=page, _external=True)
        prev = None
        if pagination.has_prev:
            prev = url_for('.active_items', page=page - 1, _external=True)
        next = None
        if pagination.has_next:
            next = url_for('.active_items', page=page + 1, _external=True)
        return jsonify(items_schema(items, current, prev, next, pagination))


class CompletedItemsAPI(MethodView):
    decorators = [auth_required]

    def get(self):
        """获得用户所有完成的事项"""
        page = request.args.get('page', 1, type=int)
        pagination = Item.query.with_parent(g.current_user).filter_by(done=True).paginate(
            page, per_page=5)
        items = pagination.items
        current = url_for('.items', page=page, _external=True)
        prev = None
        if pagination.has_prev:
            prev = url_for('.completed_items', page=page - 1, _external=True)
        next = None
        if pagination.has_next:
            next = url_for('.completed_items', page=page + 1, _external=True)
        return jsonify(items_schema(items, current, prev, next, pagination))

    def delete(self):
        """删除所有该用户已经完成的事项"""
        Item.query.with_parent(g.current_user).filter_by(done=True).delete()
        db.session.commit()  # TODO: is it better use for loop?
        return '', 204


#     as_view方法将函数转化成视图函数        端点值，比如index，user，是自定义的。
api_v1.add_url_rule('/', view_func=IndexAPI.as_view('index'), methods=['GET'])
api_v1.add_url_rule('/oauth/token', view_func=AuthTokenAPI.as_view('token'), methods=['POST'])
api_v1.add_url_rule('/user', view_func=UserAPI.as_view('user'), methods=['GET'])
api_v1.add_url_rule('/user/items', view_func=ItemsAPI.as_view('items'), methods=['GET', 'POST'])
api_v1.add_url_rule('/user/items/<int:item_id>', view_func=ItemAPI.as_view('item'),
                    methods=['GET', 'PUT', 'PATCH', 'DELETE'])
api_v1.add_url_rule('/user/items/active', view_func=ActiveItemsAPI.as_view('active_items'), methods=['GET'])
api_v1.add_url_rule('/user/items/completed', view_func=CompletedItemsAPI.as_view('completed_items'),
                    methods=['GET', 'DELETE'])
