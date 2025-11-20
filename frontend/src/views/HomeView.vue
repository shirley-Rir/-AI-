<template>
  <div class="emotion-input-page" v-if="!showPlayer">
    <!-- 装饰背景元素 -->
    <div class="decoration-element circle-large"></div>
    <div class="decoration-element circle-small"></div>

    <div class="page-header">
      <h2 class="emotion-title">灵与此刻</h2>
      <div class="title-decoration"></div>
    </div>

    <div class="input-area">
      <div class="input-group">
        <div class="text-input-container">
          <input type="text" class="text-input" v-model="textInput" placeholder="您现在的灵感是？">
        </div>

        <button class="soulmate-btn" @click="getTextRecommendations" :disabled="loading">
          <i class="fas fa-heart"></i> 知音
        </button>
      </div>

      <div class="upload-container">
        <div class="upload-box" @click="triggerFileInput">
          <div class="upload-icon">
            <i class="fas fa-cloud-upload-alt"></i>
          </div>
          <p class="upload-text">上传图片表达心情</p>
        </div>
        <input type="file" ref="fileInput" style="display: none" accept="image/*" @change="handleImageChange">
      </div>
    </div>

    <div class="ai-hint">
      AI情感匹配，精准推荐音乐
    </div>
  </div>

  <!-- 音乐播放界面 -->
  <div class="music-player-page" v-else>
    <!-- 装饰背景元素 -->
    <div class="decoration-element" style="width:200px; height:200px; background:var(--secondary-color); border-radius:50%; top:-50px; right:-50px; opacity:0.12;"></div>
    <div class="decoration-element" style="width:150px; height:150px; background:var(--primary-color); border-radius:50%; bottom:-50px; left:-50px; opacity:0.12;"></div>

    <div class="player-container">
      <div class="album-cover">
        <img :src="currentSong && (currentSong.album && currentSong.album.picUrl) ? currentSong.album.picUrl : 'https://images.unsplash.com/photo-1470225620780-dba8ba36b745?ixlib=rb-4.0.3&auto=format&fit=crop&w=700&q=80'" alt="专辑封面" class="album-image">
      </div>

      <div class="player-controls">
        <div class="track-info">
          <h3 class="track-name">{{ currentSong ? currentSong.name : '选择一首歌曲' }}</h3>
          <p class="artist-name">{{ currentSong && (currentSong.artists && Array.isArray(currentSong.artists)) ? currentSong.artists.map(artist => artist.name).join(' · ') : '未知艺术家' }}</p>
        </div>

        <div class="controls-row">
          <button class="control-btn" @click="previousSong">
            <i class="fas fa-step-backward"></i>
          </button>
          <button class="control-btn play-btn" @click="togglePlay">
            <i class="fas" :class="isPlaying ? 'fa-pause' : 'fa-play'"></i>
          </button>
          <button class="control-btn" @click="nextSong">
            <i class="fas fa-step-forward"></i>
          </button>
        </div>

        <div class="progress-container">
          <div class="time-info">
            <span>{{ formatTime(currentTime) }}</span>
            <span>{{ formatTime(duration) }}</span>
          </div>
          <div class="progress-bar" @click="seekTo">
            <div class="progress-filled" :style="{ width: progressPercentage + '%' }"></div>
          </div>
        </div>

        <div class="volume-controls">
          <i class="fas fa-volume-up volume-icon"></i>
          <div class="volume-slider" @click="setVolume">
            <div class="volume-level" :style="{ width: volume * 100 + '%' }"></div>
          </div>
        </div>

        <div class="lyrics-container" ref="lyricsContainer">
          <p class="lyrics-line" :class="{ current: index === currentLyricIndex }" v-for="(line, index) in lyrics" :key="index" @click="selectLyric(index + 6)">{{ line }}</p>
        </div>
      </div>
    </div>

    <div class="music-content">
      <h3 class="recommendation-header">为你推荐</h3>

      <div class="recommendation-container">
        <div class="song-card" v-for="(song, index) in recommendations" :key="index" @click="selectSong(song)">
          <img :src="(song.album && song.album.picUrl) ? song.album.picUrl : 'https://p3.music.126.net/SyqjxPvTbK4Jt_lWjMZgKg==/109951165633973637.jpg'" alt="歌曲封面" class="song-cover">
          <div class="song-info">
            <h4 class="song-name">{{ song.name }}</h4>
            <p class="song-artist">{{ (song.artists && Array.isArray(song.artists)) ? song.artists.map(artist => artist.name).join(', ') : '未知艺术家' }}</p>
          </div>
        </div>
      </div>
    </div>

    <audio ref="audioPlayer" @timeupdate="updateProgress" @loadedmetadata="updateDuration" @ended="handleSongEnded"></audio>
  </div>
</template>

<script>
import { ref, reactive, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api'

export default {
  name: 'HomeView',
  setup() {
    const textInput = ref('')
    const imageFile = ref(null)
    const recommendations = ref([])
    const loading = ref(false)
    const audioPlayer = ref(null)
    const playingSongId = ref(null)
    const showPlayer = ref(false)
    const currentSong = ref(null)
    const isPlaying = ref(false)
    const currentTime = ref(0)
    const duration = ref(0)
    const volume = ref(0.75)
    const lyrics = ref([
      '当清晨的第一缕阳光',
      '轻柔地唤醒沉睡的大地',
      '我与此刻温柔相拥',
      '世界变得如此宁静',
      '在这无边的思绪里',
      '时间缓缓流逝',
      '如同指尖的细沙'
    ])
    const lyricTimes = ref([]) // 存储每句歌词的时间戳
    const currentLyricIndex = ref(2)

    const triggerFileInput = () => {
      const fileInput = document.querySelector('input[type="file"]')
      if (fileInput) fileInput.click()
    }

    const handleImageChange = (event) => {
      imageFile.value = event.target.files[0]
      if (imageFile.value) {
        getImageRecommendations()
      }
    }

    const getTextRecommendations = async () => {
      if (!textInput.value.trim()) {
        ElMessage.warning('请输入文本描述')
        return
      }

      loading.value = true
      try {
        // 调用API获取推荐
        const response = await api.getTextRecommendation(textInput.value)

        if (response.success) {
          console.log('获取到的文本推荐歌曲数据:', JSON.stringify(response.songs, null, 2))
          recommendations.value = response.songs
          if (response.songs && response.songs.length > 0) {
            showPlayer.value = true
            selectSong(response.songs[0])
          }
          ElMessage.success('获取推荐成功')
        } else {
          ElMessage.error(response.message || '获取推荐失败')
        }
      } catch (error) {
        console.error('获取推荐失败:', error)
        ElMessage.error('获取推荐失败，请稍后再试')
      } finally {
        loading.value = false
      }
    }

    const getImageRecommendations = async () => {
      if (!imageFile.value) {
        ElMessage.warning('请上传图片')
        return
      }

      loading.value = true
      try {
        // 调用API获取推荐
        const response = await api.getImageRecommendation(imageFile.value)

        if (response.success) {
          console.log('获取到的图片推荐歌曲数据:', JSON.stringify(response.songs, null, 2))
          recommendations.value = response.songs
          if (response.songs && response.songs.length > 0) {
            showPlayer.value = true
            selectSong(response.songs[0])
          }
          ElMessage.success('获取推荐成功')
        } else {
          ElMessage.error(response.message || '获取推荐失败')
        }
      } catch (error) {
        console.error('获取推荐失败:', error)
        ElMessage.error('获取推荐失败，请稍后再试')
      } finally {
        loading.value = false
      }
    }

    const selectSong = async (song) => {
      currentSong.value = song
      try {
        if (playingSongId.value === song.id) {
          // 如果是同一首歌，则暂停/播放切换
          togglePlay()
          return
        }

        // 获取歌曲URL
        const response = await api.getSongUrl(song.id)

        if (response.success && response.url) {
          audioPlayer.value.src = response.url
          audioPlayer.value.volume = volume.value
          audioPlayer.value.play()
          playingSongId.value = song.id
          isPlaying.value = true
          
          // 获取歌词
          await fetchLyrics(song.id)
        } else {
          ElMessage.error('无法获取歌曲播放链接')
        }
      } catch (error) {
        console.error('播放歌曲失败:', error)
        ElMessage.error('播放歌曲失败，请稍后再试')
      }
    }
    
    // 获取歌词
    const fetchLyrics = async (songId) => {
      try {
        console.log(`开始获取歌曲ID: ${songId}的歌词`)
        // 只使用普通歌词API
        const response = await api.getLyric(songId)
        console.log('歌词API响应:', JSON.stringify(response, null, 2))
        
        if (response && response.success && response.lrc && response.lrc.lyric) {
          console.log('使用普通歌词')
          parseLyrics(response.lrc.lyric, false)
        } else {
          console.log('获取歌词失败，使用默认歌词')
          // 如果获取歌词失败，使用默认歌词
          lyrics.value = [
            '暂无歌词',
            '请欣赏音乐',
            '...',
            '...',
            '...',
            '...',
            '...'
          ]
          currentLyricIndex.value = 0
        }
      } catch (error) {
        console.error('获取歌词失败:', error)
        // 使用默认歌词
        lyrics.value = [
          '暂无歌词',
          '请欣赏音乐',
          '...',
          '...',
          '...',
          '...',
          '...'
        ]
        currentLyricIndex.value = 0
      }
    }
    
    // 解析歌词
    const parseLyrics = (lyricText, isWordByWord) => {
      console.log('开始解析歌词，类型:', isWordByWord ? '逐字歌词' : '普通歌词')
      console.log('歌词文本:', lyricText)
      
      if (isWordByWord) {
        // 解析逐字歌词
        try {
          const parsedLyrics = []
          const lines = lyricText.split('\n')
          
          for (const line of lines) {
            if (line.startsWith('[') && line.includes(']')) {
              // 提取时间戳和歌词
              const timeMatch = line.match(/^\[(\d+),(\d+)\]/)
              if (timeMatch) {
                const startTime = parseInt(timeMatch[1])
                const duration = parseInt(timeMatch[2])
                const text = line.replace(/^\[\d+,\d+\]/, '')
                
                if (text.trim()) {
                  parsedLyrics.push({
                    time: startTime,
                    duration: duration,
                    text: text.trim()
                  })
                }
              }
            }
          }
          
          // 按时间排序
          parsedLyrics.sort((a, b) => a.time - b.time)
          
          // 更新歌词数据
          lyrics.value = parsedLyrics.map(item => item.text)
          lyricTimes.value = parsedLyrics.map(item => item.time)
          currentLyricIndex.value = 0
          
          console.log('逐字歌词解析成功:', JSON.stringify(parsedLyrics, null, 2))
        } catch (error) {
          console.error('解析逐字歌词失败:', error)
          parseLyrics(lyricText, false) // 尝试按普通歌词解析
        }
      } else {
        // 解析普通歌词
        try {
          const parsedLyrics = []
          const lines = lyricText.split('\n')
          
          for (const line of lines) {
            if (line.startsWith('[') && line.includes(']')) {
              // 提取时间戳和歌词
              const timeMatch = line.match(/^\[(\d{2}):(\d{2})\.(\d{2,3})\]/)
              if (timeMatch) {
                const minutes = parseInt(timeMatch[1])
                const seconds = parseInt(timeMatch[2])
                const milliseconds = parseInt(timeMatch[3])
                const time = minutes * 60 * 1000 + seconds * 1000 + milliseconds
                const text = line.replace(/^\[\d{2}:\d{2}\.\d{2,3}\]/, '')
                
                if (text.trim()) {
                  parsedLyrics.push({
                    time: time,
                    text: text.trim()
                  })
                }
              }
            }
          }
          
          // 按时间排序
          parsedLyrics.sort((a, b) => a.time - b.time)
          
          // 更新歌词数据
          lyrics.value = parsedLyrics.map(item => item.text)
          lyricTimes.value = parsedLyrics.map(item => item.time)
          currentLyricIndex.value = 0
          
          console.log('普通歌词解析成功:', JSON.stringify(parsedLyrics, null, 2))
        } catch (error) {
          console.error('解析普通歌词失败:', error)
          // 使用默认歌词
          lyrics.value = [
            '暂无歌词',
            '请欣赏音乐',
            '...',
            '...',
            '...',
            '...',
            '...'
          ]
          currentLyricIndex.value = 0
        }
      }
    }

    const togglePlay = () => {
      if (!audioPlayer.value.src) {
        if (recommendations.value.length > 0) {
          selectSong(recommendations.value[0])
        }
        return
      }

      if (isPlaying.value) {
        audioPlayer.value.pause()
        isPlaying.value = false
      } else {
        audioPlayer.value.play()
        isPlaying.value = true
      }
    }

    const previousSong = () => {
      const currentIndex = recommendations.value.findIndex(song => song.id === currentSong.value.id)
      if (currentIndex > 0) {
        selectSong(recommendations.value[currentIndex - 1])
      } else if (recommendations.value.length > 0) {
        selectSong(recommendations.value[recommendations.value.length - 1])
      }
    }

    const nextSong = () => {
      const currentIndex = recommendations.value.findIndex(song => song.id === currentSong.value.id)
      if (currentIndex < recommendations.value.length - 1) {
        selectSong(recommendations.value[currentIndex + 1])
      } else if (recommendations.value.length > 0) {
        selectSong(recommendations.value[0])
      }
    }

    const handleSongEnded = () => {
      nextSong()
    }

    const updateProgress = () => {
      if (audioPlayer.value) {
        currentTime.value = audioPlayer.value.currentTime
      }
    }

    const updateDuration = () => {
      if (audioPlayer.value) {
        duration.value = audioPlayer.value.duration
      }
    }

    const seekTo = (event) => {
      if (!audioPlayer.value || !duration.value) return

      const progressBar = event.currentTarget
      const pos = (event.pageX - progressBar.getBoundingClientRect().left) / progressBar.offsetWidth
      audioPlayer.value.currentTime = pos * duration.value
    }

    const setVolume = (event) => {
      const volumeSlider = event.currentTarget
      const pos = (event.pageX - volumeSlider.getBoundingClientRect().left) / volumeSlider.offsetWidth
      volume.value = pos
      if (audioPlayer.value) {
        audioPlayer.value.volume = volume.value
      }
    }

    const formatTime = (seconds) => {
      if (!seconds || isNaN(seconds)) return '0:00'

      const mins = Math.floor(seconds / 60)
      const secs = Math.floor(seconds % 60)
      return `${mins}:${secs < 10 ? '0' : ''}${secs}`
    }

    const selectLyric = (index) => {
      currentLyricIndex.value = index
    }

    const generateMoreRecommendations = () => {
      ElMessage.info('AI功能正在开发中，敬请期待！')
    }

    const progressPercentage = ref(0)

    // 监听当前播放时间变化，更新进度条和歌词
    const updateProgressPercentage = () => {
      if (duration.value > 0) {
        progressPercentage.value = (currentTime.value / duration.value) * 100
      }
      
      // 更新歌词
      updateLyricIndex()
    }
    
    // 更新歌词索引
    const updateLyricIndex = () => {
      if (lyricTimes.value.length === 0) return
      
      const currentTimeMs = currentTime.value * 1000 // 转换为毫秒
      
      // 找到当前应该显示的歌词
      for (let i = lyricTimes.value.length - 1; i >= 0; i--) {
        if (currentTimeMs >= lyricTimes.value[i]) {
          if (currentLyricIndex.value !== i) {
            // 调整索引，减去6行以修正偏差
            const adjustedIndex = Math.max(0, i)
            currentLyricIndex.value = adjustedIndex
            // 滚动到当前歌词
            scrollToCurrentLyric()
          }
          break
        }
      }
    }
    
    // 滚动到当前歌词
    const scrollToCurrentLyric = () => {
      const lyricsContainer = document.querySelector('.lyrics-container')
      if (lyricsContainer) {
        const currentLyricElement = lyricsContainer.children[currentLyricIndex.value-6]
        if (currentLyricElement) {
          // 计算滚动位置，使当前歌词位于容器中间
          const containerHeight = lyricsContainer.clientHeight
          const elementTop = currentLyricElement.offsetTop
          const elementHeight = currentLyricElement.clientHeight
          // 将当前歌词滚动到容器的顶部附近，留出一些空间
          
          const scrollTop = elementTop - 200
          
          lyricsContainer.scrollTo({
            top: scrollTop,
            behavior: 'smooth'
          })
        }
      }
    }

    // 使用watch来监听currentTime变化
    watch(currentTime, updateProgressPercentage)

    return {
      textInput,
      imageFile,
      recommendations,
      loading,
      audioPlayer,
      playingSongId,
      showPlayer,
      currentSong,
      isPlaying,
      currentTime,
      duration,
      volume,
      lyrics,
      currentLyricIndex,
      progressPercentage,
      lyricTimes,
      triggerFileInput,
      handleImageChange,
      getTextRecommendations,
      getImageRecommendations,
      selectSong,
      fetchLyrics,
      parseLyrics,
      togglePlay,
      previousSong,
      nextSong,
      handleSongEnded,
      updateProgress,
      updateDuration,
      updateLyricIndex,
      scrollToCurrentLyric,
      seekTo,
      setVolume,
      formatTime,
      selectLyric,
      generateMoreRecommendations
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
  padding: 2rem 0;
  min-height: 100vh;
}

/* ========== 页面一：情感输入主界面 ========== */
.emotion-input-page {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 5rem 2rem;
  background: var(--bg-gradient);
  position: relative;
  overflow: hidden;
  min-height: 800px;
  width: 100%;
}

.page-header {
  text-align: center;
  margin-bottom: 3rem;
  z-index: 2;
}

.emotion-title {
  font-size: 2.75rem;
  font-weight: 800;
  color: var(--text-dark);
  margin-bottom: 0.75rem;
}

.title-decoration {
  width: 30%;
  height: 2px;
  background: linear-gradient(to right, transparent, var(--primary-color), transparent);
  margin: 0 auto;
  border-radius: 1px;
}

.input-area {
  width: 60%;
  max-width: 700px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2rem;
  z-index: 2;
}

.input-group {
  width: 100%;
  display: flex;
  gap: 15px;
}

.text-input-container {
  flex: 1;
  position: relative;
}

.text-input {
  width: 100%;
  padding: 1.25rem;
  border: 1px solid #e1d9d1;
  border-radius: var(--border-radius);
  background: white;
  font-size: 1.1rem;
  color: var(--text-dark);
  transition: var(--transition);
}

.text-input::placeholder {
  color: #c0bbbc;
}

.text-input:focus {
  outline: none;
  border-color: var(--secondary-color);
  box-shadow: 0 0 0 3px rgba(168, 216, 234, 0.25);
}

.soulmate-btn {
  padding: 0 2rem;
  background: linear-gradient(135deg, var(--primary-color), #ffc6d1);
  color: white;
  border: none;
  border-radius: var(--border-radius);
  font-size: 1.2rem;
  font-weight: 600;
  cursor: pointer;
  transition: var(--transition);
  box-shadow: 0 4px 15px rgba(255, 182, 193, 0.35);
  display: flex;
  align-items: center;
  gap: 10px;
}

.soulmate-btn:hover {
  transform: translateY(-3px);
  box-shadow: 0 7px 20px rgba(255, 182, 193, 0.5);
}

.upload-container {
  width: 100%;
  display: flex;
  justify-content: center;
}

.upload-box {
  width: 100%;
  padding: 1.5rem;
  background: linear-gradient(120deg, #fef8f9, #f8f4f0);
  border-radius: var(--border-radius);
  border: 1px dashed #e4dcd0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  transition: var(--transition);
  cursor: pointer;
}

.upload-box:hover {
  box-shadow: var(--hover-shadow);
  border-color: var(--primary-color);
  transform: translateY(-2px);
  background: linear-gradient(120deg, #fffbfc, #fbf7f3);
}

.upload-icon {
  width: 60px;
  height: 60px;
  background: linear-gradient(135deg, var(--primary-color), #ffc6d1);
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
  color: white;
  font-size: 1.5rem;
  box-shadow: 0 4px 15px rgba(255, 182, 193, 0.35);
}

.upload-text {
  font-size: 1rem;
  color: var(--text-dark);
  text-align: center;
}

.ai-hint {
  position: absolute;
  bottom: 2rem;
  font-size: 0.9rem;
  color: #a5a1a0;
}

/* 装饰元素 */
.decoration-element {
  position: absolute;
  opacity: 0.15;
}

.circle-large {
  width: 300px;
  height: 300px;
  border-radius: 50%;
  background: var(--primary-color);
  top: -80px;
  left: -80px;
}

.circle-small {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background: var(--secondary-color);
  right: 50px;
  bottom: -30px;
}

/* ========== 页面二：音乐播放界面 ========== */
.music-player-page {
  padding: 3rem;
  background: var(--bg-gradient);
  position: relative;
  overflow: hidden;
  min-height: 800px;
  width: 100%;
}

.player-container {
  display: flex;
  gap: 3rem;
  margin-bottom: 3rem;
  z-index: 2;
  position: relative;
}

.album-cover {
  flex-shrink: 0;
  width: 250px;
  height: 250px;
  border-radius: var(--border-radius);
  overflow: hidden;
  box-shadow: var(--card-shadow);
  position: relative;
}

.album-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.player-controls {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.track-info {
  margin-bottom: 1rem;
}

.track-name {
  font-size: 1.6rem;
  font-weight: 700;
  color: var(--text-dark);
  margin-bottom: 0.25rem;
}

.artist-name {
  font-size: 1.1rem;
  color: #957f7a;
}

.controls-row {
  display: flex;
  align-items: center;
  gap: 1.8rem;
}

.control-btn {
  width: 50px;
  height: 50px;
  background: linear-gradient(135deg, var(--secondary-color), #b8e1f5);
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
  color: white;
  font-size: 1.2rem;
  border: none;
  cursor: pointer;
  transition: var(--transition);
  box-shadow: 0 4px 10px rgba(168, 216, 234, 0.4);
}

.control-btn:hover {
  transform: scale(1.1);
  box-shadow: 0 6px 15px rgba(168, 216, 234, 0.5);
}

.play-btn {
  width: 65px;
  height: 65px;
  background: linear-gradient(135deg, var(--primary-color), #ffc6d1);
  font-size: 1.5rem;
}

.progress-container {
  margin-top: 1.2rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.time-info {
  display: flex;
  justify-content: space-between;
  font-size: 0.9rem;
  color: #9c8f8b;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: rgba(232, 227, 223, 0.8);
  border-radius: 4px;
  position: relative;
  cursor: pointer;
}

.progress-filled {
  position: absolute;
  height: 100%;
  width: 30%;
  background: linear-gradient(to right, var(--primary-color), #ffc0cb);
  border-radius: 4px;
}

.volume-controls {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  margin-top: 1rem;
}

.volume-icon {
  color: var(--accent-color);
  font-size: 1.2rem;
}

.volume-slider {
  width: 120px;
  height: 6px;
  background: rgba(232, 227, 223, 0.8);
  border-radius: 3px;
  position: relative;
}

.volume-level {
  position: absolute;
  height: 100%;
  width: 75%;
  background: linear-gradient(to right, var(--secondary-color), #b1e0f2);
  border-radius: 3px;
}

.lyrics-container {
  background: rgba(173, 216, 230, 0.12);
  border-radius: var(--border-radius);
  padding: 1.5rem;
  margin-top: 1.5rem;
  height: 280px;
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: var(--primary-color) rgba(173, 216, 230, 0.1);
}

.lyrics-container::-webkit-scrollbar {
  width: 8px;
}

.lyrics-container::-webkit-scrollbar-thumb {
  background-color: var(--primary-color);
  border-radius: 4px;
}

.lyrics-line {
  font-size: 1.05rem;
  line-height: 1.8;
  margin-bottom: 0.4rem;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  transition: var(--transition);
}

.lyrics-line.current {
  background: rgba(255, 182, 193, 0.15);
  font-weight: 700;
  color: #e66479;
}

.music-content {
  z-index: 2;
  position: relative;
}

.recommendation-header {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-dark);
  margin-bottom: 1.5rem;
  position: relative;
  padding-left: 0.5rem;
}

.recommendation-header::after {
  content: '';
  position: absolute;
  bottom: -5px;
  left: 0;
  width: 45px;
  height: 3px;
  background: var(--primary-color);
  border-radius: 2px;
}

.recommendation-container {
  display: flex;
  flex-wrap: wrap;
  gap: 1.5rem;
}

.song-card {
  width: calc(25% - 1.5rem);
  background: white;
  border-radius: var(--border-radius);
  overflow: hidden;
  box-shadow: var(--card-shadow);
  transition: var(--transition);
  cursor: pointer;
}

.song-card:hover {
  box-shadow: var(--hover-shadow);
  transform: translateY(-8px);
}

.song-cover {
  width: 100%;
  height: 140px;
  object-fit: cover;
}

.song-info {
  padding: 1rem;
}

.song-name {
  font-weight: 600;
  margin-bottom: 0.3rem;
  color: var(--text-dark);
}

.song-artist {
  font-size: 0.9rem;
  color: #957f7a;
}


</style>