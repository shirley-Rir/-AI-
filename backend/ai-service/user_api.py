
from flask import Blueprint, request, jsonify
from auth import hash_password, generate_token, verify_token, auth_required
from user_db import create_user, authenticate_user, update_user_profile, get_user_profile, get_user_preferences, update_user_preferences

# 创建用户API蓝图
user_bp = Blueprint('user', __name__, url_prefix='/api/user')

@user_bp.route('/register', methods=['POST'])
def register():
    """用户注册"""
    try:
        data = request.get_json()

        # 验证必填字段
        if not data or not data.get('username') or not data.get('password'):
            return jsonify({
                'success': False,
                'message': '用户名和密码不能为空'
            }), 400

        username = data.get('username').strip()
        email = data.get('email', '').strip()
        password = data.get('password')
        display_name = data.get('display_name', '').strip() or username

        # 验证用户名长度
        if len(username) < 3:
            return jsonify({
                'success': False,
                'message': '用户名至少需要3个字符'
            }), 400

        # 验证密码长度
        if len(password) < 6:
            return jsonify({
                'success': False,
                'message': '密码至少需要6个字符'
            }), 400

        # 对密码进行哈希处理
        password_hash = hash_password(password)

        # 创建用户
        try:
            user_id = create_user(username, email, password_hash, display_name)

            # 生成JWT令牌
            token = generate_token(user_id, username)

            return jsonify({
                'success': True,
                'message': '注册成功',
                'user': {
                    'id': user_id,
                    'username': username,
                    'email': email,
                    'display_name': display_name
                },
                'token': token
            })
        except ValueError as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 400
    except Exception as e:
        print(f"注册错误: {str(e)}")
        return jsonify({
            'success': False,
            'message': '注册失败，请稍后再试'
        }), 500

@user_bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    try:
        data = request.get_json()

        # 验证必填字段
        if not data or not data.get('username') or not data.get('password'):
            return jsonify({
                'success': False,
                'message': '用户名和密码不能为空'
            }), 400

        username = data.get('username').strip()
        password = data.get('password')

        # 对密码进行哈希处理
        password_hash = hash_password(password)

        # 验证用户
        user = authenticate_user(username, password_hash)

        if not user:
            return jsonify({
                'success': False,
                'message': '用户名或密码错误'
            }), 401

        # 生成JWT令牌
        token = generate_token(user['id'], user['username'])

        return jsonify({
            'success': True,
            'message': '登录成功',
            'user': user,
            'token': token
        })
    except Exception as e:
        print(f"登录错误: {str(e)}")
        return jsonify({
            'success': False,
            'message': '登录失败，请稍后再试'
        }), 500

@user_bp.route('/profile', methods=['GET'])
@auth_required
def get_profile():
    """获取用户资料"""
    try:
        user_id = request.current_user_id

        profile = get_user_profile(user_id)
        if not profile:
            return jsonify({
                'success': False,
                'message': '用户不存在'
            }), 404

        # 获取用户偏好设置
        preferences = get_user_preferences(user_id)
        if preferences:
            profile['preferences'] = preferences

        return jsonify({
            'success': True,
            'profile': profile
        })
    except Exception as e:
        print(f"获取用户资料错误: {str(e)}")
        return jsonify({
            'success': False,
            'message': '获取用户资料失败'
        }), 500

@user_bp.route('/profile', methods=['PUT'])
@auth_required
def update_profile():
    """更新用户资料"""
    try:
        user_id = request.current_user_id
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'message': '请提供要更新的资料'
            }), 400

        # 更新用户资料
        success = update_user_profile(
            user_id,
            display_name=data.get('display_name'),
            email=data.get('email'),
            avatar_url=data.get('avatar_url'),
            bio=data.get('bio')
        )

        if not success:
            return jsonify({
                'success': False,
                'message': '没有需要更新的资料'
            }), 400

        # 获取更新后的用户资料
        profile = get_user_profile(user_id)

        return jsonify({
            'success': True,
            'message': '资料更新成功',
            'profile': profile
        })
    except Exception as e:
        print(f"更新用户资料错误: {str(e)}")
        return jsonify({
            'success': False,
            'message': '更新用户资料失败'
        }), 500

@user_bp.route('/preferences', methods=['GET'])
@auth_required
def get_preferences():
    """获取用户偏好设置"""
    try:
        user_id = request.current_user_id

        preferences = get_user_preferences(user_id)
        if not preferences:
            return jsonify({
                'success': False,
                'message': '用户偏好设置不存在'
            }), 404

        return jsonify({
            'success': True,
            'preferences': preferences
        })
    except Exception as e:
        print(f"获取用户偏好设置错误: {str(e)}")
        return jsonify({
            'success': False,
            'message': '获取用户偏好设置失败'
        }), 500

@user_bp.route('/preferences', methods=['PUT'])
@auth_required
def update_preferences():
    """更新用户偏好设置"""
    try:
        user_id = request.current_user_id
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'message': '请提供要更新的偏好设置'
            }), 400

        # 更新用户偏好设置
        success = update_user_preferences(user_id, data)

        if not success:
            return jsonify({
                'success': False,
                'message': '没有需要更新的偏好设置'
            }), 400

        # 获取更新后的用户偏好设置
        preferences = get_user_preferences(user_id)

        return jsonify({
            'success': True,
            'message': '偏好设置更新成功',
            'preferences': preferences
        })
    except Exception as e:
        print(f"更新用户偏好设置错误: {str(e)}")
        return jsonify({
            'success': False,
            'message': '更新用户偏好设置失败'
        }), 500

@user_bp.route('/verify-token', methods=['POST'])
def verify_token_endpoint():
    """验证JWT令牌有效性"""
    try:
        data = request.get_json()

        if not data or not data.get('token'):
            return jsonify({
                'success': False,
                'message': '缺少令牌'
            }), 400

        token = data.get('token')
        payload = verify_token(token)

        if not payload:
            return jsonify({
                'success': False,
                'message': '令牌无效或已过期'
            }), 401

        # 获取用户资料
        profile = get_user_profile(payload['user_id'])

        return jsonify({
            'success': True,
            'message': '令牌有效',
            'user': profile
        })
    except Exception as e:
        print(f"验证令牌错误: {str(e)}")
        return jsonify({
            'success': False,
            'message': '验证令牌失败'
        }), 500
