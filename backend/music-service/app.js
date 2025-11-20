const express = require('express');
const cors = require('cors');
const axios = require('axios');
const multer = require('multer');
const path = require('path');
const fs = require('fs');
require('dotenv').config();

// 导入网易云音乐API
const {
  song_url,
  search,
  song_detail,
  lyric,
  lyric_new
} = require('@neteaseapireborn/api');

const app = express();
const PORT = process.env.PORT || 3001;

// 配置跨域
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// 配置文件上传
const upload = multer({ dest: 'uploads/' });

// 网易云音乐API配置
const NETEASE_CONFIG = {
  cookie: process.env.NETEASE_COOKIE || '',
  realIP: process.env.NETEASE_IP || '116.25.146.177',
  randomCNIP: true
};

// 确保uploads目录存在
if (!fs.existsSync('uploads')) {
  fs.mkdirSync('uploads');
}

// 获取歌曲URL
app.get('/api/song/url', async (req, res) => {
  try {
    const { id } = req.query;
    if (!id) {
      return res.status(400).json({ success: false, message: '缺少歌曲ID' });
    }

    console.log(`尝试获取歌曲ID: ${id}的URL`);
    const result = await song_url({
      id,
      ...NETEASE_CONFIG
    });

    console.log('网易云API返回结果:', JSON.stringify(result, null, 2));

    if (result.status === 200 && result.body && result.body.data && result.body.data.length > 0) {
      return res.json({
        success: true,
        url: result.body.data[0].url
      });
    } else {
      console.error(`获取歌曲ID ${id} 失败，状态码: ${result.status}`);
      return res.status(404).json({
        success: false,
        message: '无法获取歌曲URL',
        debug: result
      });
    }
  } catch (error) {
    console.error('获取歌曲URL错误:', error);
    res.status(500).json({
      success: false,
      message: '服务器错误'
    });
  }
});

// 搜索歌曲
app.get('/api/search', async (req, res) => {
  try {
    const { keywords, limit = 10 } = req.query;
    if (!keywords) {
      return res.status(400).json({ success: false, message: '缺少搜索关键词' });
    }

    console.log(`搜索关键词: ${keywords}, 限制: ${limit}`);
    const result = await search({
      keywords,
      limit,
      ...NETEASE_CONFIG
    });

    console.log('搜索API返回结果:', JSON.stringify(result, null, 2));

    if (result.status === 200 && result.body && result.body.result && result.body.result.songs) {
      return res.json({
        success: true,
        songs: result.body.result.songs
      });
    } else {
      console.error(`搜索失败，状态码: ${result.status}`);
      return res.status(404).json({
        success: false,
        message: '搜索失败',
        debug: result
      });
    }
  } catch (error) {
    console.error('搜索歌曲错误:', error);
    res.status(500).json({
      success: false,
      message: '服务器错误'
    });
  }
});

// 获取歌曲详情
app.get('/api/song/detail', async (req, res) => {
  try {
    const { ids } = req.query;
    if (!ids) {
      return res.status(400).json({ success: false, message: '缺少歌曲ID' });
    }

    console.log(`获取歌曲详情，ID: ${ids}`);
    const result = await song_detail({
      ids,
      ...NETEASE_CONFIG
    });

    console.log('歌曲详情API返回结果:', JSON.stringify(result, null, 2));

    if (result.status === 200 && result.body && result.body.songs) {
      return res.json({
        success: true,
        songs: result.body.songs
      });
    } else {
      console.error(`获取歌曲详情失败，状态码: ${result.status}`);
      return res.status(404).json({
        success: false,
        message: '获取歌曲详情失败',
        debug: result
      });
    }
  } catch (error) {
    console.error('获取歌曲详情错误:', error);
    res.status(500).json({
      success: false,
      message: '服务器错误'
    });
  }
});

// 获取歌词
app.get('/api/lyric', async (req, res) => {
  try {
    const { id } = req.query;
    if (!id) {
      return res.status(400).json({ success: false, message: '缺少歌曲ID' });
    }

    console.log(`获取歌曲ID: ${id}的歌词`);
    const result = await lyric({
      id,
      ...NETEASE_CONFIG
    });

    console.log('歌词API返回结果:', JSON.stringify(result, null, 2));

    if (result.status === 200 && result.body && result.body.lrc) {
      return res.json({
        success: true,
        lrc: result.body.lrc
      });
    } else {
      console.error(`获取歌曲ID ${id}的歌词失败，状态码: ${result.status}`);
      return res.status(404).json({
        success: false,
        message: '无法获取歌词',
        debug: result
      });
    }
  } catch (error) {
    console.error('获取歌词错误:', error);
    res.status(500).json({
      success: false,
      message: '服务器错误'
    });
  }
});

// 获取逐字歌词
app.get('/api/lyric/new', async (req, res) => {
  try {
    const { id } = req.query;
    if (!id) {
      return res.status(400).json({ success: false, message: '缺少歌曲ID' });
    }

    console.log(`获取歌曲ID: ${id}的逐字歌词`);
    const result = await lyric_new({
      id,
      ...NETEASE_CONFIG
    });

    console.log('逐字歌词API返回结果:', JSON.stringify(result, null, 2));

    if (result.status === 200 && result.body && result.body.yrc) {
      return res.json({
        success: true,
        yrc: result.body.yrc
      });
    } else {
      console.error(`获取歌曲ID ${id}的逐字歌词失败，状态码: ${result.status}`);
      return res.status(404).json({
        success: false,
        message: '无法获取逐字歌词',
        debug: result
      });
    }
  } catch (error) {
    console.error('获取逐字歌词错误:', error);
    res.status(500).json({
      success: false,
      message: '服务器错误'
    });
  }
});

app.listen(PORT, () => {
  console.log(`音乐服务运行在端口 ${PORT}`);
});
