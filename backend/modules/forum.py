from flask import Blueprint, request, jsonify
import os
import uuid
from database import execute_db

forum_bp = Blueprint('forum', __name__)

@forum_bp.route('/posts', methods=['GET'])
def get_posts():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    offset = (page - 1) * per_page
    
    posts = execute_db('''
        SELECT p.id, p.title, p.content, p.created_at, p.view_count, p.parent_id,
               pr.username as author_name,
               (SELECT COUNT(*) FROM forum_comments WHERE post_id = p.id) as comment_count,
               (SELECT COUNT(*) FROM forum_votes WHERE post_id = p.id AND vote_type = 1) as like_count,
               (SELECT COUNT(*) FROM forum_votes WHERE post_id = p.id AND vote_type = -1) as dislike_count
        FROM forum_posts p
        JOIN parents pr ON p.parent_id = pr.id
        ORDER BY p.created_at DESC
        LIMIT ? OFFSET ?
    ''', (per_page, offset))
    
    total = execute_db('SELECT COUNT(*) FROM forum_posts')[0][0]
    
    posts_data = [{
        'id': p[0],
        'title': p[1],
        'content': p[2],
        'created_at': p[3],
        'view_count': p[4],
        'parent_id': p[5],
        'author_name': p[6],
        'comment_count': p[7],
        'like_count': p[8],
        'dislike_count': p[9]
    } for p in posts]
    
    return jsonify({
        'posts': posts_data,
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': (total + per_page - 1) // per_page
    }), 200

@forum_bp.route('/posts/search', methods=['GET'])
def search_posts():
    keyword = request.args.get('keyword', '')
    category_id = request.args.get('category_id')
    sort_by = request.args.get('sort_by', 'latest')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    offset = (page - 1) * per_page
    
    base_query = '''
        SELECT p.id, p.title, p.content, p.created_at, p.view_count, p.parent_id, p.category_id, p.is_pinned, p.is_essential,
               pr.username as author_name, pr.avatar, pr.level,
               (SELECT COUNT(*) FROM forum_comments WHERE post_id = p.id) as comment_count,
               (SELECT COUNT(*) FROM forum_votes WHERE post_id = p.id AND vote_type = 1) as like_count,
               (SELECT COUNT(*) FROM forum_votes WHERE post_id = p.id AND vote_type = -1) as dislike_count
        FROM forum_posts p
        JOIN parents pr ON p.parent_id = pr.id
        WHERE 1=1
    '''
    params = []
    
    if keyword:
        base_query += ' AND (p.title LIKE ? OR p.content LIKE ? OR pr.username LIKE ?)'
        params.extend([f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'])
    
    if category_id:
        base_query += ' AND p.category_id = ?'
        params.append(category_id)
    
    if sort_by == 'relevance' and keyword:
        base_query += ' ORDER BY p.is_pinned DESC, CASE WHEN p.title LIKE ? THEN 100 WHEN pr.username LIKE ? THEN 80 ELSE 30 END DESC, p.created_at DESC'
        params.extend([f'%{keyword}%', f'%{keyword}%'])
    elif sort_by == 'hot':
        base_query += ' ORDER BY p.is_pinned DESC, (p.view_count + (SELECT COUNT(*) FROM forum_comments WHERE post_id = p.id) * 2) DESC, p.created_at DESC'
    elif sort_by == 'essential':
        base_query += ' ORDER BY p.is_pinned DESC, p.is_essential DESC, p.created_at DESC'
    else:
        base_query += ' ORDER BY p.is_pinned DESC, p.created_at DESC'
    
    base_query += ' LIMIT ? OFFSET ?'
    params.extend([per_page, offset])
    
    posts = execute_db(base_query, params)
    
    count_query = 'SELECT COUNT(*) FROM forum_posts p WHERE 1=1'
    count_params = []
    if keyword:
        count_query += ' AND (p.title LIKE ? OR p.content LIKE ?)'
        count_params.extend([f'%{keyword}%', f'%{keyword}%'])
    if category_id:
        count_query += ' AND p.category_id = ?'
        count_params.append(category_id)
    
    total = execute_db(count_query, count_params)[0][0]
    
    posts_data = [{
        'id': p[0],
        'title': p[1],
        'content': p[2],
        'created_at': p[3],
        'view_count': p[4],
        'parent_id': p[5],
        'category_id': p[6],
        'is_pinned': p[7],
        'is_essential': p[8],
        'author_name': p[9],
        'author_avatar': p[10],
        'author_level': p[11],
        'comment_count': p[12],
        'like_count': p[13],
        'dislike_count': p[14]
    } for p in posts]
    
    return jsonify({
        'posts': posts_data,
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': (total + per_page - 1) // per_page
    }), 200

@forum_bp.route('/posts/<int:post_id>', methods=['GET'])
def get_post(post_id):
    execute_db('UPDATE forum_posts SET view_count = view_count + 1 WHERE id = ?', (post_id,))
    
    post = execute_db('''
        SELECT p.id, p.title, p.content, p.created_at, p.view_count, p.parent_id, p.category_id, p.is_pinned, p.is_essential,
               pr.username as author_name, pr.level as author_level,
               (SELECT COUNT(*) FROM forum_votes WHERE post_id = p.id AND vote_type = 1) as like_count,
               (SELECT COUNT(*) FROM forum_votes WHERE post_id = p.id AND vote_type = -1) as dislike_count
        FROM forum_posts p
        JOIN parents pr ON p.parent_id = pr.id
        WHERE p.id = ?
    ''', (post_id,))
    
    if not post:
        return jsonify({'error': '帖子不存在'}), 404
    
    p = post[0]
    return jsonify({
        'id': p[0],
        'title': p[1],
        'content': p[2],
        'created_at': p[3],
        'view_count': p[4],
        'parent_id': p[5],
        'category_id': p[6],
        'is_pinned': p[7],
        'is_essential': p[8],
        'author_name': p[9],
        'author_level': p[10],
        'like_count': p[11],
        'dislike_count': p[12]
    }), 200

@forum_bp.route('/posts', methods=['POST'])
def create_post():
    data = request.json
    parent_id = data.get('parent_id')
    title = data.get('title')
    content = data.get('content')
    category_id = data.get('category_id')
    
    if not parent_id or not title or not content:
        return jsonify({'error': '家长ID、标题和内容不能为空'}), 400
    
    result, post_id = execute_db(
        'INSERT INTO forum_posts (parent_id, title, content, category_id) VALUES (?, ?, ?, ?)',
        (parent_id, title, content, category_id), fetch_last_id=True
    )
    
    return jsonify({'message': '发帖成功', 'post_id': post_id}), 201

@forum_bp.route('/posts/<int:post_id>', methods=['PUT'])
def update_post(post_id):
    data = request.json
    parent_id = data.get('parent_id')
    title = data.get('title')
    content = data.get('content')
    category_id = data.get('category_id')
    
    if not parent_id:
        return jsonify({'error': '用户ID不能为空'}), 400
    
    post_result = execute_db('SELECT parent_id FROM forum_posts WHERE id = ?', (post_id,))
    if not post_result:
        return jsonify({'error': '帖子不存在'}), 404
    
    user_result = execute_db('SELECT role FROM parents WHERE id = ?', (parent_id,))
    if not user_result:
        return jsonify({'error': '用户不存在'}), 404
    
    role = user_result[0][0]
    if post_result[0][0] != parent_id and role != 'admin':
        return jsonify({'error': '无权编辑此帖子'}), 403
    
    update_fields = []
    update_params = []
    
    if title:
        update_fields.append('title = ?')
        update_params.append(title)
    if content:
        update_fields.append('content = ?')
        update_params.append(content)
    if category_id:
        update_fields.append('category_id = ?')
        update_params.append(category_id)
    
    if update_fields:
        update_fields.append('updated_at = CURRENT_TIMESTAMP')
        update_params.append(post_id)
        execute_db(f'UPDATE forum_posts SET {", ".join(update_fields)} WHERE id = ?', update_params)
    
    return jsonify({'message': '更新成功'}), 200

@forum_bp.route('/posts/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    data = request.json or {}
    parent_id = data.get('parent_id')
    
    if parent_id:
        user_result = execute_db('SELECT role FROM parents WHERE id = ?', (parent_id,))
        if user_result:
            role = user_result[0][0]
            if role == 'admin':
                execute_db('DELETE FROM forum_comments WHERE post_id = ?', (post_id,))
                execute_db('DELETE FROM forum_votes WHERE post_id = ?', (post_id,))
                execute_db('DELETE FROM forum_posts WHERE id = ?', (post_id,))
                return jsonify({'message': '删除成功'}), 200
        
        post_result = execute_db('SELECT parent_id FROM forum_posts WHERE id = ?', (post_id,))
        if post_result and post_result[0][0] == parent_id:
            execute_db('DELETE FROM forum_comments WHERE post_id = ?', (post_id,))
            execute_db('DELETE FROM forum_votes WHERE post_id = ?', (post_id,))
            execute_db('DELETE FROM forum_posts WHERE id = ?', (post_id,))
            return jsonify({'message': '删除成功'}), 200
        
        return jsonify({'error': '无权删除此帖子'}), 403
    
    execute_db('DELETE FROM forum_comments WHERE post_id = ?', (post_id,))
    execute_db('DELETE FROM forum_votes WHERE post_id = ?', (post_id,))
    execute_db('DELETE FROM forum_posts WHERE id = ?', (post_id,))
    return jsonify({'message': '删除成功'}), 200

@forum_bp.route('/posts/<int:post_id>/pin', methods=['POST'])
def pin_post(post_id):
    data = request.json
    parent_id = data.get('parent_id')
    is_pinned = data.get('is_pinned', 1)
    
    user_result = execute_db('SELECT role FROM parents WHERE id = ?', (parent_id,))
    if not user_result or user_result[0][0] != 'admin':
        return jsonify({'error': '无权操作'}), 403
    
    execute_db('UPDATE forum_posts SET is_pinned = ? WHERE id = ?', (is_pinned, post_id))
    return jsonify({'message': '操作成功'}), 200

@forum_bp.route('/posts/<int:post_id>/essential', methods=['POST'])
def essential_post(post_id):
    data = request.json
    parent_id = data.get('parent_id')
    is_essential = data.get('is_essential', 1)
    
    user_result = execute_db('SELECT role FROM parents WHERE id = ?', (parent_id,))
    if not user_result or user_result[0][0] != 'admin':
        return jsonify({'error': '无权操作'}), 403
    
    execute_db('UPDATE forum_posts SET is_essential = ? WHERE id = ?', (is_essential, post_id))
    return jsonify({'message': '操作成功'}), 200

@forum_bp.route('/posts/hot', methods=['GET'])
def get_hot_posts():
    limit = int(request.args.get('limit', 5))
    
    result = execute_db('''
        SELECT p.id, p.title, p.view_count,
               (SELECT COUNT(*) FROM forum_comments WHERE post_id = p.id) as comment_count,
               (SELECT COUNT(*) FROM forum_votes WHERE post_id = p.id AND vote_type = 1) as like_count
        FROM forum_posts p
        ORDER BY (p.view_count + (SELECT COUNT(*) FROM forum_comments WHERE post_id = p.id) * 2 + 
                  (SELECT COUNT(*) FROM forum_votes WHERE post_id = p.id AND vote_type = 1) * 3) DESC
        LIMIT ?
    ''', (limit,))
    
    hot_posts = [{
        'id': h[0],
        'title': h[1],
        'view_count': h[2],
        'comment_count': h[3],
        'like_count': h[4]
    } for h in result]
    
    return jsonify(hot_posts), 200

@forum_bp.route('/comments', methods=['GET'])
def get_comments():
    post_id = request.args.get('post_id')
    if not post_id:
        return jsonify({'error': '帖子ID不能为空'}), 400
    
    comments = execute_db('''
        SELECT c.id, c.content, c.created_at, c.parent_id,
               pr.username as author_name,
               (SELECT COUNT(*) FROM forum_votes WHERE comment_id = c.id AND vote_type = 1) as like_count,
               (SELECT COUNT(*) FROM forum_votes WHERE comment_id = c.id AND vote_type = -1) as dislike_count
        FROM forum_comments c
        JOIN parents pr ON c.parent_id = pr.id
        WHERE c.post_id = ?
        ORDER BY c.created_at ASC
    ''', (post_id,))
    
    comments_data = [{
        'id': c[0],
        'content': c[1],
        'created_at': c[2],
        'parent_id': c[3],
        'author_name': c[4],
        'like_count': c[5],
        'dislike_count': c[6]
    } for c in comments]
    
    return jsonify(comments_data), 200

@forum_bp.route('/comments', methods=['POST'])
def create_comment():
    data = request.json
    post_id = data.get('post_id')
    parent_id = data.get('parent_id')
    content = data.get('content')
    
    if not post_id or not parent_id or not content:
        return jsonify({'error': '帖子ID、家长ID和内容不能为空'}), 400
    
    result, comment_id = execute_db(
        'INSERT INTO forum_comments (post_id, parent_id, content) VALUES (?, ?, ?)',
        (post_id, parent_id, content), fetch_last_id=True
    )
    
    return jsonify({'message': '评论成功', 'comment_id': comment_id}), 201

@forum_bp.route('/vote', methods=['POST'])
def vote():
    data = request.json
    parent_id = data.get('parent_id')
    vote_type = data.get('vote_type')
    post_id = data.get('post_id')
    comment_id = data.get('comment_id')
    
    if not parent_id or vote_type is None:
        return jsonify({'error': '参数不完整'}), 400
    
    if not post_id and not comment_id:
        return jsonify({'error': '必须指定帖子或评论'}), 400
    
    existing = execute_db('''
        SELECT id FROM forum_votes 
        WHERE parent_id = ? AND (post_id = ? OR comment_id = ?)
    ''', (parent_id, post_id, comment_id))
    
    if existing:
        execute_db('''
            UPDATE forum_votes SET vote_type = ? 
            WHERE parent_id = ? AND (post_id = ? OR comment_id = ?)
        ''', (vote_type, parent_id, post_id, comment_id))
    else:
        execute_db('''
            INSERT INTO forum_votes (parent_id, post_id, comment_id, vote_type)
            VALUES (?, ?, ?, ?)
        ''', (parent_id, post_id, comment_id, vote_type))
    
    return jsonify({'message': '投票成功'}), 200

@forum_bp.route('/favorites', methods=['POST'])
def add_favorite():
    data = request.json
    parent_id = data.get('parent_id')
    post_id = data.get('post_id')
    
    if not parent_id or not post_id:
        return jsonify({'error': '参数不完整'}), 400
    
    try:
        execute_db('INSERT INTO favorites (parent_id, post_id) VALUES (?, ?)', (parent_id, post_id))
        return jsonify({'message': '收藏成功'}), 201
    except:
        return jsonify({'error': '已收藏或帖子不存在'}), 400

@forum_bp.route('/favorites', methods=['DELETE'])
def remove_favorite():
    data = request.json
    parent_id = data.get('parent_id')
    post_id = data.get('post_id')
    
    if not parent_id or not post_id:
        return jsonify({'error': '参数不完整'}), 400
    
    execute_db('DELETE FROM favorites WHERE parent_id = ? AND post_id = ?', (parent_id, post_id))
    return jsonify({'message': '取消收藏成功'}), 200

@forum_bp.route('/favorites/<int:parent_id>', methods=['GET'])
def get_favorites(parent_id):
    result = execute_db('''
        SELECT p.id, p.title, p.content, p.created_at, p.view_count, p.parent_id,
               pr.username as author_name,
               (SELECT COUNT(*) FROM forum_comments WHERE post_id = p.id) as comment_count,
               (SELECT COUNT(*) FROM forum_votes WHERE post_id = p.id AND vote_type = 1) as like_count
        FROM favorites f
        JOIN forum_posts p ON f.post_id = p.id
        JOIN parents pr ON p.parent_id = pr.id
        WHERE f.parent_id = ?
        ORDER BY f.created_at DESC
    ''', (parent_id,))
    
    favorites = [{
        'id': f[0],
        'title': f[1],
        'content': f[2],
        'created_at': f[3],
        'view_count': f[4],
        'parent_id': f[5],
        'author_name': f[6],
        'comment_count': f[7],
        'like_count': f[8]
    } for f in result]
    
    return jsonify(favorites), 200

@forum_bp.route('/favorites/check', methods=['GET'])
def check_favorite():
    parent_id = request.args.get('parent_id')
    post_id = request.args.get('post_id')
    
    if not parent_id or not post_id:
        return jsonify({'error': '参数不完整'}), 400
    
    result = execute_db('SELECT id FROM favorites WHERE parent_id = ? AND post_id = ?', (parent_id, post_id))
    return jsonify({'is_favorited': len(result) > 0}), 200

@forum_bp.route('/reports', methods=['POST'])
def create_report():
    data = request.json
    parent_id = data.get('parent_id')
    post_id = data.get('post_id')
    comment_id = data.get('comment_id')
    reason = data.get('reason')
    
    if not parent_id or not reason:
        return jsonify({'error': '参数不完整'}), 400
    
    if not post_id and not comment_id:
        return jsonify({'error': '必须指定帖子或评论'}), 400
    
    execute_db('''
        INSERT INTO reports (parent_id, post_id, comment_id, reason)
        VALUES (?, ?, ?, ?)
    ''', (parent_id, post_id, comment_id, reason))
    
    return jsonify({'message': '举报成功，我们会尽快处理'}), 201

@forum_bp.route('/categories', methods=['GET'])
def get_categories():
    result = execute_db('SELECT id, name, description, icon, sort_order FROM categories ORDER BY sort_order')
    categories = [{'id': c[0], 'name': c[1], 'description': c[2], 'icon': c[3], 'sort_order': c[4]} for c in result]
    return jsonify(categories), 200

@forum_bp.route('/upload/image', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({'error': '没有上传图片'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    if '.' not in file.filename or file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
        return jsonify({'error': '不支持的文件格式'}), 400
    
    filename = f"{uuid.uuid4().hex}.{file.filename.rsplit('.', 1)[1].lower()}"
    upload_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'frontend', 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, filename)
    file.save(file_path)
    
    return jsonify({'url': f'/uploads/{filename}'}), 200
