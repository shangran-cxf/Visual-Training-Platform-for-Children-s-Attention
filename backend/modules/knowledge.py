from flask import Blueprint, request, jsonify
import os
import json
from datetime import datetime
from database import execute_db
from config import FRONTEND_DIR

knowledge_bp = Blueprint('knowledge', __name__)

KNOWLEDGE_DATA_PATH = os.path.join(FRONTEND_DIR, 'knowledge', 'knowledge-data.json')

def load_articles():
    if not os.path.exists(KNOWLEDGE_DATA_PATH):
        return []
    with open(KNOWLEDGE_DATA_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data.get('articles', [])

def save_articles(articles):
    os.makedirs(os.path.dirname(KNOWLEDGE_DATA_PATH), exist_ok=True)
    with open(KNOWLEDGE_DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump({'articles': articles}, f, ensure_ascii=False, indent=2)

@knowledge_bp.route('/articles', methods=['GET'])
def get_articles():
    articles = load_articles()
    articles_sorted = sorted(articles, key=lambda x: x.get('date', ''), reverse=True)
    return jsonify(articles_sorted), 200

@knowledge_bp.route('/articles/search', methods=['GET'])
def search_articles():
    keyword = request.args.get('keyword', '').lower()
    tag = request.args.get('tag', '')
    
    articles = load_articles()
    results = []
    
    for article in articles:
        match_keyword = True
        match_tag = True
        
        if keyword:
            title = article.get('title', '').lower()
            content = article.get('content', '').lower()
            author = article.get('author', '').lower()
            match_keyword = keyword in title or keyword in content or keyword in author
        
        if tag:
            article_tags = article.get('tags', [])
            match_tag = tag in article_tags
        
        if match_keyword and match_tag:
            results.append(article)
    
    results_sorted = sorted(results, key=lambda x: x.get('date', ''), reverse=True)
    return jsonify(results_sorted), 200

@knowledge_bp.route('/tags', methods=['GET'])
def get_tags():
    articles = load_articles()
    tags_set = set()
    
    for article in articles:
        article_tags = article.get('tags', [])
        tags_set.update(article_tags)
    
    tags_list = sorted(list(tags_set))
    return jsonify(tags_list), 200

@knowledge_bp.route('/articles', methods=['POST'])
def create_article():
    data = request.json
    
    title = data.get('title')
    content = data.get('content')
    author = data.get('author')
    category = data.get('category')
    tags = data.get('tags', [])
    summary = data.get('summary')
    difficulty = data.get('difficulty', '初级')
    reading_time = data.get('reading_time', 5)
    
    if not title or not content or not author:
        return jsonify({'error': '标题、内容和作者不能为空'}), 400
    
    articles = load_articles()
    
    max_id = 0
    for article in articles:
        if article.get('id', 0) > max_id:
            max_id = article['id']
    
    new_article = {
        'id': max_id + 1,
        'title': title,
        'content': content,
        'author': author,
        'date': datetime.now().strftime('%Y-%m-%d'),
        'category': category,
        'tags': tags if isinstance(tags, list) else [],
        'summary': summary,
        'difficulty': difficulty,
        'reading_time': reading_time
    }
    
    articles.append(new_article)
    save_articles(articles)
    
    return jsonify({'message': '文章添加成功', 'article': new_article}), 201

@knowledge_bp.route('/articles/<int:article_id>', methods=['PUT'])
def update_article(article_id):
    data = request.json
    
    articles = load_articles()
    article_index = None
    
    for i, article in enumerate(articles):
        if article.get('id') == article_id:
            article_index = i
            break
    
    if article_index is None:
        return jsonify({'error': '文章不存在'}), 404
    
    article = articles[article_index]
    
    if 'title' in data:
        article['title'] = data['title']
    if 'content' in data:
        article['content'] = data['content']
    if 'author' in data:
        article['author'] = data['author']
    if 'category' in data:
        article['category'] = data['category']
    if 'tags' in data:
        article['tags'] = data['tags'] if isinstance(data['tags'], list) else []
    if 'summary' in data:
        article['summary'] = data['summary']
    if 'difficulty' in data:
        article['difficulty'] = data['difficulty']
    if 'reading_time' in data:
        article['reading_time'] = data['reading_time']
    
    article['date'] = datetime.now().strftime('%Y-%m-%d')
    
    articles[article_index] = article
    save_articles(articles)
    
    return jsonify({'message': '文章更新成功', 'article': article}), 200

@knowledge_bp.route('/articles/<int:article_id>', methods=['DELETE'])
def delete_article(article_id):
    articles = load_articles()
    article_index = None
    
    for i, article in enumerate(articles):
        if article.get('id') == article_id:
            article_index = i
            break
    
    if article_index is None:
        return jsonify({'error': '文章不存在'}), 404
    
    deleted_article = articles.pop(article_index)
    save_articles(articles)
    
    return jsonify({'message': '文章删除成功', 'deleted_id': deleted_article['id']}), 200
