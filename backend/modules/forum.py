from flask import Blueprint, request, jsonify
import os
import uuid
import sqlite3
from database import execute_db
from utils import build_update_sql, is_admin, success_response, error_response
from middleware import require_auth
from config import CATEGORIES

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
               COALESCE((SELECT COUNT(*) FROM forum_votes WHERE post_id = p.id AND vote_type = 1), 0) as like_count,
               COALESCE((SELECT COUNT(*) FROM forum_votes WHERE post_id = p.id AND vote_type = -1), 0) as dislike_count
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
    
    # 获取当前用户ID（如果已登录）
    user_id = request.user_id if hasattr(request, 'user_id') else None
    
    base_query = '''
        SELECT p.id, p.title, p.content, p.created_at, p.view_count, p.parent_id, p.category_id, p.is_pinned, p.is_essential,
               pr.username as author_name, pr.avatar, pr.level,
               COALESCE((SELECT COUNT(*) FROM forum_comments WHERE post_id = p.id), 0) as comment_count,
               COALESCE((SELECT COUNT(*) FROM forum_votes WHERE post_id = p.id AND vote_type = 1), 0) as like_count,
               COALESCE((SELECT COUNT(*) FROM forum_votes WHERE post_id = p.id AND vote_type = -1), 0) as dislike_count,
               COALESCE((SELECT COUNT(*) FROM favorites WHERE post_id = p.id), 0) as favorite_count
    '''
    
    # 如果用户已登录，添加用户投票状态和收藏状态
    if user_id:
        base_query += ''',
               (SELECT vote_type FROM forum_votes WHERE post_id = p.id AND parent_id = ?) as user_vote,
               (SELECT 1 FROM favorites WHERE post_id = p.id AND parent_id = ?) as is_favorited
    '''
    
    base_query += '''
        FROM forum_posts p
        JOIN parents pr ON p.parent_id = pr.id
        WHERE 1=1
    '''
    
    params = []
    if user_id:
        params.extend([user_id, user_id])
    
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
    
    posts_data = []
    for p in posts:
        post_data = {
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
            'dislike_count': p[14],
            'favorite_count': p[15]
        }
        # 如果用户已登录，添加用户投票状态和收藏状态
        if user_id and len(p) > 16:
            post_data['user_vote'] = p[16] if p[16] else 0
            post_data['is_favorited'] = p[17] == 1 if len(p) > 17 else False
        posts_data.append(post_data)
    
    return success_response({
        'posts': posts_data,
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': (total + per_page - 1) // per_page
    })

@forum_bp.route('/posts/<int:post_id>', methods=['GET'])
def get_post(post_id):
    execute_db('UPDATE forum_posts SET view_count = view_count + 1 WHERE id = ?', (post_id,))
    
    # 获取当前用户ID（如果已登录）
    user_id = request.user_id if hasattr(request, 'user_id') else None
    
    base_query = '''
        SELECT p.id, p.title, p.content, p.created_at, p.view_count, p.parent_id, p.category_id, p.is_pinned, p.is_essential,
               pr.username as author_name, pr.level as author_level,
               COALESCE((SELECT COUNT(*) FROM forum_votes WHERE post_id = p.id AND vote_type = 1), 0) as like_count,
               COALESCE((SELECT COUNT(*) FROM forum_votes WHERE post_id = p.id AND vote_type = -1), 0) as dislike_count
    '''
    
    # 如果用户已登录，添加用户投票状态和收藏状态
    if user_id:
        base_query += ''',
               (SELECT vote_type FROM forum_votes WHERE post_id = p.id AND parent_id = ?) as user_vote,
               (SELECT 1 FROM favorites WHERE post_id = p.id AND parent_id = ?) as is_favorited
    '''
    
    base_query += '''
        FROM forum_posts p
        JOIN parents pr ON p.parent_id = pr.id
        WHERE p.id = ?
    '''
    
    params = []
    if user_id:
        params.extend([user_id, user_id])
    params.append(post_id)
    
    post = execute_db(base_query, params)
    
    if not post:
        return error_response('帖子不存在', status=404)
    
    p = post[0]
    post_data = {
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
    }
    
    # 如果用户已登录，添加用户投票状态和收藏状态
    if user_id and len(p) > 12:
        post_data['user_vote'] = p[13] if p[13] else 0
        post_data['is_favorited'] = p[14] == 1
    
    return success_response(post_data)

@forum_bp.route('/posts', methods=['POST'])
def create_post():
    data = request.json
    parent_id = data.get('parent_id')
    title = data.get('title')
    content = data.get('content')
    category_id = data.get('category_id')
    
    if not parent_id or not title or not content:
        return error_response('家长ID、标题和内容不能为空', status=400)
    
    try:
        result, post_id = execute_db(
            'INSERT INTO forum_posts (parent_id, title, content, category_id) VALUES (?, ?, ?, ?)',
            (parent_id, title, content, category_id), fetch_last_id=True
        )
        
        return success_response({'post_id': post_id}, '发帖成功')
    except Exception as e:
        print(f"发帖操作失败: {e}")
        return error_response('服务器内部错误', status=500)

@forum_bp.route('/posts/<int:post_id>', methods=['PUT'])
def update_post(post_id):
    data = request.json
    parent_id = data.get('parent_id')
    title = data.get('title')
    content = data.get('content')
    category_id = data.get('category_id')
    
    if not parent_id:
        return error_response('用户ID不能为空', status=400)
    
    try:
        post_result = execute_db('SELECT parent_id FROM forum_posts WHERE id = ?', (post_id,))
        if not post_result:
            return error_response('帖子不存在', status=404)
        
        if post_result[0][0] != parent_id and not is_admin(parent_id):
            return error_response('无权编辑此帖子', status=403)
        
        update_data = {}
        
        if title:
            update_data['title'] = title
        if content:
            update_data['content'] = content
        if category_id:
            update_data['category_id'] = category_id
        
        if update_data:
            update_data['updated_at'] = 'CURRENT_TIMESTAMP'
            sql, params = build_update_sql('forum_posts', update_data, 'id = ?')
            execute_db(sql, params + (post_id,))
        
        return success_response(None, '更新成功')
    except Exception as e:
        print(f"更新帖子操作失败: {e}")
        return error_response('服务器内部错误', status=500)

@forum_bp.route('/posts/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    data = request.json or {}
    parent_id = data.get('parent_id')
    
    try:
        if parent_id:
            if is_admin(parent_id):
                execute_db('DELETE FROM forum_comments WHERE post_id = ?', (post_id,))
                execute_db('DELETE FROM forum_votes WHERE post_id = ?', (post_id,))
                execute_db('DELETE FROM forum_posts WHERE id = ?', (post_id,))
                return success_response(None, '删除成功')
            
            post_result = execute_db('SELECT parent_id FROM forum_posts WHERE id = ?', (post_id,))
            if post_result and post_result[0][0] == parent_id:
                execute_db('DELETE FROM forum_comments WHERE post_id = ?', (post_id,))
                execute_db('DELETE FROM forum_votes WHERE post_id = ?', (post_id,))
                execute_db('DELETE FROM forum_posts WHERE id = ?', (post_id,))
                return success_response(None, '删除成功')
            
            return error_response('无权删除此帖子', status=403)
        
        execute_db('DELETE FROM forum_comments WHERE post_id = ?', (post_id,))
        execute_db('DELETE FROM forum_votes WHERE post_id = ?', (post_id,))
        execute_db('DELETE FROM forum_posts WHERE id = ?', (post_id,))
        return success_response(None, '删除成功')
    except Exception as e:
        print(f"删除帖子操作失败: {e}")
        return error_response('服务器内部错误', status=500)

@forum_bp.route('/posts/<int:post_id>/pin', methods=['POST'])
def pin_post(post_id):
    data = request.json
    parent_id = data.get('parent_id')
    is_pinned = data.get('is_pinned', 1)
    
    if not is_admin(parent_id):
        return error_response('无权操作', status=403)
    
    try:
        execute_db('UPDATE forum_posts SET is_pinned = ? WHERE id = ?', (is_pinned, post_id))
        return success_response(None, '操作成功')
    except Exception as e:
        print(f"置顶操作失败: {e}")
        return error_response('服务器内部错误', status=500)

@forum_bp.route('/posts/<int:post_id>/essential', methods=['POST'])
def essential_post(post_id):
    data = request.json
    parent_id = data.get('parent_id')
    is_essential = data.get('is_essential', 1)
    
    if not is_admin(parent_id):
        return error_response('无权操作', status=403)
    
    try:
        execute_db('UPDATE forum_posts SET is_essential = ? WHERE id = ?', (is_essential, post_id))
        return success_response(None, '操作成功')
    except Exception as e:
        print(f"精华操作失败: {e}")
        return error_response('服务器内部错误', status=500)

@forum_bp.route('/posts/hot', methods=['GET'])
def get_hot_posts():
    limit = int(request.args.get('limit', 5))
    
    result = execute_db('''
        SELECT p.id, p.title, p.view_count,
               COALESCE((SELECT COUNT(*) FROM forum_comments WHERE post_id = p.id), 0) as comment_count,
               COALESCE((SELECT COUNT(*) FROM forum_votes WHERE post_id = p.id AND vote_type = 1), 0) as like_count,
               COALESCE((SELECT COUNT(*) FROM forum_votes WHERE post_id = p.id AND vote_type = -1), 0) as dislike_count,
               COALESCE((SELECT COUNT(*) FROM favorites WHERE post_id = p.id), 0) as favorite_count
        FROM forum_posts p
        ORDER BY (p.view_count + 
                  COALESCE((SELECT COUNT(*) FROM forum_comments WHERE post_id = p.id), 0) * 2 + 
                  COALESCE((SELECT COUNT(*) FROM forum_votes WHERE post_id = p.id AND vote_type = 1), 0) * 3 - 
                  COALESCE((SELECT COUNT(*) FROM forum_votes WHERE post_id = p.id AND vote_type = -1), 0) * 1 + 
                  COALESCE((SELECT COUNT(*) FROM favorites WHERE post_id = p.id), 0) * 4) DESC
        LIMIT ?
    ''', (limit,))
    
    hot_posts = [{
        'id': h[0],
        'title': h[1],
        'view_count': h[2],
        'comment_count': h[3],
        'like_count': h[4],
        'dislike_count': h[5],
        'favorite_count': h[6]
    } for h in result]
    
    return jsonify(hot_posts), 200

@forum_bp.route('/comments', methods=['GET'])
def get_comments():
    post_id = request.args.get('post_id')
    if not post_id:
        return error_response('帖子ID不能为空', status=400)
    
    comments = execute_db('''
        SELECT c.id, c.content, c.created_at, c.parent_id,
               pr.username as author_name,
               COALESCE((SELECT COUNT(*) FROM forum_votes WHERE comment_id = c.id AND vote_type = 1), 0) as like_count,
               COALESCE((SELECT COUNT(*) FROM forum_votes WHERE comment_id = c.id AND vote_type = -1), 0) as dislike_count
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
    
    return success_response(comments_data)

@forum_bp.route('/comments', methods=['POST'])
def create_comment():
    data = request.json
    post_id = data.get('post_id')
    parent_id = data.get('parent_id')
    content = data.get('content')
    
    if not post_id or not parent_id or not content:
        return error_response('帖子ID、家长ID和内容不能为空', status=400)
    
    result, comment_id = execute_db(
        'INSERT INTO forum_comments (post_id, parent_id, content) VALUES (?, ?, ?)',
        (post_id, parent_id, content), fetch_last_id=True
    )
    
    return success_response({'comment_id': comment_id}, '评论成功')

@forum_bp.route('/vote', methods=['POST'])
def vote():
    data = request.json
    parent_id = data.get('parent_id')
    vote_type = data.get('vote_type')
    post_id = data.get('post_id')
    comment_id = data.get('comment_id')
    
    # 增强参数校验
    if not parent_id:
        return error_response('用户ID不能为空', status=400)
    if vote_type is None:
        return error_response('投票类型不能为空', status=400)
    if not post_id and not comment_id:
        return error_response('必须指定帖子或评论', status=400)
    if post_id and comment_id:
        return error_response('不能同时指定帖子和评论', status=400)
    
    try:
        # 根据是帖子还是评论构建不同的查询条件
        if post_id:
            # 检查帖子是否存在
            post_exists = execute_db('SELECT id FROM forum_posts WHERE id = ?', (post_id,))
            if not post_exists:
                return error_response('帖子不存在', status=404)
            
            existing = execute_db('''
                SELECT id FROM forum_votes 
                WHERE parent_id = ? AND post_id = ? AND comment_id IS NULL
            ''', (parent_id, post_id))
            
            if existing:
                if vote_type == 0:
                    # 取消投票
                    execute_db('''
                        DELETE FROM forum_votes 
                        WHERE parent_id = ? AND post_id = ? AND comment_id IS NULL
                    ''', (parent_id, post_id))
                else:
                    # 更新投票类型
                    execute_db('''
                        UPDATE forum_votes SET vote_type = ? 
                        WHERE parent_id = ? AND post_id = ? AND comment_id IS NULL
                    ''', (vote_type, parent_id, post_id))
            elif vote_type != 0:
                # 新增投票
                execute_db('''
                    INSERT INTO forum_votes (parent_id, post_id, comment_id, vote_type)
                    VALUES (?, ?, NULL, ?)
                ''', (parent_id, post_id, vote_type))
        elif comment_id:
            # 检查评论是否存在
            comment_exists = execute_db('SELECT id FROM forum_comments WHERE id = ?', (comment_id,))
            if not comment_exists:
                return error_response('评论不存在', status=404)
            
            existing = execute_db('''
                SELECT id FROM forum_votes 
                WHERE parent_id = ? AND post_id IS NULL AND comment_id = ?
            ''', (parent_id, comment_id))
            
            if existing:
                if vote_type == 0:
                    # 取消投票
                    execute_db('''
                        DELETE FROM forum_votes 
                        WHERE parent_id = ? AND post_id IS NULL AND comment_id = ?
                    ''', (parent_id, comment_id))
                else:
                    # 更新投票类型
                    execute_db('''
                        UPDATE forum_votes SET vote_type = ? 
                        WHERE parent_id = ? AND post_id IS NULL AND comment_id = ?
                    ''', (vote_type, parent_id, comment_id))
            elif vote_type != 0:
                # 新增投票
                execute_db('''
                    INSERT INTO forum_votes (parent_id, post_id, comment_id, vote_type)
                    VALUES (?, NULL, ?, ?)
                ''', (parent_id, comment_id, vote_type))
        
        return success_response(None, '投票成功')
    except Exception as e:
        print(f"投票操作失败: {e}")
        return error_response('服务器内部错误', status=500)

@forum_bp.route('/favorites', methods=['GET'])
@require_auth
def get_favorites():
    parent_id = request.user_id
    
    result = execute_db('''
        SELECT p.id, p.title, p.content, p.created_at, p.view_count, p.parent_id,
               pr.username as author_name,
               (SELECT COUNT(*) FROM forum_comments WHERE post_id = p.id) as comment_count,
               (SELECT COUNT(*) FROM forum_votes WHERE post_id = p.id AND vote_type = 1) as like_count,
               (SELECT COUNT(*) FROM favorites WHERE post_id = p.id) as favorite_count
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
        'like_count': f[8],
        'favorite_count': f[9]
    } for f in result]
    
    return success_response(favorites)

@forum_bp.route('/favorites/<int:post_id>', methods=['POST'])
@require_auth
def add_favorite(post_id):
    parent_id = request.user_id
    
    try:
        execute_db('INSERT INTO favorites (parent_id, post_id) VALUES (?, ?)', (parent_id, post_id))
        return success_response(None, '收藏成功')
    except sqlite3.IntegrityError:
        return error_response('已收藏或帖子不存在', status=400)
    except Exception as e:
        print(f"收藏操作失败: {e}")
        return error_response('服务器内部错误', status=500)

@forum_bp.route('/favorites/<int:post_id>', methods=['DELETE'])
@require_auth
def remove_favorite(post_id):
    parent_id = request.user_id
    
    try:
        execute_db('DELETE FROM favorites WHERE parent_id = ? AND post_id = ?', (parent_id, post_id))
        return success_response(None, '取消收藏成功')
    except Exception as e:
        print(f"取消收藏操作失败: {e}")
        return error_response('服务器内部错误', status=500)

@forum_bp.route('/categories', methods=['GET'])
def get_categories():
    return jsonify(CATEGORIES), 200

@forum_bp.route('/upload/image', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return error_response('没有上传图片', status=400)
    
    file = request.files['image']
    if file.filename == '':
        return error_response('没有选择文件', status=400)
    
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    if '.' not in file.filename or file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
        return error_response('不支持的文件格式', status=400)
    
    filename = f"{uuid.uuid4().hex}.{file.filename.rsplit('.', 1)[1].lower()}"
    upload_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'frontend', 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, filename)
    file.save(file_path)
    
    return success_response({'url': f'/uploads/{filename}'})
