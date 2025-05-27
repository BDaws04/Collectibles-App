from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import sqlite3
import uuid
from utils import valid_image
import json

UPLOAD_FOLDER = 'backend/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

DATABASE_FILE = "data/items.db"
if not os.path.exists(DATABASE_FILE):
    os.makedirs(os.path.dirname(DATABASE_FILE), exist_ok=True)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
CORS(app)

def init_db():
    with sqlite3.connect(DATABASE_FILE) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                tags TEXT NOT NULL,
                image_path TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

init_db()

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400
    
    if not all(field in request.form for field in ('title', 'description', 'tags')):
        return jsonify({'error': 'Missing title, description, or tags'}), 400
    
    image = request.files['image']
    title = request.form['title']
    description = request.form['description']
    tags = [tag.strip() for tag in request.form['tags'].split(',')]


    if image.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if not valid_image(image.filename):
        return jsonify({'error': 'Invalid image file type'}), 400
    
    unique_name = f"{uuid.uuid4().hex}_{secure_filename(image.filename)}"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
    image.save(file_path)

    with sqlite3.connect(DATABASE_FILE) as conn:
        conn.execute('''
            INSERT INTO items (title, description, tags, image_path)
            VALUES (?, ?, ?, ?)
        ''', (title, description, json.dumps(tags), file_path))

    return jsonify({
        'message': 'File uploaded successfully',
        'filename': unique_name
    }), 201

@app.route('/items', methods=['GET'])
def get_items():
    with sqlite3.connect(DATABASE_FILE) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute('SELECT * FROM items ORDER BY created_at DESC')
        items = cursor.fetchall()

    items_list = []
    for item in items:
        items_list.append({
            'id': item['id'],
            'title': item['title'],
            'description': item['description'],
            'tags': json.loads(item['tags']),
            'image_path': item['image_path'],
            'created_at': item['created_at']
        })

    return jsonify(items_list), 200

@app.route('/items/<int:item_id>', methods=['GET'])
def get_item(item_id):
    with sqlite3.connect(DATABASE_FILE) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute('SELECT * FROM items WHERE id = ?', (item_id,))
        item = cursor.fetchone()

    if item is None:
        return jsonify({'error': 'Item not found'}), 404

    return jsonify({
        'id': item['id'],
        'title': item['title'],
        'description': item['description'],
        'tags': json.loads(item['tags']),
        'image_path': item['image_path'],
        'created_at': item['created_at']
    }), 200

if __name__ == '__main__':
    app.run(debug=True)