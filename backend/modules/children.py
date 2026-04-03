from flask import Blueprint, request, jsonify
from database import execute_db

children_bp = Blueprint('children', __name__)

@children_bp.route('/api/children', methods=['POST'])
def add_child():
    data = request.json
    parent_id = data.get('parent_id')
    name = data.get('name')
    age = data.get('age')
    
    if not parent_id or not name:
        return jsonify({'error': '家长ID和孩子姓名不能为空'}), 400
    
    result, child_id = execute_db(
        'INSERT INTO children (parent_id, name, age) VALUES (?, ?, ?)',
        (parent_id, name, age), fetch_last_id=True
    )
    
    return jsonify({'message': '添加成功', 'child_id': child_id}), 201

@children_bp.route('/api/children/<int:parent_id>', methods=['GET'])
def get_children(parent_id):
    result = execute_db(
        'SELECT id, name, age, created_at FROM children WHERE parent_id = ?',
        (parent_id,)
    )
    
    children = [{'id': c[0], 'name': c[1], 'age': c[2], 'created_at': c[3]} for c in result]
    return jsonify(children), 200

@children_bp.route('/api/children/<int:child_id>', methods=['DELETE'])
def delete_child(child_id):
    execute_db('DELETE FROM children WHERE id = ?', (child_id,))
    return jsonify({'message': '删除成功'}), 200
