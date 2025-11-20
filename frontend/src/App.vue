<template>
  <div id="app">
    <div class="title-container">
      <h1 class="main-title">情感音乐播放器</h1>
      <div class="highlight-bar"></div>
    </div>
    <div class="nav-container">
      <router-link to="/" class="nav-link" :class="{ active: $route.path === '/' }">情感输入</router-link>
      <router-link to="/history" class="nav-link" :class="{ active: $route.path === '/history' }">推荐历史</router-link>
    </div>
    <div class="content-container">
      <router-view/>
    </div>
  </div>
</template>

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
</style>
