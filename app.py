import os
import sqlite3
import uuid
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for
from werkzeug.utils import secure_filename
from PIL import Image, ImageOps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'event-ig-secret-key-2026'
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 64 * 1024 * 1024  # 64MB max upload limit
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif', 'heic', 'heif', 'bmp'}

@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({"success": False, "error": "照片檔案過大（超過 64MB 限制），請選擇較小的照片！"}), 413

# 中文版預設活動角色基礎資料
DEFAULT_CHARACTERS = {
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
    }
}

CHARACTERS = dict(DEFAULT_CHARACTERS)

DB_PATH = os.path.join(app.root_path, 'database.db')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_characters():
    """從資料庫獲取所有角色資料，若為空則返回預設值並快取"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT * FROM characters')
        rows = cursor.fetchall()
    except Exception:
        rows = []
    conn.close()

    chars = {}
    for row in rows:
        try:
            tags = json.loads(row['hashtags']) if row['hashtags'] else []
        except Exception:
            tags = [t.strip() for t in (row['hashtags'] or '').split(',') if t.strip()]
        chars[row['id']] = {
            "id": row['id'],
            "name": row['name'],
            "handle": row['handle'],
            "avatar": row['avatar'],
            "bio": row['bio'] or "",
            "followers": row['followers'] or "",
            "following": row['following'] or "",
            "hashtags": tags
        }
    if not chars:
        return dict(DEFAULT_CHARACTERS)
    CHARACTERS.clear()
    CHARACTERS.update(chars)
    return chars

def init_db():
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(app.root_path, 'static', 'avatars'), exist_ok=True)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS characters (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            handle TEXT NOT NULL,
            avatar TEXT NOT NULL,
            bio TEXT,
            followers TEXT,
            following TEXT,
            hashtags TEXT
        )
    ''')
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

    # 如果角色資料庫為空，寫入預設角色
    cursor.execute('SELECT COUNT(*) FROM characters')
    if cursor.fetchone()[0] == 0:
        for cid, cinfo in DEFAULT_CHARACTERS.items():
            cursor.execute(
                '''INSERT INTO characters (id, name, handle, avatar, bio, followers, following, hashtags)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                (
                    cid,
                    cinfo['name'],
                    cinfo['handle'],
                    cinfo['avatar'],
                    cinfo['bio'],
                    cinfo['followers'],
                    cinfo['following'],
                    json.dumps(cinfo['hashtags'], ensure_ascii=False)
                )
            )
        conn.commit()

    # 如果貼文資料庫為空，新增預設展示貼文
    cursor.execute('SELECT COUNT(*) FROM posts')
    count = cursor.fetchone()[0]
    if count == 0:
        sample_posts = [
            ("char_3", "/static/uploads/sample_clue.svg", "在聖殿入口處發現第一條智慧線索！ 📜✨ #所羅門 #智慧", 99),
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
    get_characters()

# --- 頁面路由 ---

@app.route('/')
def index():
    """活動主控中心 / 角色 QR Code 選單"""
    characters = get_characters()
    return render_template('index.html', characters=characters)

@app.route('/post')
def post_page():
    """手機發文頁面"""
    characters = get_characters()
    character_id = request.args.get('character_id', 'char_1')
    character = characters.get(character_id) or next(iter(characters.values()))
    return render_template('post.html', character=character, characters=characters)

@app.route('/screen')
def screen_page():
    """大螢幕 IG 個人檔案牆頁面"""
    characters = get_characters()
    character_id = request.args.get('character_id', 'char_1')
    character = characters.get(character_id) or next(iter(characters.values()))
    return render_template('screen.html', current_character=character, characters=characters)

@app.route('/admin')
def admin_page():
    """人物自我介紹與角色後台管理頁面"""
    characters = get_characters()
    active_id = request.args.get('character_id', 'char_1')
    if active_id not in characters:
        active_id = next(iter(characters.keys()))
    return render_template('admin.html', characters=characters, active_id=active_id)

# --- API 路由 ---

@app.route('/api/characters', methods=['GET'])
def api_get_characters():
    return jsonify({"success": True, "characters": get_characters()})

@app.route('/api/characters/<character_id>', methods=['GET'])
def api_get_character(character_id):
    characters = get_characters()
    if character_id in characters:
        return jsonify({"success": True, "character": characters[character_id]})
    return jsonify({"success": False, "error": "找不到此角色"}), 404

@app.route('/api/characters/<character_id>', methods=['POST', 'PUT'])
def api_update_character(character_id):
    """更新角色資料（自我介紹 Bio、暱稱、帳號、粉絲數、Hashtags）"""
    characters = get_characters()
    if character_id not in characters:
        return jsonify({"success": False, "error": "找不到此角色"}), 404

    data = request.get_json(silent=True)
    if data is None:
        data = request.form.to_dict()

    bio = data.get('bio')
    name = data.get('name')
    handle = data.get('handle')
    followers = data.get('followers')
    following = data.get('following')
    hashtags_raw = data.get('hashtags')

    conn = get_db_connection()
    cursor = conn.cursor()

    updates = []
    params = []

    if bio is not None:
        updates.append("bio = ?")
        params.append(bio.strip())
    if name is not None and name.strip():
        updates.append("name = ?")
        params.append(name.strip())
    if handle is not None and handle.strip():
        updates.append("handle = ?")
        params.append(handle.strip())
    if followers is not None:
        updates.append("followers = ?")
        params.append(followers.strip())
    if following is not None:
        updates.append("following = ?")
        params.append(following.strip())
    if hashtags_raw is not None:
        if isinstance(hashtags_raw, list):
            tags = [str(t).strip() for t in hashtags_raw if str(t).strip()]
        else:
            tags = [t.strip() for t in str(hashtags_raw).replace('\n', ',').replace('，', ',').split(',') if t.strip()]
        tags = [t if t.startswith('#') else f"#{t}" for t in tags]
        updates.append("hashtags = ?")
        params.append(json.dumps(tags, ensure_ascii=False))

    if not updates:
        conn.close()
        return jsonify({"success": False, "error": "未提供要修改的資料"}), 400

    params.append(character_id)
    cursor.execute(f"UPDATE characters SET {', '.join(updates)} WHERE id = ?", params)
    conn.commit()
    conn.close()

    updated_characters = get_characters()
    return jsonify({
        "success": True,
        "message": f"「{updated_characters[character_id]['name']}」的資料已成功更新！",
        "character": updated_characters[character_id]
    })

@app.route('/api/characters/<character_id>/reset', methods=['POST'])
def api_reset_character(character_id):
    """將角色恢復為預設自我介紹與設定"""
    if character_id not in DEFAULT_CHARACTERS:
        return jsonify({"success": False, "error": "找不到此預設角色"}), 404

    default_info = DEFAULT_CHARACTERS[character_id]
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        '''UPDATE characters 
           SET name = ?, handle = ?, avatar = ?, bio = ?, followers = ?, following = ?, hashtags = ?
           WHERE id = ?''',
        (
            default_info['name'],
            default_info['handle'],
            default_info['avatar'],
            default_info['bio'],
            default_info['followers'],
            default_info['following'],
            json.dumps(default_info['hashtags'], ensure_ascii=False),
            character_id
        )
    )
    conn.commit()
    conn.close()

    updated_characters = get_characters()
    return jsonify({
        "success": True,
        "message": f"「{default_info['name']}」已恢復為預設自我介紹！",
        "character": updated_characters[character_id]
    })

@app.route('/api/posts', methods=['GET'])
def api_get_posts():
    characters = get_characters()
    character_id = request.args.get('character_id')
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if character_id and character_id in characters:
        cursor.execute('SELECT * FROM posts WHERE character_id = ? ORDER BY id DESC', (character_id,))
    else:
        cursor.execute('SELECT * FROM posts ORDER BY id DESC')
        
    rows = cursor.fetchall()
    conn.close()
    
    posts = []
    for row in rows:
        char_info = characters.get(row['character_id'], {
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
    characters = get_characters()
    character_id = request.form.get('character_id')
    caption = request.form.get('caption', '').strip()
    
    if not character_id or character_id not in characters:
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
        
        # 使用 Pillow 自動校正手機拍照之 EXIF 方向與最佳化
        try:
            with Image.open(save_path) as img:
                img = ImageOps.exif_transpose(img)
                if img.mode in ('RGBA', 'P') and ext in ('jpg', 'jpeg', 'heic', 'heif'):
                    img = img.convert('RGB')
                img.save(save_path, quality=90, optimize=True)
        except Exception as e:
            app.logger.warning(f"PIL 處理圖片失敗 (保留原圖): {e}")

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
        
    return jsonify({"success": False, "error": "不支援的圖片格式，支援 JPG, PNG, WEBP, GIF, HEIC"}), 400

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
