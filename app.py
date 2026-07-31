import os
import sqlite3
import uuid
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'event-ig-secret-key-2026'
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload limit
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}

# 中文版預設活動角色資料
CHARACTERS = {
    "char_1": {
        "id": "char_1",
        "name": "福爾摩斯偵探",
        "handle": "@sherlock_detective",
        "avatar": "/static/avatars/detective.svg",
        "bio": "破解活動終極懸案... 🕵️‍♂️🔍 | 貝克街 221B | 在下方留下你的線索！",
        "followers": "1.2萬",
        "following": "142"
    },
    "char_2": {
        "id": "char_2",
        "name": "怪盜基德",
        "handle": "@phantom_thief_x",
        "avatar": "/static/avatars/thief.svg",
        "bio": "能抓到我嗎？ 🃏✨ | 偷走心靈與月光寶物 | 月光之下 🌙",
        "followers": "9.8萬",
        "following": "0"
    },
    "char_3": {
        "id": "char_3",
        "name": "特工 V",
        "handle": "@v_cyber_agent",
        "avatar": "/static/avatars/hacker.svg",
        "bio": "主機防線已突破。 💻⚡ | 新東京 2099 | 請在貼文中回報加密情報",
        "followers": "4.5萬",
        "following": "512"
    }
}

DB_PATH = os.path.join(app.root_path, 'database.db')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(app.root_path, 'static', 'avatars'), exist_ok=True)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            character_id TEXT NOT NULL,
            image_url TEXT NOT NULL,
            caption TEXT,
            likes INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()

    # 如果資料庫為空，新增預設展示貼文
    cursor.execute('SELECT COUNT(*) FROM posts')
    count = cursor.fetchone()[0]
    if count == 0:
        sample_posts = [
            ("char_1", "/static/uploads/sample_clue.svg", "在主舞台入口處發現第一條關鍵線索！ #偵探 #活動線索", 42),
            ("char_2", "/static/uploads/sample_card.svg", "預告函已經發出，你們能在時間內解開嗎？ 🃏✨ #怪盜基德", 128),
            ("char_3", "/static/uploads/sample_code.svg", "加密網路已上線，正在掃描全場 QR Code 數據 📡 #賽博特工", 89)
        ]
        for char_id, img, cap, likes in sample_posts:
            cursor.execute(
                'INSERT INTO posts (character_id, image_url, caption, likes) VALUES (?, ?, ?, ?)',
                (char_id, img, cap, likes)
            )
        conn.commit()
    conn.close()

with app.app_context():
    init_db()

# --- 頁面路由 ---

@app.route('/')
def index():
    """活動主控中心 / 角色 QR Code 選單"""
    return render_template('index.html', characters=CHARACTERS)

@app.route('/post')
def post_page():
    """手機發文頁面"""
    character_id = request.args.get('character_id', 'char_1')
    character = CHARACTERS.get(character_id, CHARACTERS['char_1'])
    return render_template('post.html', character=character, characters=CHARACTERS)

@app.route('/screen')
def screen_page():
    """大螢幕 IG 個人檔案牆頁面"""
    character_id = request.args.get('character_id', 'char_1')
    character = CHARACTERS.get(character_id, CHARACTERS['char_1'])
    return render_template('screen.html', current_character=character, characters=CHARACTERS)

# --- API 路由 ---

@app.route('/api/characters', methods=['GET'])
def api_get_characters():
    return jsonify({"success": True, "characters": CHARACTERS})

@app.route('/api/posts', methods=['GET'])
def api_get_posts():
    character_id = request.args.get('character_id')
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if character_id and character_id in CHARACTERS:
        cursor.execute('SELECT * FROM posts WHERE character_id = ? ORDER BY id DESC', (character_id,))
    else:
        cursor.execute('SELECT * FROM posts ORDER BY id DESC')
        
    rows = cursor.fetchall()
    conn.close()
    
    posts = []
    for row in rows:
        char_info = CHARACTERS.get(row['character_id'], {
            "name": "未知角色",
            "avatar": "/static/avatars/default.svg",
            "handle": "@unknown"
        })
        posts.append({
            "id": row['id'],
            "character_id": row['character_id'],
            "character_name": char_info['name'],
            "character_avatar": char_info['avatar'],
            "character_handle": char_info['handle'],
            "image_url": row['image_url'],
            "caption": row['caption'],
            "likes": row['likes'],
            "created_at": row['created_at']
        })
        
    return jsonify({
        "success": True,
        "count": len(posts),
        "posts": posts
    })

@app.route('/api/posts', methods=['POST'])
def api_create_post():
    character_id = request.form.get('character_id')
    caption = request.form.get('caption', '').strip()
    
    if not character_id or character_id not in CHARACTERS:
        return jsonify({"success": False, "error": "無效的角色 ID"}), 400
        
    if 'image' not in request.files:
        return jsonify({"success": False, "error": "請上傳圖片檔案"}), 400
        
    file = request.files['image']
    if file.filename == '':
        return jsonify({"success": False, "error": "尚未選擇圖片"}), 400
        
    if file and allowed_file(file.filename):
        ext = file.filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(save_path)
        
        image_url = f"/static/uploads/{unique_filename}"
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO posts (character_id, image_url, caption) VALUES (?, ?, ?)',
            (character_id, image_url, caption)
        )
        conn.commit()
        post_id = cursor.lastrowid
        conn.close()
        
        return jsonify({
            "success": True,
            "message": "貼文發布成功！",
            "post": {
                "id": post_id,
                "character_id": character_id,
                "image_url": image_url,
                "caption": caption,
                "likes": 0
            }
        })
        
    return jsonify({"success": False, "error": "不支援的圖片格式，僅支援 JPG, PNG, WEBP, GIF"}), 400

@app.route('/api/posts/<int:post_id>/like', methods=['POST'])
def api_like_post(post_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE posts SET likes = likes + 1 WHERE id = ?', (post_id,))
    conn.commit()
    cursor.execute('SELECT likes FROM posts WHERE id = ?', (post_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return jsonify({"success": True, "likes": row['likes']})
    return jsonify({"success": False, "error": "找不到貼文"}), 404

@app.route('/api/posts/<int:post_id>', methods=['DELETE'])
def api_delete_post(post_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT image_url FROM posts WHERE id = ?', (post_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return jsonify({"success": False, "error": "貼文不存在"}), 404
        
    image_url = row['image_url']
    cursor.execute('DELETE FROM posts WHERE id = ?', (post_id,))
    conn.commit()
    conn.close()
    
    # 嘗試刪除實體上傳檔案 (如果不是預設範例檔)
    if image_url.startswith('/static/uploads/') and not ('sample_' in image_url):
        filename = os.path.basename(image_url)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                app.logger.error(f"刪除圖片檔案失敗: {e}")
                
    return jsonify({"success": True, "message": "貼文已成功刪除！"})

if __name__ == '__main__':
    print("啟動 Instagram 活動互動系統...")
    print("請在瀏覽器開啟 http://127.0.0.1:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
