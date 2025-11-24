import axios from 'axios'
import auth from '../auth'

// 音乐服务axios实例
const musicApi = axios.create({
  baseURL: process.env.VUE_APP_MUSIC_API_URL || 'http://localhost:3001',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// AI服务axios实例
const aiApi = axios.create({
  baseURL: process.env.VUE_APP_AI_API_URL || 'http://localhost:5000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 为音乐服务添加请求拦截器
musicApi.interceptors.request.use(
  config => {
    // 在发送请求之前做些什么
    return config
  },
  error => {
    // 对请求错误做些什么
    return Promise.reject(error)
  }
)

// 为音乐服务添加响应拦截器
musicApi.interceptors.response.use(
  response => {
    // 对响应数据做点什么
    return response.data
  },
  error => {
    // 对响应错误做点什么
    console.error('音乐API请求错误:', error)
    return Promise.reject(error)
  }
)

// 为AI服务添加请求拦截器
aiApi.interceptors.request.use(
  config => {
    // 添加JWT令牌到请求头
    if (auth.token.value) {
      config.headers.Authorization = `Bearer ${auth.token.value}`
    }
    return config
  },
  error => {
    // 对请求错误做些什么
    return Promise.reject(error)
  }
)

// 为AI服务添加响应拦截器
aiApi.interceptors.response.use(
  response => {
    // 对响应数据做点什么
    return response.data
  },
  error => {
    // 对响应错误做点什么
    console.error('AI API请求错误:', error)
    return Promise.reject(error)
  }
)

// API方法
export default {
  // 基于文本推荐
  getTextRecommendation(text) {
    return aiApi.post('/api/recommend/text', { text })
  },

  // 基于图片推荐
  getImageRecommendation(imageFile) {
    const formData = new FormData()
    formData.append('image', imageFile)

    return aiApi.post('/api/recommend/image', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // 获取歌曲URL
  getSongUrl(songId) {
    return musicApi.get('/api/song/url', {
      params: { id: songId }
    })
  },

  // 搜索歌曲
  searchSongs(keywords, limit = 10) {
    return musicApi.get('/api/search', {
      params: { keywords, limit }
    })
  },

  // 获取歌曲详情
  getSongDetails(songIds) {
    return musicApi.get('/api/song/detail', {
      params: { ids: Array.isArray(songIds) ? songIds.join(',') : songIds }
    })
  },

  // 获取推荐历史
  getHistory() {
    return aiApi.get('/api/history')
  },

  // 获取分页推荐历史
  getPagedHistory(page = 1, pageSize = 5) {
    return aiApi.get('/api/history/paged', {
      params: { page, pageSize }
    })
  },

  // 清空推荐历史
  clearHistory() {
    return aiApi.delete('/api/history')
  },

  // 获取歌词
  getLyric(songId) {
    return musicApi.get('/api/lyric', {
      params: { id: songId }
    })
  },

  // 获取逐字歌词
  getLyricNew(songId) {
    return musicApi.get('/api/lyric/new', {
      params: { id: songId }
    })
  },

  // 用户认证相关API
  // 用户登录
  login(username, password) {
    return aiApi.post('/api/user/login', { username, password })
  },

  // 用户注册
  register(username, email, password, displayName) {
    return aiApi.post('/api/user/register', {
      username,
      email,
      password,
      display_name: displayName
    })
  },

  // 验证令牌
  verifyToken(token) {
    return aiApi.post('/api/user/verify-token', { token })
  },

  // 获取用户资料
  getUserProfile() {
    return aiApi.get('/api/user/profile')
  },

  // 更新用户资料
  updateUserProfile(profile) {
    return aiApi.put('/api/user/profile', profile)
  },

  // 获取用户偏好设置
  getUserPreferences() {
    return aiApi.get('/api/user/preferences')
  },

  // 更新用户偏好设置
  updateUserPreferences(preferences) {
    return aiApi.put('/api/user/preferences', preferences)
  }
}
