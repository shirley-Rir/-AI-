<template>
  <div class="history-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>推荐历史</span>
          <el-button type="danger" @click="clearHistory" :disabled="!history || history.length === 0">
            清空历史
          </el-button>
        </div>
      </template>

      <el-empty v-if="!history || history.length === 0" description="暂无推荐历史" />

      <el-timeline v-else-if="history && history.length > 0">
        <el-timeline-item
          v-for="(item, index) in history"
          :key="index"
          :timestamp="item.timestamp"
          placement="top"
        >
          <el-card class="history-item">
            <div class="history-header">
              <h4>{{ item.type === 'text' ? '文本推荐' : '图片推荐' }}</h4>
              <span class="history-time">{{ item.timestamp }}</span>
            </div>

            <div class="history-content">
              <div class="history-input">
                <p v-if="item.type === 'text'" class="input-text">{{ item.input }}</p>
                <div v-else class="image-preview">
                  <img :src="item.imageUrl" alt="上传的图片" @error="handleImageError" @load="handleImageLoad" />
                </div>
              </div>

              <div class="history-songs">
                <h5>推荐歌曲</h5>
                <div class="recommendation-container">
                  <div 
                    class="song-card" 
                    v-for="(song, songIndex) in item.songs" 
                    :key="songIndex" 
                    @click="playSong(song)"
                  >
                    <img :src="song.cover || (song.album && song.album.picUrl) || 'https://p2.music.126.net/6y-UleORITSBtjQJ4xgN2A==/109951165633973637.jpg'" alt="歌曲封面" class="song-cover">
                    <div class="song-info">
                      <h4 class="song-name">{{ song.name }}</h4>
                      <p class="song-artist">{{ song.artist || '未知艺术家' }}</p>
                    </div>
                    <div class="play-button" v-if="playingSongId === song.id">
                      <i class="fas fa-pause"></i>
                    </div>
                    <div class="play-button" v-else>
                      <i class="fas fa-play"></i>
                    </div>
                  </div>
                </div>
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
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '../api'

export default {
  name: 'HistoryView',
  setup() {
    const router = useRouter()
    const history = ref([])
    const loading = ref(false)
    const audioPlayer = ref(null)
    const playingSongId = ref(null)
    const isPlaying = ref(false)

    // 获取历史记录
    const fetchHistory = async () => {
      try {
        loading.value = true
        const response = await api.getHistory()
        // 检查响应数据结构
        if (response && response.success && response.history) {
          console.log("接收到的历史记录数据:", response.history);
          history.value = response.history
        } else {
          history.value = []
        }
      } catch (error) {
        console.error('获取历史记录失败:', error)
        ElMessage.error('获取历史记录失败')
        history.value = []
      } finally {
        loading.value = false
      }
    }

    // 清空历史记录
    const clearHistory = async () => {
      try {
        await api.clearHistory()
        history.value = []
        ElMessage.success('历史记录已清空')
      } catch (error) {
        console.error('清空历史记录失败:', error)
        ElMessage.error('清空历史记录失败')
      }
    }

    // 播放歌曲
    const playSong = async (song) => {
      // 跳转到主页面并传递歌曲信息
      const songInfo = {
        id: song.id,
        name: song.name,
        artist: song.artist
      }

      // 使用localStorage存储歌曲信息，以便主页面可以获取
      localStorage.setItem('playSong', JSON.stringify(songInfo))

      // 跳转到主页面，并设置标志位以显示音乐播放界面
      localStorage.setItem('showPlayer', 'true')
      router.push('/')

      ElMessage.success(`正在播放: ${song.name} - ${song.artist}`)
    }

    // 歌曲播放结束
    const handleSongEnded = () => {
      isPlaying.value = false
    }
    
    // 图片加载成功处理
    const handleImageLoad = (event) => {
      console.log("图片加载成功:", event.target.src);
    }
    
    // 图片加载失败处理
    const handleImageError = (event) => {
      console.error("图片加载失败:", event.target.src);
      
      // 尝试从item对象获取imagePreview字段
      const itemElement = event.target.closest(".el-card");
      const itemIndex = Array.from(itemElement.parentElement.children).indexOf(itemElement);
      const item = history.value[itemIndex];
      
      console.error("图片URL详情:", {
        src: event.target.src,
        imageUrl: item.imageUrl,
        imagePreview: item.imagePreview
      });
      
      // 如果imagePreview存在且与imageUrl不同，尝试使用imagePreview
      if (item.imagePreview && item.imagePreview !== item.imageUrl) {
        console.log("尝试使用imagePreview字段:", item.imagePreview);
        event.target.src = item.imagePreview;
      }
    }

    onMounted(() => {
      fetchHistory()
    })

    return {
      history,
      loading,
      audioPlayer,
      playingSongId,
      isPlaying,
      clearHistory,
      playSong,
      handleSongEnded,
      handleImageLoad,
      handleImageError
    }
  }
}
</script>

<style scoped>
.history-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.history-item {
  margin-bottom: 15px;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.history-time {
  color: #909399;
  font-size: 14px;
}

.history-content {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.history-input {
  margin-bottom: 10px;
}

.input-text {
  background-color: #f5f7fa;
  padding: 10px;
  border-radius: 4px;
  white-space: pre-wrap;
}

.image-preview {
  max-width: 200px;
  max-height: 200px;
  overflow: hidden;
  border-radius: 4px;
}

.image-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.history-songs h5 {
  margin-bottom: 10px;
  color: #409EFF;
}

.recommendation-container {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
}

.song-card {
  display: flex;
  align-items: center;
  padding: 10px;
  border-radius: 8px;
  background-color: #f9f9f9;
  cursor: pointer;
  transition: all 0.3s ease;
  width: 300px;
  position: relative;
}

.song-card:hover {
  background-color: #f0f0f0;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.song-cover {
  width: 60px;
  height: 60px;
  border-radius: 4px;
  margin-right: 12px;
  object-fit: cover;
}

.song-info {
  flex: 1;
}

.song-name {
  margin: 0 0 5px 0;
  font-size: 16px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.song-artist {
  margin: 0;
  color: #666;
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.play-button {
  position: absolute;
  right: 10px;
  bottom: 10px;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background-color: rgba(64, 158, 255, 0.8);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.song-card:hover .play-button {
  opacity: 1;
}
</style>
