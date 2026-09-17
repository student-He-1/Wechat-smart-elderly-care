// pages/companion/music/music.js —— 舒缓轻音乐播放器（适老化）
const { MUSIC_LIST } = require('../../../utils/music-config');

Page({
  data: {
    musicList: MUSIC_LIST.map(m => ({ ...m, favorite: false })),
    currentIndex: 0,
    isPlaying: false,
    currentTime: 0,
    duration: 0,
    progress: 0,
    currentTimeText: '0:00',
    durationText: '',
    playMode: 'order', // order / single
  },

  onLoad() {
    this._createAudio();
    // 恢复收藏状态
    const favs = wx.getStorageSync('music_favorites') || [];
    const list = this.data.musicList.map(m => ({ ...m, favorite: favs.includes(m.id) }));
    this.setData({ musicList: list });
  },

  _createAudio() {
    if (this._audio) {
      this._audio.stop();
      this._audio.destroy();
      this._audio = null;
    }
    const audio = wx.createInnerAudioContext();
    audio.onPlay(() => this.setData({ isPlaying: true }));
    audio.onPause(() => this.setData({ isPlaying: false }));
    audio.onStop(() => this.setData({ isPlaying: false, currentTime: 0, progress: 0 }));
    audio.onEnded(() => this._onEnded());
    audio.onTimeUpdate(() => {
      const cur = audio.currentTime || 0;
      const dur = audio.duration || 0;
      this.setData({
        currentTime: cur,
        duration: dur,
        progress: dur > 0 ? (cur / dur) * 100 : 0,
        currentTimeText: this._formatTime(cur),
        durationText: this._formatTime(dur),
      });
    });
    audio.onError((err) => {
      console.error('音乐播放错误:', err);
      wx.showToast({ title: '音乐文件暂未放入，请稍后再试', icon: 'none' });
      this.setData({ isPlaying: false });
    });
    this._audio = audio;
  },

  onUnload() {
    if (this._audio) {
      this._audio.stop();
      this._audio.destroy();
      this._audio = null;
    }
  },

  // 播放指定歌曲
  playMusic(e) {
    const index = e.currentTarget.dataset.index;
    this.setData({ currentIndex: index });
    this._playCurrent(index);
  },

  _playCurrent(idx) {
    const index = (typeof idx === 'number') ? idx : this.data.currentIndex;
    const music = this.data.musicList[index];
    if (!music) return;
    this.setData({
      currentTime: 0,
      progress: 0,
      currentTimeText: '0:00',
      durationText: music.duration || '',
    });
    // 每次播放新建实例，杜绝旧曲目残留
    this._createAudio();
    this._audio.src = music.url;
    this._audio.play();
  },

  // 播放/暂停切换
  togglePlay() {
    if (this.data.isPlaying) {
      this._audio.pause();
    } else {
      if (!this._audio.src) {
        this._playCurrent();
      } else {
        this._audio.play();
      }
    }
  },

  // 上一首
  prevMusic() {
    let idx = this.data.currentIndex - 1;
    if (idx < 0) idx = this.data.musicList.length - 1;
    this.setData({ currentIndex: idx });
    this._playCurrent(idx);
  },

  // 下一首
  nextMusic() {
    let idx = this.data.currentIndex + 1;
    if (idx >= this.data.musicList.length) idx = 0;
    this.setData({ currentIndex: idx });
    this._playCurrent(idx);
  },

  // 播放结束
  _onEnded() {
    if (this.data.playMode === 'single') {
      this._playCurrent(); // 单曲循环
    } else {
      this.nextMusic(); // 顺序播放
    }
  },

  // 切换播放模式
  toggleMode() {
    const mode = this.data.playMode === 'order' ? 'single' : 'order';
    this.setData({ playMode: mode });
    wx.showToast({ title: mode === 'single' ? '单曲循环' : '顺序播放', icon: 'none' });
  },

  // 收藏/取消收藏
  toggleFavorite(e) {
    const index = e.currentTarget.dataset.index;
    const list = [...this.data.musicList];
    list[index].favorite = !list[index].favorite;
    this.setData({ musicList: list });
    const favs = list.filter(m => m.favorite).map(m => m.id);
    wx.setStorageSync('music_favorites', favs);
    wx.showToast({ title: list[index].favorite ? '已收藏' : '已取消收藏', icon: 'none' });
  },

  // 进度条拖动
  onSliderChanging(e) {
    const value = e.detail.value;
    this.setData({ progress: value });
  },

  onSliderChange(e) {
    const value = e.detail.value;
    const dur = this._audio.duration || 0;
    if (dur > 0) {
      this._audio.seek((value / 100) * dur);
    } else {
      wx.showToast({ title: '音频加载中，请稍候', icon: 'none' });
    }
  },

  // 格式化时间
  _formatTime(sec) {
    sec = Math.floor(sec || 0);
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return `${m}:${s < 10 ? '0' + s : s}`;
  },
});
