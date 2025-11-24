
import os
import sqlite3
from datetime import datetime
import json

# 数据库文件路径
DB_PATH = os.path.join(os.path.dirname(__file__), 'app.db')

def create_user(username, email, password_hash, display_name=None):
    """创建新用户"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # 创建新用户
        cursor.execute(
            "INSERT INTO users (username, email, password_hash, display_name) VALUES (?, ?, ?, ?)", 
            (username, email, password_hash, display_name or username)
        )
        user_id = cursor.lastrowid

        # 为新用户创建默认偏好设置
        cursor.execute("INSERT INTO user_preferences (user_id) VALUES (?)", (user_id,))

        conn.commit()
        return user_id
    except sqlite3.IntegrityError as e:
        conn.close()
        raise ValueError(f"用户创建失败: {str(e)}")
    finally:
        conn.close()

def authenticate_user(username, password_hash):
    """验证用户登录"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, username, email, display_name, avatar_url, bio FROM users WHERE username = ? AND password_hash = ?", 
        (username, password_hash)
    )
    result = cursor.fetchone()

    if result:
        # 更新最后登录时间
        cursor.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?", (result[0],))
        conn.commit()

    conn.close()

    if result:
        return {
            'id': result[0],
            'username': result[1],
            'email': result[2],
            'display_name': result[3],
            'avatar_url': result[4],
            'bio': result[5]
        }
    return None

def update_user_profile(user_id, display_name=None, email=None, avatar_url=None, bio=None):
    """更新用户资料"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 构建更新语句
    updates = []
    params = []

    if display_name is not None:
        updates.append("display_name = ?")
        params.append(display_name)

    if email is not None:
        updates.append("email = ?")
        params.append(email)

    if avatar_url is not None:
        updates.append("avatar_url = ?")
        params.append(avatar_url)

    if bio is not None:
        updates.append("bio = ?")
        params.append(bio)

    if not updates:
        conn.close()
        return False

    params.append(user_id)
    cursor.execute(f"UPDATE users SET {', '.join(updates)} WHERE id = ?", params)

    affected_rows = cursor.rowcount
    conn.commit()
    conn.close()
    return affected_rows > 0

def get_user_profile(user_id):
    """获取用户资料"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, username, email, display_name, avatar_url, bio, created_at, last_login FROM users WHERE id = ?", 
        (user_id,)
    )
    result = cursor.fetchone()

    conn.close()

    if result:
        return {
            'id': result[0],
            'username': result[1],
            'email': result[2],
            'display_name': result[3],
            'avatar_url': result[4],
            'bio': result[5],
            'created_at': result[6],
            'last_login': result[7]
        }
    return None

def get_user_preferences(user_id):
    """获取用户偏好设置"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT theme, language, music_source, auto_play, show_lyrics, recommendation_count FROM user_preferences WHERE user_id = ?", 
        (user_id,)
    )
    result = cursor.fetchone()

    conn.close()

    if result:
        return {
            'theme': result[0],
            'language': result[1],
            'music_source': result[2],
            'auto_play': bool(result[3]),
            'show_lyrics': bool(result[4]),
            'recommendation_count': result[5]
        }
    return None

def update_user_preferences(user_id, preferences):
    """更新用户偏好设置"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 构建更新语句
    updates = []
    params = []

    if 'theme' in preferences:
        updates.append("theme = ?")
        params.append(preferences['theme'])

    if 'language' in preferences:
        updates.append("language = ?")
        params.append(preferences['language'])

    if 'music_source' in preferences:
        updates.append("music_source = ?")
        params.append(preferences['music_source'])

    if 'auto_play' in preferences:
        updates.append("auto_play = ?")
        params.append(1 if preferences['auto_play'] else 0)

    if 'show_lyrics' in preferences:
        updates.append("show_lyrics = ?")
        params.append(1 if preferences['show_lyrics'] else 0)

    if 'recommendation_count' in preferences:
        updates.append("recommendation_count = ?")
        params.append(preferences['recommendation_count'])

    if not updates:
        conn.close()
        return False

    params.append(user_id)
    cursor.execute(f"UPDATE user_preferences SET {', '.join(updates)} WHERE user_id = ?", params)

    affected_rows = cursor.rowcount
    conn.commit()
    conn.close()
    return affected_rows > 0
