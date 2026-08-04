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
        "name": "羅波安",
        "handle": "@rehoboam_king",
        "avatar": "/static/avatars/Rehoboam.svg",
        "bio": "猶大王國國王 👑 | 尋求國家智慧與建言 | 歡迎在下方留言互動！",
        "followers": "3.2萬",
        "following": "180",
        "hashtags": ["#猶大王國", "#聆聽建言", "#國家大事", "#羅波安", "#尋求智慧"]
    },
    "char_2": {
        "id": "char_2",
        "name": "拔示巴",
        "handle": "@bathsheba_queen",
        "avatar": "/static/avatars/bathsheba.svg",
        "bio": "王后與母后 🌸👑 | 耶路撒冷王宮 | 智慧與優雅的生活記趣",
        "followers": "5.8萬",
        "following": "230",
        "hashtags": ["#耶路撒冷王宮", "#母后日常", "#優雅與智慧", "#王宮生活", "#拔示巴"]
    },
    "char_3": {
        "id": "char_3",
        "name": "所羅門王",
        "handle": "@solomon_wise",
        "avatar": "/static/avatars/solomon.svg",
        "bio": "智慧之王 📜👑 | 建造聖殿與箴言詩篇 | 歡迎交流與探索智慧",
        "followers": "15.4萬",
        "following": "300",
        "hashtags": ["#智慧箴言", "#建造聖殿", "#求真理", "#所羅門的智慧", "#傳道書"]
    },
    "char_4": {
        "id": "char_4",
        "name": "約押將軍",
        "handle": "@general_joab",
        "avatar": "/static/avatars/Joab.svg",
        "bio": "大衛王朝大將軍 ⚔️🛡️ | 勇猛統帥與王國衛士 | 軍情與線索回報",
        "followers": "8.7萬",
        "following": "95",
        "hashtags": ["#大衛王朝", "#勇猛統帥", "#守護耶路撒冷", "#軍情線索", "#約押將軍"]
    },
    "char_5": {
        "id": "char_5",
        "name": "示巴女王",
        "handle": "@queen_of_sheba",
        "avatar": "/static/avatars/Sheba.svg",
        "bio": "示巴王國之首 🏛️💎 | 遠道尋求智慧與真理 | 帶來香料與黃金 ✨",
        "followers": "12.1萬",
        "following": "150",
        "hashtags": ["#示巴王國", "#香料與黃金", "#遠道尋求智慧", "#真理之光", "#示巴女王"]
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
            ("char_3", "/static/uploads/sample_clue.svg", "在聖殿入口處發現第一條智慧線索！ 📜✨ #所羅門 #智慧", 99),
            ("char_5", "/static/uploads/sample_card.svg", "帶著香料與寶石遠道而來，尋求真理與智慧！ 💎✨ #示巴女王", 156),
            ("char_4", "/static/uploads/sample_code.svg", "王國防線巡視完畢，全軍警戒守護耶路撒冷 ⚔️🛡️ #約押將軍", 88),
            ("char_1", "/static/uploads/sample_clue.svg", "聆聽眾人的建言，思考王國未來的道路 👑📖 #羅波安", 64),
            ("char_2", "/static/uploads/sample_card.svg", "耶路撒冷王宮的陽光，願智慧與平安臨到大家 🌸✨ #拔示巴", 112)
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
