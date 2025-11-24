
import { ref } from 'vue'

// 状态
const token = ref(localStorage.getItem('token') || '')
const user = ref(JSON.parse(localStorage.getItem('user') || '{}'))

// 设置令牌
const setToken = (newToken) => {
  token.value = newToken
  localStorage.setItem('token', newToken)
}

// 设置用户信息
const setUser = (newUser) => {
  user.value = newUser
  localStorage.setItem('user', JSON.stringify(newUser))
}

// 清除认证信息
const clearAuth = () => {
  token.value = ''
  user.value = {}
  localStorage.removeItem('token')
  localStorage.removeItem('user')
}

// 检查是否已登录
const isAuthenticated = () => {
  return !!token.value
}

// 导出
export default {
  token,
  user,
  setToken,
  setUser,
  clearAuth,
  isAuthenticated
}
