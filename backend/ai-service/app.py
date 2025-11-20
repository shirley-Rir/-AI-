import os
import json
import base64
import requests
import datetime
import re
import random
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from PIL import Image
import io

# 加载环境变量
load_dotenv()

app = Flask(__name__)
CORS(app)  # 启用跨域支持

# 配置
MUSIC_SERVICE_URL = os.getenv('MUSIC_SERVICE_URL', 'http://localhost:3001')
NETEASE_API_URL = os.getenv('NETEASE_API_URL', 'http://localhost:3000')
QWEN_API_KEY = os.getenv('QWEN_API_KEY', 'your_qwen_api_key')

# 存储推荐历史的简单内存存储（生产环境应使用数据库）
recommendation_history = []

@app.route('/api/recommend/text', methods=['POST'])
def text_recommend():
    """基于文本推荐歌曲"""
    try:
        # 更健壮地解析 JSON：先尝试安全解析，若失败则记录原始请求体并返回 400
        data = None
        try:
            data = request.get_json(silent=True)
        except Exception as _e:
            data = None

        if not data:
            raw_body = request.get_data(as_text=True)
            print(f"解析请求 JSON 失败或为空，原始请求体: {raw_body}")
            return jsonify({'success': False, 'message': '请求体不是合法的 JSON 或为空', 'raw': raw_body}), 400

        text = data.get('text', '')

        if not text:
            return jsonify({'success': False, 'message': '文本内容不能为空'}), 400

        # 流程调整：不再把用户原始输入优先当作搜索关键词直接返回。
        # 现在的流程：先调用大模型生成最多5条推荐（模型独立工作），
        # 然后对模型返回的每条推荐仅用歌曲名去调用音乐服务搜索并取第一条匹配。

        # 1. 使用通义千问分析文本，提取场景/情感标签
        scene_emotion = analyze_text(text)

        # 2. 基于场景/情感标签生成推荐歌曲关键词（作为备用）
        keywords = generate_keywords(scene_emotion)

        # 3. 调用大模型生成5首候选歌曲（JSON格式）
        try:
                model_recs_json = call_recommender_model(text)
                try:
                    model_recs_obj = json.loads(model_recs_json) if isinstance(model_recs_json, str) else model_recs_json
                except Exception:
                    # 如果解析失败，将原始字符串作为候选处理
                    model_recs_obj = model_recs_json
        except Exception as e:
            print(f"调用模型生成推荐失败: {e}")
            model_recs_obj = { 'analysis': {}, 'recommendations': [] }

        # 4. 对模型返回的每一首候选（recommendations字段），调用音乐服务/网易云搜索以获取真实歌曲条目
        # 归一化模型返回，确保是一个推荐条目列表
        model_recs_list = normalize_model_recommendations(model_recs_obj)
        matched_songs = []
        for rec in model_recs_list:
            title = (rec.get('title') or '').strip()
            artist = (rec.get('artist') or '').strip()
            if not title:
                continue
            # 首先仅用歌名进行搜索（用户要求），如果未命中，再尝试用 '歌名 歌手' 组合
            search_results = search_songs([title])
            if not search_results and artist:
                search_results = search_songs([f"{title} {artist}"])
            if search_results:
                matched_songs.append(search_results[0])

        # 5. 获取匹配歌曲的详细信息
        song_details = get_song_details(matched_songs) if matched_songs else []

        # 5b. 无论是否匹配到真实歌曲，都把模型返回（原始与归一化后的）包含在响应中，
        # 以便前端独立展示模型推荐列表。
        try:
            model_raw_str = model_recs_json if isinstance(model_recs_json, str) else json.dumps(model_recs_json, ensure_ascii=False)
        except Exception:
            model_raw_str = str(model_recs_json)

        if not song_details:
            print("模型推荐的歌曲未能在音乐服务中匹配到真实条目，返回模型建议供参考")
            # 不视为错误，仍返回模型建议（前端可选择只展示模型推荐）
            return jsonify({
                'success': True,
                'message': '未能在音乐服务中匹配到模型推荐，返回模型建议供参考',
                'songs': [],
                'model_recommendations': model_recs_obj,
                'model_raw': model_raw_str,
                'analysis': scene_emotion,
                'keywords': keywords
            }), 200

        # 6. 保存推荐历史（保存实际匹配到的歌曲）
        save_recommendation_history('text', text, None, song_details)

        return jsonify({
            'success': True,
            'songs': song_details,
            'model_recommendations': model_recs_obj,
            'model_raw': model_raw_str,
            'analysis': scene_emotion,
            'keywords': keywords
        })
    except Exception as e:
        print(f"文本推荐错误: {str(e)}")
        return jsonify({'success': False, 'message': '服务器错误，请稍后再试'}), 500

@app.route('/api/recommend/image', methods=['POST'])
def image_recommend():
    """基于图片推荐歌曲"""
    try:
        # 检查是否有文件上传
        if 'image' not in request.files:
            return jsonify({'success': False, 'message': '没有上传图片'}), 400

        file = request.files['image']

        if file.filename == '':
            return jsonify({'success': False, 'message': '没有选择图片'}), 400

        # 读取图片并转换为base64（用于显示在历史记录中）
        image_bytes = file.read()
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')

        # 1. 使用通义千问分析图片，提取场景/情感标签
        scene_emotion = analyze_image(image_bytes)

        # 2. 使用模型生成 5 条候选推荐（将图像分析结果作为模型输入）
        model_input = scene_emotion.get('description', '')
        # 组合 tags 以提供更丰富的上下文
        tags = scene_emotion.get('tags', []) or []
        if tags:
            model_input = model_input + ' ' + ' '.join(tags)

        try:
            model_recs_json = call_recommender_model(model_input)
            try:
                model_recs_obj = json.loads(model_recs_json) if isinstance(model_recs_json, str) else model_recs_json
            except Exception:
                model_recs_obj = model_recs_json
        except Exception as e:
            print(f"调用模型生成图片推荐失败: {e}")
            model_recs_obj = { 'analysis': {}, 'recommendations': [] }

        # 3. 归一化模型返回并逐条只用歌曲名搜索（每次只取第一条匹配）
        model_recs_list = normalize_model_recommendations(model_recs_obj)
        matched_songs = []
        for rec in model_recs_list:
            title = (rec.get('title') or '').strip()
            artist = (rec.get('artist') or '').strip()
            if not title:
                matched_songs.append(None)
                continue

            search_results = search_songs([title])
            if not search_results and artist:
                search_results = search_songs([f"{title} {artist}"])

            if search_results:
                # 只取第一条匹配
                matched_songs.append(search_results[0])
            else:
                matched_songs.append(None)

        # 4. 获取匹配歌曲的详细信息（仅对存在匹配的ID调用 detail）
        existing = [s for s in matched_songs if s]
        song_details = get_song_details(existing) if existing else []

        # 将 song_details 按照 model_recs_list 顺序映射回每条推荐（保持一一对应）
        id_map = {}
        for sd in song_details:
            sid = str(sd.get('id') or sd.get('songId') or '')
            if sid:
                id_map[sid] = sd

        final_songs = []
        for s in matched_songs:
            if not s:
                final_songs.append(None)
            else:
                sid = str(s.get('id') or s.get('songId') or '')
                if sid and sid in id_map:
                    final_songs.append(id_map[sid])
                else:
                    final_songs.append(s)

        # 5. 保存推荐历史（保存实际匹配到的歌曲）
        save_recommendation_history('image', None, image_base64, [fs for fs in final_songs if fs])

        return jsonify({
            'success': True,
            'songs': [fs for fs in final_songs if fs],
            'model_recommendations': model_recs_obj,
            'model_raw': model_recs_json,
            'analysis': scene_emotion
        })
    except Exception as e:
        print(f"图片推荐错误: {str(e)}")
        return jsonify({'success': False, 'message': '服务器错误，请稍后再试'}), 500


@app.route('/api/recommend/model-only', methods=['POST'])
def model_only_recommend():
    """仅调用大模型，返回模型原始响应与归一化的5首推荐（不进行任何音乐服务搜索）。"""
    try:
        # 解析请求
        try:
            data = request.get_json(silent=True)
        except Exception:
            data = None
        if not data:
            raw_body = request.get_data(as_text=True)
            print(f"解析请求 JSON 失败或为空，原始请求体: {raw_body}")
            return jsonify({'success': False, 'message': '请求体不是合法的 JSON 或为空', 'raw': raw_body}), 400

        text = (data.get('text') or '').strip()
        if not text:
            return jsonify({'success': False, 'message': '文本内容不能为空'}), 400

        # 分析文本（可选，保留分析信息）
        scene_emotion = analyze_text(text)

        # 调用推荐模型并返回其原始输出与归一化后的推荐列表
        try:
            model_raw = call_recommender_model(text)
        except Exception as e:
            print(f"模型独立调用失败: {e}")
            return jsonify({'success': False, 'message': '调用模型失败', 'error': str(e)}), 500

        # 解析并归一化
        try:
            model_obj = json.loads(model_raw) if isinstance(model_raw, str) else model_raw
        except Exception:
            model_obj = model_raw

        normalized = normalize_model_recommendations(model_obj)

        return jsonify({
            'success': True,
            'model_raw': model_raw,
            'model_recommendations': normalized,
            'analysis': scene_emotion
        })

    except Exception as e:
        print(f"model-only 推荐错误: {e}")
        return jsonify({'success': False, 'message': '服务器错误'}), 500


@app.route('/api/recommend/resolve', methods=['POST'])
def recommend_resolve():
    """解析模型推荐并在音乐服务中逐条搜索匹配。

    请求体支持两种形式：
    - 提供 `recommendations` 字段（模型返回的推荐列表），或
    - 提供 `text` 字段，后端会先调用模型获取推荐再解析。

    返回：每个推荐项与在音乐服务中找到的首个匹配（若有）对应。
    """
    try:
        try:
            data = request.get_json(silent=True)
        except Exception:
            data = None
        if not data:
            raw_body = request.get_data(as_text=True)
            print(f"解析请求 JSON 失败或为空，原始请求体: {raw_body}")
            return jsonify({'success': False, 'message': '请求体不是合法的 JSON 或为空', 'raw': raw_body}), 400

        recs = data.get('recommendations')
        text = data.get('text')

        # 如果未传 recommendations，但有 text，则先调用模型
        if not recs and text:
            try:
                model_raw = call_recommender_model(text)
            except Exception as e:
                print(f"调用模型获取推荐失败: {e}")
                return jsonify({'success': False, 'message': '调用模型失败', 'error': str(e)}), 500

            try:
                model_obj = json.loads(model_raw) if isinstance(model_raw, str) else model_raw
            except Exception:
                model_obj = model_raw

            recs = normalize_model_recommendations(model_obj)

        else:
            # 传入了 recommendations，归一化处理
            recs = normalize_model_recommendations(recs)

        if not recs:
            return jsonify({'success': True, 'resolved': []})

        resolved = []
        for rec in recs:
            title = (rec.get('title') or '').strip()
            artist = (rec.get('artist') or '').strip()
            if not title:
                resolved.append({'recommendation': rec, 'song': None})
                continue

            # 优先仅用歌名搜索，若未命中再尝试 title + artist
            search_results = search_songs([title])
            if not search_results and artist:
                search_results = search_songs([f"{title} {artist}"])

            if search_results:
                # 获取首条匹配的详情并附回
                details = get_song_details([search_results[0]])
                resolved.append({'recommendation': rec, 'song': (details[0] if details else search_results[0])})
            else:
                resolved.append({'recommendation': rec, 'song': None})

        return jsonify({'success': True, 'resolved': resolved})

    except Exception as e:
        print(f"recommend-resolve 错误: {e}")
        return jsonify({'success': False, 'message': '服务器错误'}), 500

@app.route('/api/history', methods=['GET'])
def get_history():
    """获取推荐历史"""
    try:
        # 返回历史记录，按时间倒序排列
        sorted_history = sorted(recommendation_history, 
                              key=lambda x: x['timestamp'], 
                              reverse=True)
        return jsonify({
            'success': True,
            'history': sorted_history
        })
    except Exception as e:
        print(f"获取历史记录错误: {str(e)}")
        return jsonify({'success': False, 'message': '获取历史记录失败'}), 500

@app.route('/api/song/url', methods=['GET'])
def get_song_url():
    """获取歌曲播放URL"""
    try:
        song_id = request.args.get('id')
        if not song_id:
            return jsonify({'success': False, 'message': '缺少歌曲ID'}), 400

        print(f"AI服务: 尝试获取歌曲ID {song_id} 的URL")
        print(f"AI服务: 请求音乐服务 {MUSIC_SERVICE_URL}/api/song/url")

        # 调用音乐服务API
        response = requests.get(f"{MUSIC_SERVICE_URL}/api/song/url", 
                              params={'id': song_id})

        print(f"AI服务: 音乐服务响应状态码: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"AI服务: 音乐服务返回数据: {data}")
            return jsonify(data)
        else:
            print(f"AI服务: 音乐服务返回错误，状态码: {response.status_code}")
            return jsonify({'success': False, 'message': '获取歌曲URL失败'}), 404

    except Exception as e:
        print(f"AI服务: 获取歌曲URL错误: {str(e)}")
        return jsonify({'success': False, 'message': '服务器错误'}), 500

@app.route('/api/history', methods=['DELETE'])
def clear_history():
    """清空推荐历史"""
    try:
        global recommendation_history
        recommendation_history = []
        return jsonify({
            'success': True,
            'message': '历史记录已清空'
        })
    except Exception as e:
        print(f"清空历史记录错误: {str(e)}")
        return jsonify({'success': False, 'message': '清空历史记录失败'}), 500

def analyze_text(text):
    """使用通义千问分析文本，提取场景/情感"""
    try:
        # 构建强制JSON输出的提示词，使用用户原始输入作为分析对象
        prompt = build_strict_json_prompt(text)

        response = call_qwen_api(prompt)
        # 确保返回是JSON字符串，解析并返回对象
        return json.loads(response)
    except Exception as e:
        print(f"文本分析错误: {str(e)}")
        # 返回默认值
        return {
            "type": "其他",
            "description": "无法分析",
            "tags": ["默认"]
        }

def analyze_image(image_bytes):
    """使用通义千问分析图片，提取场景/情感"""
    try:
        # 将图片转换为base64
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')

        prompt = """请分析这张图片，判断它属于场景类、情感类还是其他，并给出具体的场景或情感描述。

请以JSON格式返回结果，包含以下字段：
- type: 场景类、情感类或其他
- description: 具体的场景或情感描述
- tags: 相关标签列表（最多5个）
"""

        response = call_qwen_api_with_image(prompt, image_base64)
        return json.loads(response)
    except Exception as e:
        print(f"图片分析错误: {str(e)}")
        # 返回默认值
        return {
            "type": "场景类",
            "description": "图片场景",
            "tags": ["默认"]
        }

def generate_keywords(scene_emotion):
    """基于场景/情感生成搜索关键词"""
    try:
        tags = scene_emotion.get('tags', []) or []
        description = scene_emotion.get('description', '') or ''

        # 优先使用tags生成关键词，加入description作为备选
        keywords = []
        for t in tags:
            if isinstance(t, str) and t.strip():
                keywords.append(t.strip())

        if description and description not in keywords:
            keywords.insert(0, description)

        # 保证关键词列表不为空，长度最多5
        if not keywords:
            keywords = [description] if description else ['默认']

        # 截断并返回
        return keywords[:5]
    except Exception as e:
        print(f"生成关键词错误: {str(e)}")
        # 返回默认值
        return [scene_emotion.get('description', '默认')]

def search_songs(keywords):
    """使用关键词搜索歌曲"""
    try:
        # 使用第一个关键词搜索
        keyword = keywords[0] if keywords else "默认"

        # 调用音乐服务API
        response = requests.get(f"{MUSIC_SERVICE_URL}/api/search", 
                              params={'keywords': keyword, 'limit': 10})

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                songs = data.get('songs', [])
                # 只保留看起来像歌曲的对象（必须包含id或songId）
                valid = []
                for s in songs:
                    if isinstance(s, dict) and (s.get('id') or s.get('songId')):
                        valid.append(s)
                if valid:
                    return valid
                else:
                    print(f"音乐服务返回的结果缺少有效id，将被忽略: {songs}")

        # 如果失败，尝试直接调用网易云音乐API
        response = requests.get(f"{NETEASE_API_URL}/search", 
                              params={'keywords': keyword, 'limit': 10, 'randomCNIP': 'true'})

        if response.status_code == 200 and response.json().get('code') == 200:
            songs = response.json().get('result', {}).get('songs', [])
            valid = []
            for s in songs:
                if isinstance(s, dict) and (s.get('id') or s.get('songId')):
                    valid.append(s)
            if valid:
                return valid
            else:
                print(f"网易云直连返回的结果缺少有效id，将被忽略: {songs}")

        return []
    except Exception as e:
        print(f"搜索歌曲错误: {str(e)}")
        return []


def normalize_model_recommendations(model_obj):
    """归一化大模型返回结果，确保返回一个包含至多5个推荐项的列表，
    每项为字典至少包含 'title' 字段，优先使用模型返回的 title/artist 字段。
    支持输入格式：
    - 顶层为 dict 且包含 'recommendations' 列表
    - 顶层为 list（字符串列表或对象列表）
    - 顶层为单个对象（单首歌）
    - 顶层为字符串（尝试 parse 为 JSON）
    """
    try:
        if not model_obj:
            return []

        # 如果传入的是字符串，尝试解析为 JSON
        if isinstance(model_obj, str):
            try:
                parsed = json.loads(model_obj)
                return normalize_model_recommendations(parsed)
            except Exception:
                # 非 JSON 字符串，作为单条标题处理
                return [{'title': model_obj}]

        # 如果是 dict，优先取 recommendations 字段
        candidates = None
        if isinstance(model_obj, dict):
            if isinstance(model_obj.get('recommendations'), list):
                candidates = model_obj.get('recommendations')
            else:
                # 尝试在值中寻找第一个列表
                for v in model_obj.values():
                    if isinstance(v, list):
                        candidates = v
                        break
                # 若仍未找到，视为单个推荐对象
                if candidates is None:
                    candidates = [model_obj]

        # 如果直接是列表
        if isinstance(model_obj, list):
            candidates = model_obj

        if not isinstance(candidates, list):
            return []

        recs = []
        for item in candidates:
            if isinstance(item, str):
                recs.append({'title': item})
            elif isinstance(item, dict):
                title = item.get('title') or item.get('name') or ''
                artist = item.get('artist') or item.get('singer') or ''
                reason = item.get('reason') or item.get('desc') or ''
                language = item.get('language') or ''
                recs.append({'title': title, 'artist': artist, 'reason': reason, 'language': language})
            else:
                continue

        # 去重并保留最多5条
        seen = set()
        out = []
        for r in recs:
            key = (r.get('title','') + '|' + r.get('artist','')).strip().lower()
            if not r.get('title'):
                continue
            if key in seen:
                continue
            seen.add(key)
            out.append(r)
            if len(out) >= 5:
                break

        return out
    except Exception as e:
        print(f"归一化模型返回错误: {e}")
        return []

def get_song_details(songs):
    """获取歌曲详细信息"""
    try:
        if not songs:
            return []

        # 提取歌曲ID
        song_ids = [str(song.get('id')) for song in songs]

        # 调用音乐服务API
        response = requests.get(f"{MUSIC_SERVICE_URL}/api/song/detail", 
                              params={'ids': ','.join(song_ids)})

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                # 获取原始歌曲列表
                songs = data.get('songs', [])

                # 将网易云API常见字段映射到前端期望字段
                for song in songs:
                    # 网易云返回的专辑通常在'al'，映射为 'album'
                    if 'al' in song and (song.get('album') is None):
                        song['album'] = song.get('al')

                    # 网易云返回的艺术家通常在'ar'，映射为 'artists'
                    if 'ar' in song and (song.get('artists') is None):
                        # 将网易的'ar'数组中的'name'字段保留，转换成与前端一致的artists格式
                        song['artists'] = song.get('ar')

                    # 兼容不同字段名：picUrl 或 pic
                    if song.get('album'):
                        # 一般网易云专辑封面字段为 'picUrl' 或 'pic'
                        if 'picUrl' not in song['album'] or not song['album'].get('picUrl'):
                            # 尝试常见替代字段 'pic'
                            if song['album'].get('pic'):
                                song['album']['picUrl'] = song['album'].get('pic')
                            else:
                                song['album']['picUrl'] = 'https://p3.music.126.net/SyqjxPvTbK4Jt_lWjMZgKg==/109951165633973637.jpg'
                        if 'name' not in song['album'] or not song['album'].get('name'):
                            song['album']['name'] = '未知专辑'

                    # 确保artists数组存在且不为空
                    if 'artists' not in song or not song['artists']:
                        song['artists'] = [{'name': '未知艺术家'}]
                    else:
                        # 确保每个artist都有name
                        for artist in song['artists']:
                            if 'name' not in artist or not artist.get('name'):
                                artist['name'] = '未知艺术家'

                # 去重：按照歌曲ID去重，保持原始顺序
                seen_ids = set()
                unique_songs = []
                for s in songs:
                    sid = str(s.get('id') or s.get('songId') or '')
                    if not sid:
                        # 作为兜底，尝试组合 name+artists
                        sid = (s.get('name', '') + '|' + ','.join([a.get('name','') for a in s.get('artists',[])])).strip()
                    if sid and sid not in seen_ids:
                        seen_ids.add(sid)
                        unique_songs.append(s)

                # 限制返回数量（最多10首），防止重复过多
                return unique_songs[:10]

        # 如果失败，尝试直接调用网易云音乐API
        response = requests.get(f"{NETEASE_API_URL}/song/detail", 
                              params={'ids': ','.join(song_ids), 'randomCNIP': 'true'})

        if response.status_code == 200 and response.json().get('code') == 200:
            songs = response.json().get('songs', [])
            # 应用同样的数据完整性检查
            for song in songs:
                # 确保album对象存在
                if 'album' not in song or song['album'] is None:
                    song['album'] = {
                        'name': '未知专辑',
                        'picUrl': 'https://p3.music.126.net/SyqjxPvTbK4Jt_lWjMZgKg==/109951165633973637.jpg'
                    }
                else:
                    # 确保album对象有picUrl
                    if 'picUrl' not in song['album'] or song['album']['picUrl'] is None:
                        song['album']['picUrl'] = 'https://p3.music.126.net/SyqjxPvTbK4Jt_lWjMZgKg==/109951165633973637.jpg'
                    # 确保album对象有name
                    if 'name' not in song['album'] or song['album']['name'] is None:
                        song['album']['name'] = '未知专辑'

                # 确保artists数组存在且不为空
                if 'artists' not in song or not song['artists']:
                    song['artists'] = [{'name': '未知艺术家'}]
                else:
                    # 确保每个artist都有name
                    for artist in song['artists']:
                        if 'name' not in artist or not artist['name']:
                            artist['name'] = '未知艺术家'

            # 去重：按照歌曲ID去重，保持原始顺序
            seen_ids = set()
            unique_songs = []
            for s in songs:
                sid = str(s.get('id') or s.get('songId') or '')
                if not sid:
                    sid = (s.get('name', '') + '|' + ','.join([a.get('name','') for a in s.get('artists',[])])).strip()
                if sid and sid not in seen_ids:
                    seen_ids.add(sid)
                    unique_songs.append(s)

            return unique_songs[:10]

        return []
    except Exception as e:
        print(f"获取歌曲详情错误: {str(e)}")
        return []

def save_recommendation_history(type, input_text, image_base64, songs):
    """保存推荐历史"""
    try:
        history_item = {
            'type': type,
            'timestamp': datetime.datetime.now().isoformat(),
            'input': input_text,
            'imagePreview': f"data:image/jpeg;base64,{image_base64}" if image_base64 else None,
            'songs': songs[:5]  # 只保存前5首歌
        }

        recommendation_history.append(history_item)

        # 限制历史记录数量，最多保存50条
        if len(recommendation_history) > 50:
            recommendation_history.pop(0)
    except Exception as e:
        print(f"保存历史记录错误: {str(e)}")

def call_qwen_api(prompt):
    """调用通义千问API"""
    try:
        print(f"调用通义千问API（真实调用）提示词长度: {len(prompt) if prompt else 0}")

        api_key = os.getenv('QWEN_API_KEY', QWEN_API_KEY)
        api_url = os.getenv('QWEN_API_URL') or os.getenv('QWEN_API_ENDPOINT')
        if not api_key or api_key == 'your_qwen_api_key':
            raise RuntimeError('QWEN_API_KEY 未配置或为占位符，请设置真实 API Key 到环境变量 QWEN_API_KEY')
        if not api_url:
            raise RuntimeError('QWEN_API_URL 未配置，请设置模型 API 的 URL 到环境变量 QWEN_API_URL')

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        }

        endpoint_url = api_url
        if 'chat' not in api_url:
            endpoint_url = api_url.rstrip('/') + '/chat/completions'

        payload = {
            'model': os.getenv('QWEN_MODEL', 'qwen-plus'),
            'messages': [
                {'role': 'system', 'content': 'You are a helpful assistant.'},
                {'role': 'user', 'content': prompt}
            ],
            'temperature': float(os.getenv('QWEN_TEMPERATURE', '0.2')),
            'max_tokens': int(os.getenv('QWEN_MAX_TOKENS', '800'))
        }

        resp = requests.post(endpoint_url, headers=headers, json=payload, timeout=20)
        if resp.status_code != 200:
            raise RuntimeError(f'model API 返回非200: {resp.status_code} {resp.text}')

        # 可选写入 debug 日志
        try:
            if os.getenv('DEBUG_DUMP_MODEL_RESPONSE', '').lower() == 'true':
                debug_path = os.path.join(os.path.dirname(__file__), 'recommender_debug.log')
                with open(debug_path, 'a', encoding='utf-8') as f:
                    f.write(f"\n==== {datetime.datetime.now().isoformat()} CALL_QWEN_API ====\n")
                    f.write("PROMPT:\n")
                    f.write(prompt + "\n")
                    f.write("RESPONSE_TEXT:\n")
                    f.write(resp.text + "\n")
        except Exception as _e:
            print(f"写入模型调试日志失败: {_e}")

        # 尝试解析 JSON 并抽取文本
        data = resp.json()
        content = None
        if isinstance(data, dict):
            choices = data.get('choices')
            if choices and isinstance(choices, list) and len(choices) > 0:
                first = choices[0]
                if isinstance(first, dict):
                    msg = first.get('message') or first.get('delta')
                    if isinstance(msg, dict):
                        content = msg.get('content') or msg.get('content', '')
                    content = content or first.get('text') or first.get('message', '')
            if not content:
                content = data.get('content') or data.get('text')

        if not content:
            content = resp.text

        # 抽取 JSON 块
        m = re.search(r'(\{[\s\S]*\}|\[[\s\S]*\])', content)
        if m:
            extracted = m.group(1).strip()
            print(f"从模型响应中提取到 JSON 块 (call_qwen_api): {extracted[:200]}...")
            return extracted

        return content
    except Exception as e:
        print(f"调用通义千问API错误: {str(e)}")
        raise


def build_strict_json_prompt(user_text: str) -> str:
    """构建一个要求模型严格以JSON格式返回情感/场景/主题/氛围的提示词。

    在模型提示中我们把原始输入放入 `INPUT_TEXT:` 字段，明确要求返回 JSON 且给出字段说明。
    """
    prompt = f"""
请分析下面的输入文本，抽取并判断其：核心情感（emotion）、发生场景（scene）、潜在主题（themes）、整体氛围（atmosphere）和标签列表（tags）。

OUTPUT_REQUIREMENTS: 返回必须是严格的 JSON 字符串，且包含如下字段：
- emotion: 字符串，表示主要情感（例如：孤独、喜悦、怀念、激情、忧伤、治愈、浪漫等）
- scene: 字符串，表示发生场景（例如：深夜独处、雨天散步、夏日出游等）
- themes: 数组，表示潜在主题关键词（每个元素为字符串，最多5个）
- atmosphere: 字符串，表示整体氛围风格（简短描述）
- tags: 数组，额外标签，用于搜索关键词（最多5个）
- description: 字符串，1-2句简短描述总结（不超过40字）

请注意：严格只输出 JSON，不要包含其它多余文本或注释。

INPUT_TEXT: {user_text}
"""
    return prompt


def build_recommender_prompt(user_text: str) -> str:
        """根据用户提供的模板构建用于大模型的推荐提示词，强制要求模型返回 JSON。

        模板示例（用户要求的格式）会包含输入文本和示例输出结构说明，要求模型返回包含analysis和recommendations的JSON。
        """
        prompt = f"""
请根据下面的输入内容，**如果用户输入的是歌名则接下来的推荐歌单里必须有这首歌曲**，首先分析其中的核心情感、发生场景、潜在主题以及整体氛围；随后基于分析推荐5首中文或英文歌曲。

返回格式必须严格为 JSON：
{{
    "analysis": {{
        "core_emotions": ["情感1","情感2"],
        "scenario": "场景描述",
        "theme": "主题句",
        "atmosphere": "氛围描述"
    }},
    "recommendations": [
        {{"title": "歌名", "artist": "歌手", "language": "中文/英文", "reason": "不超过30字的推荐理由"}},
        ... 共5条
    ]
}}

严格注意：
- 只输出 JSON，不要输出任何额外文本或解释；
- recommendations 必须包含 5 条不重复歌曲，尽量大众熟悉但不过度烂大街；
- 推荐理由不超过30字；
- language 字段需标注为 "中文" 或 "英文"；
- 不返回纯器乐曲，除非非常匹配场景。

INPUT_TEXT: {user_text}
"""
        return prompt

def call_qwen_api_with_image(prompt, image_base64):
    """调用通义千问多模态API（图片分析）"""
    try:
        print(f"调用通义千问多模态API（真实调用），提示词长度: {len(prompt) if prompt else 0}, 图片大小: {len(image_base64) if image_base64 else 0}")

        api_key = os.getenv('QWEN_API_KEY', QWEN_API_KEY)
        api_url = os.getenv('QWEN_API_URL') or os.getenv('QWEN_API_ENDPOINT')
        if not api_key or api_key == 'your_qwen_api_key':
            raise RuntimeError('QWEN_API_KEY 未配置或为占位符，请设置真实 API Key 到环境变量 QWEN_API_KEY')
        if not api_url:
            raise RuntimeError('QWEN_API_URL 未配置，请设置模型 API 的 URL 到环境变量 QWEN_API_URL')

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        }

        endpoint_url = api_url
        if 'chat' not in api_url:
            endpoint_url = api_url.rstrip('/') + '/chat/completions'

        # 把图片以 base64 安放在 user 消息中，模型端需要能够解析 IMAGE_BASE64: <base64> 的形式
        combined = f"IMAGE_BASE64: {image_base64}\n{prompt}"

        payload = {
            'model': os.getenv('QWEN_MODEL', 'qwen-plus'),
            'messages': [
                {'role': 'system', 'content': 'You are a helpful assistant for multimodal image analysis.'},
                {'role': 'user', 'content': combined}
            ],
            'temperature': float(os.getenv('QWEN_TEMPERATURE', '0.2')),
            'max_tokens': int(os.getenv('QWEN_MAX_TOKENS', '800'))
        }

        resp = requests.post(endpoint_url, headers=headers, json=payload, timeout=30)
        if resp.status_code != 200:
            raise RuntimeError(f'model API 返回非200: {resp.status_code} {resp.text}')

        # 可选 debug dump
        try:
            if os.getenv('DEBUG_DUMP_MODEL_RESPONSE', '').lower() == 'true':
                debug_path = os.path.join(os.path.dirname(__file__), 'recommender_debug.log')
                with open(debug_path, 'a', encoding='utf-8') as f:
                    f.write(f"\n==== {datetime.datetime.now().isoformat()} CALL_QWEN_API_IMAGE ====\n")
                    f.write("PROMPT:\n")
                    f.write(prompt + "\n")
                    f.write("RESPONSE_TEXT:\n")
                    f.write(resp.text + "\n")
        except Exception as _e:
            print(f"写入模型调试日志失败: {_e}")

        data = resp.json()
        content = None
        if isinstance(data, dict):
            choices = data.get('choices')
            if choices and isinstance(choices, list) and len(choices) > 0:
                first = choices[0]
                if isinstance(first, dict):
                    msg = first.get('message') or first.get('delta')
                    if isinstance(msg, dict):
                        content = msg.get('content') or msg.get('content', '')
                    content = content or first.get('text') or first.get('message', '')
            if not content:
                content = data.get('content') or data.get('text')

        if not content:
            content = resp.text

        m = re.search(r'(\{[\s\S]*\}|\[[\s\S]*\])', content)
        if m:
            extracted = m.group(1).strip()
            print(f"从模型响应中提取到 JSON 块 (call_qwen_api_with_image): {extracted[:200]}...")
            return extracted

        return content
    except Exception as e:
        print(f"调用通义千问多模态API错误: {str(e)}")
        raise


def call_recommender_model(user_text: str) -> str:
    """调用大模型生成 5 首歌曲推荐，要求返回严格的 JSON 字符串。

    返回格式示例：
    [
      {"title": "歌名", "artist": "歌手", "language": "中文", "reason": "30字内推荐理由"},
      ... 共5条
    ]

    当前实现为本地模拟；未来可替换为真实大模型 HTTP 调用（使用 QWEN_API_KEY）。
    """
    # 尝试调用真实的 QWEN / 通义类 HTTP 接口（需在环境中设置 QWEN_API_KEY 与 QWEN_API_URL）
    try:
        prompt = build_recommender_prompt(user_text)
        print(f"调用推荐模型提示词（真实API）:\n{prompt[:400]}...")

        api_key = os.getenv('QWEN_API_KEY', QWEN_API_KEY)
        api_url = os.getenv('QWEN_API_URL') or os.getenv('QWEN_API_ENDPOINT')
        if not api_key or api_key == 'your_qwen_api_key':
            raise RuntimeError('QWEN_API_KEY 未配置或为占位符，请设置真实 API Key 到环境变量 QWEN_API_KEY')
        if not api_url:
            raise RuntimeError('QWEN_API_URL 未配置，请设置模型 API 的 URL 到环境变量 QWEN_API_URL')

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        }

        # 如果用户在 .env 中提供的是 base URL（例如 dashscope 的 compatible-mode/v1），
        # 我们需要拼接上 chat completions 路径以兼容 OpenAI-like 接口。
        endpoint_url = api_url
        if 'chat' not in api_url:
            endpoint_url = api_url.rstrip('/') + '/chat/completions'

        # 常见 Chat Completions 请求体（兼容 OpenAI-like 接口和 dashscope 的 compatible-mode）
        payload = {
            'model': os.getenv('QWEN_MODEL', 'qwen-plus'),
            'messages': [
                {'role': 'system', 'content': 'You are a helpful assistant.'},
                {'role': 'user', 'content': prompt}
            ],
            'temperature': float(os.getenv('QWEN_TEMPERATURE', '0.2')),
            'max_tokens': int(os.getenv('QWEN_MAX_TOKENS', '800'))
        }

        resp = requests.post(endpoint_url, headers=headers, json=payload, timeout=20)
        if resp.status_code != 200:
            raise RuntimeError(f'模型API返回非200状态: {resp.status_code} {resp.text}')

        data = resp.json()

        # 尝试从常见响应结构中抽取文本内容，兼容 OpenAI-like 或 choices.message.content 的结构
        content = None
        if isinstance(data, dict):
            # OpenAI-like: choices[0].message.content
            choices = data.get('choices')
            if choices and isinstance(choices, list) and len(choices) > 0:
                first = choices[0]
                if isinstance(first, dict):
                    msg = first.get('message') or first.get('delta')
                    if isinstance(msg, dict):
                        content = msg.get('content') or msg.get('content', '')
                    content = content or first.get('text') or first.get('message', '')

            # 其它接口可能直接返回 `data[0].content` 或类似字段
            if not content:
                # 尝试常见字段
                content = data.get('content') or data.get('text')

        if not content:
            # 最后回退为原始响应文本
            content = resp.text

        # 可选：把原始响应写入 debug 日志，便于离线排查
        try:
            if os.getenv('DEBUG_DUMP_MODEL_RESPONSE', '').lower() == 'true':
                debug_path = os.path.join(os.path.dirname(__file__), 'recommender_debug.log')
                with open(debug_path, 'a', encoding='utf-8') as f:
                    f.write(f"\n==== {datetime.datetime.now().isoformat()} ====\n")
                    f.write("PROMPT:\n")
                    f.write(prompt + "\n")
                    f.write("RESPONSE_TEXT:\n")
                    f.write(resp.text + "\n")
        except Exception as _e:
            print(f"写入模型调试日志失败: {_e}")

        # 抽取第一个 JSON 对象/数组，避免模型返回额外文本
        m = re.search(r'(\{[\s\S]*\}|\[[\s\S]*\])', content)
        if m:
            extracted = m.group(1).strip()
            print(f"从模型响应中提取到 JSON 块: {extracted[:200]}...")
            return extracted

        # 如果没找到 JSON，直接返回原文（上层会捕获解析失败并处理）
        return content.strip()

    except Exception as e:
        # 如果请求对象存在且响应文本可用，尝试写入调试日志
        try:
            resp_text = locals().get('resp').text if locals().get('resp') is not None else None
            if resp_text and os.getenv('DEBUG_DUMP_MODEL_RESPONSE', '').lower() == 'true':
                debug_path = os.path.join(os.path.dirname(__file__), 'recommender_debug.log')
                with open(debug_path, 'a', encoding='utf-8') as f:
                    f.write(f"\n==== {datetime.datetime.now().isoformat()} ERROR ====\n")
                    f.write("PROMPT:\n")
                    f.write((prompt or '') + "\n")
                    f.write("EXCEPTION:\n")
                    f.write(str(e) + "\n")
                    f.write("RESPONSE_TEXT_IF_ANY:\n")
                    f.write((resp_text or '') + "\n")
        except Exception as _ew:
            print(f"写入错误调试日志时失败: {_ew}")

        print(f"调用真实模型失败: {e}")
        # 向上抛出异常以便调用方能明确知道失败原因
        raise

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
