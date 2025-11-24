
import os
import jwt
import hashlib
import uuid
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app
from database import get_or_create_user

# JWT密钥，实际部署时应从环境变量获取
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your_secret_key_change_in_production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_DELTA = timedelta(days=7)  # Token有效期7天

def hash_password(password):
    """对密码进行哈希处理"""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def generate_token(user_id, username):
    """生成JWT令牌"""
    payload = {
        'user_id': user_id,
        'username': username,
        'exp': datetime.utcnow() + JWT_EXPIRATION_DELTA,
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def verify_token(token):
    """验证JWT令牌"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None  # Token过期
    except jwt.InvalidTokenError:
        return None  # Token无效

def auth_required(f):
    """认证装饰器，用于需要登录的路由"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        # 从请求头获取token
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]  # Bearer <token>
            except IndexError:
                return jsonify({'success': False, 'message': '无效的认证令牌格式'}), 401

        if not token:
            return jsonify({'success': False, 'message': '缺少认证令牌'}), 401

        # 验证token
        payload = verify_token(token)
        if not payload:
            return jsonify({'success': False, 'message': '认证令牌无效或已过期'}), 401

        # 将用户信息添加到请求上下文
        if payload:
            request.current_user_id = payload['user_id']
            request.current_username = payload['username']

        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    """获取当前登录用户信息"""
    if hasattr(request, 'current_user_id'):
        return {
            'id': request.current_user_id,
            'username': request.current_username
        }
    return None
