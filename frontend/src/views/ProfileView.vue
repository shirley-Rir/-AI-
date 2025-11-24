
<template>
  <div class="profile-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>个人资料</span>
        </div>
      </template>

      <div class="profile-content">
        <div class="profile-avatar">
          <el-avatar :size="120" :src="profileForm.avatar_url || defaultAvatar">
            <User />
          </el-avatar>
          <el-button type="primary" plain class="avatar-button" @click="showAvatarDialog = true">
            更换头像
          </el-button>
        </div>

        <el-form ref="profileFormRef" :model="profileForm" :rules="profileRules" label-width="100px" class="profile-form">
          <el-form-item label="用户名" prop="username">
            <el-input v-model="profileForm.username" disabled />
          </el-form-item>
          <el-form-item label="显示名称" prop="display_name">
            <el-input v-model="profileForm.display_name" />
          </el-form-item>
          <el-form-item label="邮箱" prop="email">
            <el-input v-model="profileForm.email" />
          </el-form-item>
          <el-form-item label="个人简介" prop="bio">
            <el-input v-model="profileForm.bio" type="textarea" :rows="4" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="updateProfile" :loading="profileLoading">
              保存资料
            </el-button>
          </el-form-item>
        </el-form>
      </div>
    </el-card>

    <!-- 头像上传对话框 -->
    <el-dialog v-model="showAvatarDialog" title="更换头像" width="30%">
      <el-upload
        ref="avatarUploader"
        :action="uploadUrl"
        :headers="uploadHeaders"
        :show-file-list="false"
        :on-success="handleAvatarSuccess"
        :before-upload="beforeAvatarUpload"
        class="avatar-uploader"
      >
        <img v-if="tempAvatarUrl" :src="tempAvatarUrl" class="avatar-preview" />
        <el-icon v-else class="avatar-uploader-icon"><Plus /></el-icon>
      </el-upload>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showAvatarDialog = false">取消</el-button>
          <el-button type="primary" @click="confirmAvatar" :disabled="!tempAvatarUrl">
            确定
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { User, Plus } from '@element-plus/icons-vue'
import api from '../api'
import auth from '../auth'

export default {
  name: 'ProfileView',
  components: {
    User,
    Plus
  },
  setup() {
    const profileFormRef = ref(null)
    const profileLoading = ref(false)
    const showAvatarDialog = ref(false)
    const tempAvatarUrl = ref('')

    // 默认头像
    const defaultAvatar = 'https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png'

    // 上传URL和请求头
    const uploadUrl = `${process.env.VUE_APP_AI_API_URL || 'http://localhost:5000'}/api/upload/avatar`
    const uploadHeaders = {
      'Authorization': `Bearer ${auth.token.value}`
    }

    // 用户资料表单
    const profileForm = reactive({
      username: '',
      email: '',
      display_name: '',
      avatar_url: '',
      bio: ''
    })



    // 表单验证规则
    const profileRules = {
      display_name: [
        { required: true, message: '请输入显示名称', trigger: 'blur' }
      ],
      email: [
        { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' }
      ]
    }

    // 获取用户资料
    const fetchProfile = async () => {
      try {
        const response = await api.getUserProfile()

        if (response.success) {
          const { profile } = response

          // 更新资料表单
          Object.assign(profileForm, profile)
        } else {
          ElMessage.error(response.message || '获取用户资料失败')
        }
      } catch (error) {
        console.error('获取用户资料错误:', error)
        ElMessage.error('获取用户资料失败')
      }
    }

    // 更新用户资料
    const updateProfile = async () => {
      const valid = await profileFormRef.value.validate()
      if (!valid) return

      profileLoading.value = true
      try {
        const response = await api.updateUserProfile({
          display_name: profileForm.display_name,
          email: profileForm.email,
          avatar_url: profileForm.avatar_url,
          bio: profileForm.bio
        })

        if (response.success) {
          // 更新本地用户信息
          auth.setUser(response.profile)

          ElMessage.success('资料更新成功')
        } else {
          ElMessage.error(response.message || '资料更新失败')
        }
      } catch (error) {
        console.error('更新用户资料错误:', error)
        ElMessage.error('更新用户资料失败')
      } finally {
        profileLoading.value = false
      }
    }



    // 头像上传前验证
    const beforeAvatarUpload = (file) => {
      const isJPG = file.type === 'image/jpeg' || file.type === 'image/png'
      const isLt2M = file.size / 1024 / 1024 < 2

      if (!isJPG) {
        ElMessage.error('头像只能是 JPG 或 PNG 格式!')
      }
      if (!isLt2M) {
        ElMessage.error('头像大小不能超过 2MB!')
      }

      return isJPG && isLt2M
    }

    // 头像上传成功
    const handleAvatarSuccess = (response) => {
      if (response.success) {
        tempAvatarUrl.value = response.url
      } else {
        ElMessage.error(response.message || '头像上传失败')
      }
    }

    // 确认使用新头像
    const confirmAvatar = () => {
      profileForm.avatar_url = tempAvatarUrl.value
      showAvatarDialog.value = false
    }

    // 组件挂载时获取用户资料
    onMounted(() => {
      fetchProfile()
    })

    return {
      profileFormRef,
      profileForm,
      profileRules,
      profileLoading,
      showAvatarDialog,
      tempAvatarUrl,
      defaultAvatar,
      uploadUrl,
      uploadHeaders,
      updateProfile,
      beforeAvatarUpload,
      handleAvatarSuccess,
      confirmAvatar
    }
  }
}
</script>

<style scoped>
.profile-container {
  max-width: 800px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
  font-size: 18px;
}

.profile-content {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.profile-avatar {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 2rem;
}

.avatar-button {
  margin-top: 1rem;
}

.profile-form, .preferences-form {
  width: 100%;
  max-width: 500px;
}

.preferences-card {
  margin-top: 2rem;
}

.avatar-uploader {
  display: flex;
  justify-content: center;
  align-items: center;
  border: 1px dashed #d9d9d9;
  border-radius: 6px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  width: 178px;
  height: 178px;
}

.avatar-uploader:hover {
  border-color: var(--primary-color);
}

.avatar-uploader-icon {
  font-size: 28px;
  color: #8c939d;
  width: 178px;
  height: 178px;
  line-height: 178px;
  text-align: center;
}

.avatar-preview {
  width: 178px;
  height: 178px;
  display: block;
  object-fit: cover;
}
</style>
