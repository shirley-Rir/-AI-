# 智能音乐推荐系统-V1
该项目 目前仅做了本地运行；后续二次开发再考虑搭载到线上，不可商业用途，因为API的原因

这是一个基于AI的智能音乐推荐系统，用户可以通过输入文本或上传图片来获取符合场景或情感的音乐推荐。
**项目全程使用AI code生成**
步骤
1.一个idea -->用大模型进行项目内容及其架构，技术栈，接口等内容;
2.前端页面设计:pixso（AI生成)
3.将接口信息，技术栈，项目需求接入AI Agent（这里用的是智普CODEGEEX、copilot、codex、结合使用)
## 系统架构

系统分为三个主要部分：
1. 前端：Vue 3 + Element Plus
2. 音乐服务：Node.js + Express（处理网易云音乐的API调用）
3. AI服务：Python + Flask（处理AI模型调用和业务逻辑）

## 功能特点

- 支持文本输入，分析场景和情感并推荐相应歌曲
- 支持图片上传，识别图片中的场景并推荐相应歌曲 （目前效果不好，AI层面需要再开发）
- 提供音乐播放功能
- 保存推荐历史记录，支持查看和清空

## 部署说明

### 前置条件

1. 安装Node.js（版本 >= 14）
2. 安装Python（版本 >= 3.8）
3. 安装网易云音乐API服务（参考[NeteaseCloudMusicApiEnhanced](https://github.com/neteasecloudmusicapienhanced/api-enhanced)）
4. 准备通义千问API密钥

### 部署步骤

#### 1. 部署网易云音乐API服务

```bash
# 克隆项目
git clone https://github.com/neteasecloudmusicapienhanced/api-enhanced.git

# 进入目录
cd api-enhanced

# 安装依赖
pnpm i

# 启动服务（默认端口3000）
node app.js
```

#### 2. 部署音乐服务

```bash
# 进入音乐服务目录
cd backend/music-service

# 安装依赖
npm install

# 启动服务（默认端口3001）
npm start
```

#### 3. 部署AI服务

```bash
# 进入AI服务目录
cd backend/ai-service

# 安装依赖
pip install -r requirements.txt

# 配置环境变量（修改.env文件，填入通义千问API密钥）

# 启动服务（默认端口5000）
python app.py
```

#### 4. 部署前端

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 开发环境启动
npm run serve

# 生产环境构建
npm run build
```

## 环境变量配置

### 音乐服务 (.env)

```
# 服务端口
PORT=3001
```

### AI服务 (.env)

```
# 音乐服务URL
MUSIC_SERVICE_URL=http://localhost:3001

# 网易云音乐API URL
NETEASE_API_URL=http://localhost:3000

# 通义千问API密钥
QWEN_API_KEY=your_qwen_api_key
```

### 前端 (.env.development/.env.production)

```
# API基础URL
VUE_APP_API_BASE_URL=http://localhost:5000
```

## 注意事项

1. 确保所有服务都已正确启动，并按照正确的顺序（网易云音乐API → 音乐服务 → AI服务 → 前端）
2. 通义千问API密钥需要有效，否则AI分析功能将无法正常工作
3. 生产环境中，建议使用专业的数据库替换内存存储的历史记录
4. 生产环境中，建议使用HTTPS协议，确保数据传输安全

## 开发说明

### 前端

- 使用Vue 3和Element Plus构建
- 使用Axios进行HTTP请求
- 采用组件化开发，代码结构清晰

### 后端

- 音乐服务使用Node.js和Express，负责处理网易云音乐的API调用
- AI服务使用Python和Flask，负责处理AI模型调用和业务逻辑
- 服务间通过HTTP API进行通信

## 许可证
CC BY-NC-SA 4.0
