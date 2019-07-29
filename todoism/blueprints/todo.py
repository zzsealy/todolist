from flask import render_template, request, Blueprint, jsonify
from flask_login import current_user, login_required

from todoism.extensions import db
from todoism.models import Item

todo_bp = Blueprint('todo', __name__)


@todo_bp.route('/app')
@login_required
def app():
    all_count = Item.query.with_parent(current_user).count()  # 返回用户待办事项的个数
    active_count = Item.query.with_parent(current_user).filter_by(done=False).count() # 未完成事项的个数
    completed_count = Item.query.with_parent(current_user).filter_by(done=True).count() # 完成的事项的个数
    return render_template('_app.html', items=current_user.items,
                           all_count=all_count, active_count=active_count, completed_count=completed_count)


# 写新的事项
@todo_bp.route('/item/mew', methods=['POST'])
@login_required
def new_item():
    data = request.get_json()   # 获取输入
    if data is None or data['body'].strip() == '':  # 如果data的body内容去除首尾的空格后返回的结果是空的
        return jsonify(message='无效的内容.'), 400
    item = Item(body=data['body'], author=current_user._get_current_object())
    db.session.add(item)
    db.session.commit()
    return jsonify(html=render_template('_item.html', item=item), message='+1')


# 编辑事项
@todo_bp.route('/item/<int:item_id>/edit', methods=['PUT'])
@login_required
def edit_item(item_id):
    item = Item.query.get_or_404(item_id)
    if current_user != item.author:
        return jsonify(message='没有修改权限！'), 403
    data = request.get_json()
    if data is None or data['body'].strip() == '':  # 如果data的body内容去除首尾的空格后返回的结果是空的
        return jsonify(message='无效的内容.'), 400
    item.body = data['body']
    # db.session.add(item)
    db.session.commit()
    return jsonify(message='事项更新成功！')


# 更改完成状态
@todo_bp.route('/item/<int:item_id>/toggle', methods=['PATCH'])  #PATCH方法请求一个更改的集合
@login_required
def toggle_item(item_id):
    item = Item.query.get_or_404(item_id)
    if current_user != item.author:
        return jsonify(message="没有修改权限！"), 403

    item.done = not item.done
    db.session.commit()
    return jsonify(message='事项完成')


# 删除事项
@todo_bp.route('/item/<int:item_id>/delete', methods=['DELETE'])
@login_required
def delete_item(item_id):
    item = Item.query.get_or_404(item_id)
    if current_user != item.author:
        return jsonify(message='没有权限'), 403

    db.session.delete(item)
    db.session.commit()
    return jsonify(message='删除事项')


@todo_bp.route('/item/clear', methods=['DELETE'])
@login_required
def clear_items():
    items = Item.query.with_parent(current_user).filter_by(done=True).all()
    for item in items:
        db.session.delete(item)
    db.session.commit()
    return jsonify(message='删除了全部的事项！')




