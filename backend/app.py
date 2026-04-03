from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

from config import FRONTEND_DIR, APP_CONFIG
from database import init_db, execute_db
from modules import auth_bp, children_bp, forum_bp, knowledge_bp, badges_bp, admin_bp
from analytics import data_collector_bp

app = Flask(__name__)
app.static_folder = FRONTEND_DIR
CORS(app)

init_db()

app.register_blueprint(auth_bp)
app.register_blueprint(children_bp)
app.register_blueprint(forum_bp, url_prefix='/api/forum')
app.register_blueprint(knowledge_bp, url_prefix='/api/knowledge')
app.register_blueprint(badges_bp)
app.register_blueprint(admin_bp)

app.register_blueprint(data_collector_bp)

@app.route('/')
def index():
    return send_from_directory(FRONTEND_DIR, 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory(FRONTEND_DIR, path)

@app.route('/api/upload/detection', methods=['POST'])
def upload_detection():
    data = request.json
    child_id = data.get('child_id')
    selective_attention = data.get('selective_attention')
    sustained_attention = data.get('sustained_attention')
    visual_tracking = data.get('visual_tracking')
    working_memory = data.get('working_memory')
    inhibitory_control = data.get('inhibitory_control')
    total_score = data.get('total_score')
    
    if not child_id:
        return jsonify({'error': '孩子ID不能为空'}), 400
    
    execute_db('''
        INSERT INTO detection_data (child_id, selective_attention, sustained_attention, visual_tracking, working_memory, inhibitory_control, total_score)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (child_id, selective_attention, sustained_attention, visual_tracking, working_memory, inhibitory_control, total_score))
    
    return jsonify({'message': '检测数据上传成功'}), 201

@app.route('/api/upload/training', methods=['POST'])
def upload_training():
    data = request.json
    child_id = data.get('child_id')
    training_type = data.get('training_type')
    difficulty = data.get('difficulty')
    accuracy = data.get('accuracy')
    completion_time = data.get('completion_time')
    error_count = data.get('error_count')
    
    if not child_id or not training_type:
        return jsonify({'error': '孩子ID和训练类型不能为空'}), 400
    
    execute_db('''
        INSERT INTO training_data (child_id, training_type, difficulty, accuracy, completion_time, error_count)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (child_id, training_type, difficulty, accuracy, completion_time, error_count))
    
    return jsonify({'message': '训练数据上传成功'}), 201

@app.route('/api/get/detection', methods=['GET'])
def get_detection():
    child_id = request.args.get('child_id')
    
    if not child_id:
        return jsonify({'error': '孩子ID不能为空'}), 400
    
    result = execute_db('''
        SELECT timestamp, selective_attention, sustained_attention, visual_tracking, working_memory, inhibitory_control, total_score
        FROM detection_data
        WHERE child_id = ?
        ORDER BY timestamp DESC
    ''', (child_id,))
    
    data = [{
        'timestamp': row[0],
        'selective_attention': row[1],
        'sustained_attention': row[2],
        'visual_tracking': row[3],
        'working_memory': row[4],
        'inhibitory_control': row[5],
        'total_score': row[6]
    } for row in result]
    
    return jsonify(data), 200

@app.route('/api/get/training', methods=['GET'])
def get_training():
    child_id = request.args.get('child_id')
    
    if not child_id:
        return jsonify({'error': '孩子ID不能为空'}), 400
    
    result = execute_db('''
        SELECT timestamp, training_type, difficulty, accuracy, completion_time, error_count
        FROM training_data
        WHERE child_id = ?
        ORDER BY timestamp DESC
    ''', (child_id,))
    
    data = [{
        'timestamp': row[0],
        'training_type': row[1],
        'difficulty': row[2],
        'accuracy': row[3],
        'completion_time': row[4],
        'error_count': row[5]
    } for row in result]
    
    return jsonify(data), 200

if __name__ == '__main__':
    app.run(
        debug=APP_CONFIG['debug'],
        host=APP_CONFIG['host'],
        port=APP_CONFIG['port']
    )
