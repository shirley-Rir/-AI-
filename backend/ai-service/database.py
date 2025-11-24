
import os
import sqlite3
from datetime import datetime
import json

# 数据库文件路径
DB_PATH = os.path.join(os.path.dirname(__file__), 'app.db')

def init_db():
    """初始化数据库"""
    # 确保目录存在
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 创建用户表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE,
        password_hash TEXT,
        display_name TEXT,
        avatar_url TEXT,
        bio TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP
    )
    """)

    # 创建推荐历史表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS recommendation_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        type TEXT NOT NULL,  -- 'text' 或 'image'
        input_text TEXT,
        image_base64 TEXT,
        image_url TEXT,  -- COS图片URL
        songs TEXT,  -- JSON格式的歌曲列表
        analysis TEXT,  -- JSON格式的分析结果
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    """)

    # 创建收藏表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS favorites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        history_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (history_id) REFERENCES recommendation_history (id)
    )
    """)
    
    # 创建用户偏好设置表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_preferences (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE,
        theme TEXT DEFAULT 'light',
        language TEXT DEFAULT 'zh-CN',
        music_source TEXT DEFAULT 'netease',
        auto_play BOOLEAN DEFAULT 0,
        show_lyrics BOOLEAN DEFAULT 1,
        recommendation_count INTEGER DEFAULT 5,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    """)

    conn.commit()
    conn.close()

def get_or_create_user(username, email=None):
    """获取或创建用户"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 尝试获取用户
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()

    if result:
        user_id = result[0]
    else:
        # 创建新用户
        cursor.execute("INSERT INTO users (username, email, password_hash, display_name) VALUES (?, ?, ?, ?)", (username, email, "", username))
        user_id = cursor.lastrowid

    conn.commit()
    conn.close()
    return user_id

def save_recommendation(user_id, rec_type, input_text, image_base64, songs, analysis, image_url=None):
    """保存推荐记录"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 确保歌曲对象包含封面信息
    formatted_songs = []
    if songs:
        for song in songs:
            # 处理封面信息 - 确保有封面
            cover = song.get('cover', '')
            if not cover and song.get('album'):
                cover = song['album'].get('picUrl', '')
            if not cover:
                cover = 'https://p3.music.126.net/SyqjxPvTbK4Jt_lWjMZgKg==/109951165633973637.jpg'

            # 处理艺术家信息 - 确保有艺术家信息
            artist = song.get('artist', '')
            if not artist and song.get('artists'):
                artists = song['artists']
                if isinstance(artists, list) and artists:
                    artist = ', '.join([a.get('name', '') for a in artists])
                elif isinstance(artists, str):
                    artist = artists

            # 获取预览链接
            preview_url = song.get('preview_url', '')
            if not preview_url and song.get('url'):
                preview_url = song.get('url', '')

            formatted_song = {
                'id': song.get('id', ''),
                'name': song.get('name', ''),
                'artist': artist,
                'cover': cover,
                'preview_url': preview_url
            }
            formatted_songs.append(formatted_song)

    # 将歌曲列表和分析结果转为JSON字符串
    songs_json = json.dumps(formatted_songs) if formatted_songs else None
    analysis_json = json.dumps(analysis) if analysis else None

    cursor.execute("""
    INSERT INTO recommendation_history 
    (user_id, type, input_text, image_base64, songs, analysis, image_url) 
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, rec_type, input_text, image_base64, songs_json, analysis_json, image_url))

    history_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return history_id

def get_user_history(user_id, limit=20, offset=0):
    """获取用户的历史记录"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id, type, input_text, image_base64, image_url, songs, analysis, created_at 
    FROM recommendation_history 
    WHERE user_id = ? 
    ORDER BY created_at DESC 
    LIMIT ? OFFSET ?
    """, (user_id, limit, offset))

    records = cursor.fetchall()
    conn.close()
    print(f"从数据库获取到 {len(records)} 条历史记录，用户ID: {user_id}")
    # 转换为字典列表并解析JSON字段
    history = []
    for record in records:
        # record[4]现在是image_url，record[5]是songs
        image_url = record[4]
        songs = json.loads(record[5]) if record[5] else []
        # 为每首歌曲添加显示信息
        formatted_songs = []
        for song in songs:
            # 处理封面信息 - 支持多种可能的字段名
            cover = song.get('cover', '')
            if not cover and song.get('album'):
                cover = song['album'].get('picUrl', '')
            if not cover:
                cover = 'https://p3.music.126.net/SyqjxPvTbK4Jt_lWjMZgKg==/109951165633973637.jpg'

            # 处理艺术家信息 - 支持多种可能的字段名
            artist = song.get('artist', '')
            if not artist and song.get('artists'):
                artists = song['artists']
                if isinstance(artists, list) and artists:
                    artist = ', '.join([a.get('name', '') for a in artists])
                elif isinstance(artists, str):
                    artist = artists

            # 获取预览链接
            preview_url = song.get('preview_url', '')
            if not preview_url and song.get('url'):
                preview_url = song.get('url', '')
            if not preview_url:
                # 如果没有预览链接，尝试通过歌曲ID获取
                song_id = song.get('id', '')
                if song_id:
                    # 这里可以调用音乐服务的API获取预览链接
                    # 为了避免过多API调用，暂时使用空字符串
                    preview_url = ''

            formatted_song = {
                'id': song.get('id', ''),
                'name': song.get('name', ''),
                'artist': artist,
                'cover': cover,
                'preview_url': preview_url
            }
            formatted_songs.append(formatted_song)
            
        # 将时间转换为东八区时间
        # record[6]现在是created_at，record[3]是image_base64，record[4]是image_url，record[5]是analysis
        timestamp = record[7]
        if timestamp:
            # 如果是字符串格式的时间，先解析为datetime对象
            if isinstance(timestamp, str):
                try:
                    timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                except:
                    pass

            # 转换为东八区时间
            if isinstance(timestamp, datetime):
                from datetime import timezone, timedelta
                # 定义东八区时区
                beijing_tz = timezone(timedelta(hours=8))

                # 如果时间没有时区信息，假设为UTC
                if timestamp.tzinfo is None:
                    timestamp = timestamp.replace(tzinfo=timezone.utc)

                # 转换为东八区时间
                timestamp = timestamp.astimezone(beijing_tz)
                # 格式化为更友好的显示格式
                timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S')

        # 优先使用COS图片URL，如果没有则使用base64图片
        image_preview = None
        if image_url:
            image_preview = image_url
        elif record[3]:  # image_base64
            image_preview = f"data:image/jpeg;base64,{record[3]}"

        history_item = {
            'id': record[0],
            'type': record[1],
            'input': record[2],
            'imagePreview': image_preview,
            'imageUrl': image_url,  # 添加COS URL字段
            'songs': formatted_songs,
            'analysis': json.loads(record[6]) if record[6] else {},
            'timestamp': timestamp,
            'cover': formatted_songs[0]['cover'] if formatted_songs else None,
            'title': formatted_songs[0]['name'] if formatted_songs else '',
            'artist': formatted_songs[0]['artist'] if formatted_songs else ''
        }
        history.append(history_item)
    print(f"处理后的历史记录: {history}")

    return history

def get_history_count(user_id):
    """获取用户历史记录总数"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM recommendation_history WHERE user_id = ?", (user_id,))
    count = cursor.fetchone()[0]

    conn.close()
    return count

def add_to_favorites(user_id, history_id):
    """添加历史记录到收藏"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 检查是否已收藏
    cursor.execute("SELECT id FROM favorites WHERE user_id = ? AND history_id = ?", (user_id, history_id))
    if cursor.fetchone():
        conn.close()
        return False  # 已收藏

    # 添加到收藏
    cursor.execute("INSERT INTO favorites (user_id, history_id) VALUES (?, ?)", (user_id, history_id))
    conn.commit()
    conn.close()
    return True

def remove_from_favorites(user_id, history_id):
    """从收藏中移除历史记录"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM favorites WHERE user_id = ? AND history_id = ?", (user_id, history_id))
    affected_rows = cursor.rowcount

    conn.commit()
    conn.close()
    return affected_rows > 0

def get_favorites(user_id, limit=20, offset=0):
    """获取用户收藏的历史记录"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT h.id, h.type, h.input_text, h.image_base64, h.image_url, h.songs, h.analysis, h.created_at 
    FROM recommendation_history h
    JOIN favorites f ON h.id = f.history_id
    WHERE f.user_id = ? 
    ORDER BY f.created_at DESC 
    LIMIT ? OFFSET ?
    """, (user_id, limit, offset))

    records = cursor.fetchall()
    conn.close()

    # 转换为字典列表并解析JSON字段
    favorites = []
    for record in records:
        # 优先使用COS图片URL，如果没有则使用base64图片
        image_preview = None
        image_url = record[4]
        if image_url:
            image_preview = image_url
        elif record[3]:  # image_base64
            image_preview = f"data:image/jpeg;base64,{record[3]}"

        fav_item = {
            'id': record[0],
            'type': record[1],
            'input': record[2],
            'imagePreview': image_preview,
            'imageUrl': image_url,  # 添加COS URL字段
            'songs': json.loads(record[5]) if record[5] else [],
            'analysis': json.loads(record[6]) if record[6] else {},
            'timestamp': record[7]
        }
        favorites.append(fav_item)

    return favorites

def search_history(user_id, query, limit=20, offset=0):
    """搜索用户的历史记录"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 使用LIKE进行模糊匹配
    search_pattern = f"%{query}%"
    cursor.execute("""
    SELECT id, type, input_text, image_base64, image_url, songs, analysis, created_at 
    FROM recommendation_history 
    WHERE user_id = ? AND (
        input_text LIKE ? OR
        type LIKE ? OR
        songs LIKE ?
    )
    ORDER BY created_at DESC 
    LIMIT ? OFFSET ?
    """, (user_id, search_pattern, search_pattern, search_pattern, limit, offset))

    records = cursor.fetchall()
    conn.close()

    # 转换为字典列表并解析JSON字段
    results = []
    for record in records:
        result_item = {
            'id': record[0],
            'type': record[1],
            'input': record[2],
            'imagePreview': f"data:image/jpeg;base64,{record[3]}" if record[3] else None,
            'songs': json.loads(record[4]) if record[4] else [],
            'analysis': json.loads(record[5]) if record[5] else {},
            'timestamp': record[6]
        }
        results.append(result_item)

    return results

def delete_history(user_id, history_id):
    """删除指定的历史记录"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 先删除相关的收藏记录
    cursor.execute("DELETE FROM favorites WHERE history_id = ?", (history_id,))

    # 删除历史记录
    cursor.execute("DELETE FROM recommendation_history WHERE id = ? AND user_id = ?", (history_id, user_id))
    affected_rows = cursor.rowcount

    conn.commit()
    conn.close()
    return affected_rows > 0

def clear_user_history(user_id):
    """清空用户的所有历史记录"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 删除用户的所有收藏记录
    cursor.execute("DELETE FROM favorites WHERE user_id = ?", (user_id,))

    # 删除用户的所有历史记录
    cursor.execute("DELETE FROM recommendation_history WHERE user_id = ?", (user_id,))
    affected_rows = cursor.rowcount

    conn.commit()
    conn.close()
    return affected_rows > 0

# 初始化数据库
if __name__ == "__main__":
    init_db()
    print("数据库初始化完成")
