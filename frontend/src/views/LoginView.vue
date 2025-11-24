
<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <h1 class="login-title">情感音乐播放器</h1>
        <div class="highlight-bar"></div>
      </div>

      <el-tabs v-model="activeTab" class="login-tabs">
        <el-tab-pane label="登录" name="login">
          <el-form ref="loginFormRef" :model="loginForm" :rules="loginRules" class="login-form">
            <el-form-item prop="username">
              <el-input
                v-model="loginForm.username"
                placeholder="用户名"
                prefix-icon="User"
                size="large"
              />
            </el-form-item>
            <el-form-item prop="password">
              <el-input
                v-model="loginForm.password"
                type="password"
                placeholder="密码"
                prefix-icon="Lock"
                size="large"
                show-password
                @keyup.enter="handleLogin"
              />
            </el-form-item>
            <el-form-item>
              <el-button
                type="primary"
                size="large"
                class="login-button"
                :loading="loginLoading"
                @click="handleLogin"
              >
                登录
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="注册" name="register">
          <el-form ref="registerFormRef" :model="registerForm" :rules="registerRules" class="login-form">
            <el-form-item prop="username">
              <el-input
                v-model="registerForm.username"
                placeholder="用户名（至少3个字符）"
                prefix-icon="User"
                size="large"
              />
            </el-form-item>
            <el-form-item prop="email">
              <el-input
                v-model="registerForm.email"
                placeholder="邮箱（可选）"
                prefix-icon="Message"
                size="large"
              />
            </el-form-item>
            <el-form-item prop="display_name">
              <el-input
                v-model="registerForm.display_name"
                placeholder="显示名称（可选）"
                prefix-icon="Avatar"
                size="large"
              />
            </el-form-item>
            <el-form-item prop="password">
              <el-input
                v-model="registerForm.password"
                type="password"
                placeholder="密码（至少6个字符）"
                prefix-icon="Lock"
                size="large"
                show-password
              />
            </el-form-item>
            <el-form-item prop="confirmPassword">
              <el-input
                v-model="registerForm.confirmPassword"
                type="password"
                placeholder="确认密码"
                prefix-icon="Lock"
                size="large"
                show-password
                @keyup.enter="handleRegister"
              />
            </el-form-item>
            <el-form-item>
              <el-button
                type="primary"
                size="large"
                class="login-button"
                :loading="registerLoading"
                @click="handleRegister"
              >
                注册
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock, Message, Avatar } from '@element-plus/icons-vue'
import api from '../api'
import auth from '../auth'

export default {
  name: 'LoginView',
  components: {
    User,
    Lock,
    Message,
    Avatar
  },
  setup() {
    const router = useRouter()
    const activeTab = ref('login')
    const loginLoading = ref(false)
    const registerLoading = ref(false)
    const loginFormRef = ref(null)
    const registerFormRef = ref(null)

    // 登录表单
    const loginForm = reactive({
      username: '',
      password: ''
    })

    // 注册表单
    const registerForm = reactive({
      username: '',
      email: '',
      display_name: '',
      password: '',
      confirmPassword: ''
    })

    // 表单验证规则
    const loginRules = {
      username: [
        { required: true, message: '请输入用户名', trigger: 'blur' }
      ],
      password: [
        { required: true, message: '请输入密码', trigger: 'blur' }
      ]
    }

    const registerRules = {
      username: [
        { required: true, message: '请输入用户名', trigger: 'blur' },
        { min: 3, message: '用户名至少需要3个字符', trigger: 'blur' }
      ],
      email: [
        { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' }
      ],
      password: [
        { required: true, message: '请输入密码', trigger: 'blur' },
        { min: 6, message: '密码至少需要6个字符', trigger: 'blur' }
      ],
      confirmPassword: [
        { required: true, message: '请确认密码', trigger: 'blur' },
        {
          validator: (rule, value, callback) => {
            if (value !== registerForm.password) {
              callback(new Error('两次输入的密码不一致'))
            } else {
              callback()
            }
          },
          trigger: 'blur'
        }
      ]
    }

    // 处理登录
    const handleLogin = async () => {
      const valid = await loginFormRef.value.validate()
      if (!valid) return

      loginLoading.value = true
      try {
        const response = await api.login(loginForm.username, loginForm.password)

        if (response.success) {
          // 保存用户信息和令牌
          auth.setToken(response.token)
          auth.setUser(response.user)

          ElMessage.success('登录成功')
          router.push('/')
        } else {
          ElMessage.error(response.message || '登录失败')
        }
      } catch (error) {
        console.error('登录错误:', error)
        ElMessage.error('登录失败，请稍后再试')
      } finally {
        loginLoading.value = false
      }
    }

    // 处理注册
    const handleRegister = async () => {
      const valid = await registerFormRef.value.validate()
      if (!valid) return

      registerLoading.value = true
      try {
        const response = await api.register(
          registerForm.username,
          registerForm.email,
          registerForm.password,
          registerForm.display_name
        )

        if (response.success) {
          // 保存用户信息和令牌
          auth.setToken(response.token)
          auth.setUser(response.user)

          ElMessage.success('注册成功')
          router.push('/')
        } else {
          ElMessage.error(response.message || '注册失败')
        }
      } catch (error) {
        console.error('注册错误:', error)
        ElMessage.error('注册失败，请稍后再试')
      } finally {
        registerLoading.value = false
      }
    }

    return {
      activeTab,
      loginForm,
      registerForm,
      loginRules,
      registerRules,
      loginLoading,
      registerLoading,
      loginFormRef,
      registerFormRef,
      handleLogin,
      handleRegister
    }
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: var(--bg-gradient);
}

.login-card {
  width: 100%;
  max-width: 450px;
  padding: 2rem;
  border-radius: var(--border-radius);
  box-shadow: var(--card-shadow);
  background-color: white;
}

.login-header {
  text-align: center;
  margin-bottom: 2rem;
}

.login-title {
  font-size: 2rem;
  font-weight: 800;
  color: var(--text-dark);
  margin-bottom: 0.5rem;
}

.highlight-bar {
  width: 80px;
  height: 4px;
  background: linear-gradient(to right, var(--primary-color), var(--secondary-color));
  margin: 0 auto;
  border-radius: 2px;
}

.login-tabs {
  margin-top: 1.5rem;
}

.login-form {
  margin-top: 1.5rem;
}

.login-button {
  width: 100%;
  font-weight: 600;
  background: linear-gradient(to right, var(--primary-color), var(--secondary-color));
  border: none;
  transition: var(--transition);
}

.login-button:hover {
  transform: translateY(-2px);
  box-shadow: var(--hover-shadow);
}

:deep(.el-tabs__header) {
  margin-bottom: 1.5rem;
}

:deep(.el-tabs__nav-wrap::after) {
  display: none;
}

:deep(.el-tabs__item) {
  font-weight: 600;
  font-size: 1rem;
}

:deep(.el-tabs__item.is-active) {
  color: var(--primary-color);
}

:deep(.el-tabs__active-bar) {
  background: linear-gradient(to right, var(--primary-color), var(--secondary-color));
}
</style>
