<template>
  <div id="app">
    <div class="title-container">
      <h1 class="main-title">情感音乐播放器</h1>
      <div class="highlight-bar"></div>
    </div>
    <div class="nav-container">
      <router-link to="/" class="nav-link" :class="{ active: $route.path === '/' }">情感输入</router-link>
      <router-link to="/history" class="nav-link" :class="{ active: $route.path === '/history' }">推荐历史</router-link>
      
      <!-- 用户菜单 -->
      <div class="user-menu">
        <template v-if="isAuthenticated">
          <el-dropdown @command="handleUserMenuCommand">
            <span class="user-info">
              <el-avatar :size="32" :src="user.avatar_url">
                <User />
              </el-avatar>
              <span class="username">{{ user.display_name || user.username }}</span>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">
                  <el-icon><User /></el-icon>个人资料
                </el-dropdown-item>
                <el-dropdown-item command="logout" divided>
                  <el-icon><SwitchButton /></el-icon>退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </template>
        <template v-else>
          <router-link to="/login" class="nav-link login-btn">登录/注册</router-link>
        </template>
      </div>
    </div>
    <div class="content-container">
      <router-view/>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { User, SwitchButton } from '@element-plus/icons-vue'
import auth from './auth'

export default {
  name: 'App',
  components: {
    User,
    SwitchButton
  },
  setup() {
    const router = useRouter()
    
    // 计算属性：是否已登录
    const isAuthenticated = computed(() => auth.isAuthenticated())
    
    // 计算属性：当前用户信息
    const user = computed(() => auth.user.value)
    
    // 处理用户菜单命令
    const handleUserMenuCommand = (command) => {
      if (command === 'profile') {
        router.push('/profile')
      } else if (command === 'logout') {
        // 显示确认对话框
        ElMessageBox.confirm('确定要退出登录吗？', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }).then(() => {
          // 清除认证信息
          auth.clearAuth()
          
          // 显示成功消息
          ElMessage.success('已退出登录')
          
          // 重定向到首页
          router.push('/')
        }).catch(() => {
          // 用户取消
        })
      }
    }
    
    return {
      isAuthenticated,
      user,
      handleUserMenuCommand
    }
  }
}
</script>

<style>
:root {
  --primary-color: #ffb6c1; /* 柔和的粉红色 */
  --secondary-color: #a8d8ea; /* 淡蓝色 */
  --accent-color: #d9c6c1; /* 柔和米色 */
  --text-dark: #5a5c69; /* 深灰色文本 */
  --text-light: #ffffff; /* 白色文本 */
  --bg-gradient: linear-gradient(135deg, #fff5f7 0%, #f9f3ee 100%);
  --card-shadow: 0 4px 20px rgba(255, 182, 193, 0.2);
  --inset-shadow: inset 0 2px 5px rgba(0,0,0,0.05);
  --hover-shadow: 0 8px 25px rgba(255, 182, 193, 0.3);
  --transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
  --border-radius: 12px;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Nunito', sans-serif;
  background: #f8f5f2;
  color: var(--text-dark);
  display: flex;
  flex-direction: column;
  align-items: center;
  min-height: 100vh;
}

#app {
  width: 100%;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.title-container {
  text-align: center;
  padding: 2rem 0 1rem;
  position: relative;
}

.main-title {
  font-size: 2.5rem;
  font-weight: 800;
  color: var(--text-dark);
  margin-bottom: 0.5rem;
}

.highlight-bar {
  width: 100px;
  height: 4px;
  background: linear-gradient(to right, var(--primary-color), var(--secondary-color));
  margin: 0 auto;
  border-radius: 2px;
}

.nav-container {
  display: flex;
  justify-content: center;
  gap: 2rem;
  margin-bottom: 2rem;
}

.nav-link {
  padding: 0.8rem 1.5rem;
  border-radius: 50px;
  color: var(--text-dark);
  text-decoration: none;
  font-weight: 600;
  transition: var(--transition);
  position: relative;
}

.nav-link:hover {
  color: var(--primary-color);
  transform: translateY(-2px);
}

.nav-link.active {
  background: var(--primary-color);
  color: white;
  box-shadow: 0 4px 15px rgba(255, 182, 193, 0.35);
}

.content-container {
  flex: 1;
  width: 100%;
  max-width: 1440px;
  margin: 0 auto;
  padding: 0 1rem 2rem;
}

.user-menu {
  margin-left: auto;
  display: flex;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  cursor: pointer;
}

.username {
  margin-left: 0.5rem;
  font-weight: 600;
}

.login-btn {
  background: var(--primary-color);
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 50px;
  font-weight: 600;
  transition: var(--transition);
}

.login-btn:hover {
  transform: translateY(-2px);
  box-shadow: var(--hover-shadow);
}
</style>