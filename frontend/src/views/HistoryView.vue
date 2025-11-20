<template>
  <div class="history-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>推荐历史</span>
          <el-button type="danger" @click="clearHistory" :disabled="history.length === 0">
            清空历史
          </el-button>
        </div>
      </template>

      <el-empty v-if="history.length === 0" description="暂无推荐历史" />

      <el-timeline v-else>
        <el-timeline-item
          v-for="(item, index) in history"
          :key="index"
          :timestamp="item.timestamp"
          placement="top"
        >
          <el-card>
            <h4>{{ item.type === 'text' ? '文本推荐' : '图片推荐' }}</h4>
            <p v-if="item.type === 'text'">输入: {{ item.input }}</p>
            <div v-else class="image-preview">
              <img :src="item.imagePreview" alt="上传的图片" />
            </div>

            <div class="song-list">
              <div 
                v-for="(song, songIndex) in item.songs" 
                :key="songIndex" 
                class="song-item"
              >
                <el-card shadow="hover" class="song-card">
                  <div class="song-info">
                    <img :src="(song.album && song.album.picUrl) ? song.album.picUrl : 'https://p3.music.126.net/SyqjxPvTbK4Jt_lWjMZgKg==/109951165633973637.jpg'" alt="专辑封面" class="album-cover">
                    <div class="song-details">
                      <h3>{{ song.name }}</h3>
                      <p>{{ (song.artists && Array.isArray(song.artists)) ? song.artists.map(artist => artist.name).join(', ') : '未知艺术家' }}</p>
                      <p>专辑: {{ (song.album && song.album.name) ? song.album.name : '未知专辑' }}</p>
                    </div>
                    <div class="player-controls">
                      <el-button 
                        type="primary" 
                        circle 
                        @click="playSong(song)"
                        :icon="playingSongId === song.id ? VideoPause : VideoPlay"
                      />
                    </div>
                  </div>
                </el-card>
              </div>
            </div>
          </el-card>
        </el-timeline-item>
      </el-timeline>
    </el-card>

    <audio ref="audioPlayer" @ended="handleSongEnded"></audio>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { VideoPlay, VideoPause } from '@element-plus/icons-vue'
import api from '../api'

export default {
  name: 'HistoryView',
  components: {
    VideoPlay,
    VideoPause
  },
  setup() {
    const history = ref([])
    const audioPlayer = ref(null)
    const playingSongId = ref(null)

    // 获取历史记录
    const fetchHistory = async () => {
      try {
        const response = await api.getHistory()
        if (response.success) {
          history.value = response.history
        }
      } catch (error) {
        console.error('获取历史记录失败:', error)
        ElMessage.error('获取历史记录失败')
      }
    }

    // 清空历史记录
    const clearHistory = async () => {
      try {
        await ElMessageBox.confirm('确定要清空所有推荐历史吗？', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })

        const response = await api.clearHistory()
        if (response.success) {
          history.value = []
          ElMessage.success('历史记录已清空')
        } else {
          ElMessage.error(response.message || '清空历史记录失败')
        }
      } catch (error) {
        if (error !== 'cancel') {
          console.error('清空历史记录失败:', error)
          ElMessage.error('清空历史记录失败')
        }
      }
    }

    // 播放歌曲
    const playSong = async (song) => {
      try {
        if (playingSongId.value === song.id) {
          // 如果是同一首歌，则暂停/播放切换
          if (audioPlayer.value.paused) {
            audioPlayer.value.play()
          } else {
            audioPlayer.value.pause()
          }
          return
        }

        // 获取歌曲URL
        const response = await api.getSongUrl(song.id)

        if (response.success && response.url) {
          audioPlayer.value.src = response.url
          audioPlayer.value.play()
          playingSongId.value = song.id
        } else {
          ElMessage.error('无法获取歌曲播放链接')
        }
      } catch (error) {
        console.error('播放歌曲失败:', error)
        ElMessage.error('播放歌曲失败，请稍后再试')
      }
    }

    // 歌曲播放结束
    const handleSongEnded = () => {
      playingSongId.value = null
    }

    // 组件挂载时获取历史记录
    onMounted(() => {
      fetchHistory()
    })

    return {
      history,
      audioPlayer,
      playingSongId,
      clearHistory,
      playSong,
      handleSongEnded,
      VideoPlay,
      VideoPause
    }
  }
}
</script>

<style scoped>
.history-container {
  max-width: 1200px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
  font-size: 18px;
}

.image-preview {
  margin: 10px 0;
  max-width: 200px;
}

.image-preview img {
  max-width: 100%;
  border-radius: 4px;
}

.song-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 15px;
  margin-top: 15px;
}

.song-item {
  margin-bottom: 15px;
}

.song-card {
  height: 100%;
}

.song-info {
  display: flex;
  align-items: center;
  padding: 10px;
}

.album-cover {
  width: 60px;
  height: 60px;
  border-radius: 4px;
  margin-right: 15px;
  object-fit: cover;
}

.song-details {
  flex-grow: 1;
}

.song-details h3 {
  margin: 0 0 5px;
  font-size: 16px;
}

.song-details p {
  margin: 0 0 5px;
  font-size: 14px;
  color: #666;
}

.player-controls {
  margin-left: 15px;
}
</style>
