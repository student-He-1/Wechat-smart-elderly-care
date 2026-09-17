// pages/companion/audiobook/audiobook.js —— 听书戏曲（经典名著、评书相声、传统戏曲）
const CATEGORIES = [
  { key: 'novel', name: '经典名著', icon: '📚' },
  { key: 'pingshu', name: '评书相声', icon: '🎙️' },
  { key: 'opera', name: '传统戏曲', icon: '🎭' },
];

const AUDIOBOOKS = {
  novel: [
    { id: 1, title: '三国演义·桃园三结义', author: '经典名著片段', duration: '15:30', url: '/assets/audiobook/novel1.mp3' },
    { id: 2, title: '红楼梦·黛玉葬花', author: '经典名著片段', duration: '12:00', url: '/assets/audiobook/novel2.mp3' },
    { id: 3, title: '西游记·三打白骨精', author: '经典名著片段', duration: '18:20', url: '/assets/audiobook/novel3.mp3' },
    { id: 4, title: '水浒传·武松打虎', author: '经典名著片段', duration: '14:10', url: '/assets/audiobook/novel4.mp3' },
  ],
  pingshu: [
    { id: 1, title: '阿东读历史·第536集', author: '有声评书', duration: '20:00', url: '/assets/audiobook/阿东读历史 - 第536集.mp3' },
    { id: 2, title: '相声·报菜名', author: '经典相声', duration: '08:30', url: '/assets/audiobook/pingshu2.mp3' },
    { id: 3, title: '评书·杨家将精选', author: '传统评书', duration: '22:15', url: '/assets/audiobook/pingshu3.mp3' },
    { id: 4, title: '相声·五官争功', author: '经典相声', duration: '10:00', url: '/assets/audiobook/pingshu4.mp3' },
  ],
  opera: [
    { id: 1, title: '帝女花·香夭', author: '任剑辉、白雪仙', duration: '16:40', url: '/assets/audiobook/任剑辉、白雪仙 - 《帝女花》香夭.mp3' },
    { id: 2, title: '评剧·刘巧儿', author: '新派经典', duration: '18:00', url: '/assets/audiobook/opera2.mp3' },
    { id: 3, title: '豫剧·花木兰', author: '常派经典', duration: '20:30', url: '/assets/audiobook/opera3.mp3' },
    { id: 4, title: '越剧·梁山伯与祝英台', author: '经典选段', duration: '25:00', url: '/assets/audiobook/opera4.mp3' },
  ],
};

Page({
  data: {
    categories: CATEGORIES,
    activeKey: 'novel',
    list: AUDIOBOOKS.novel,
    currentIndex: 0,
    isPlaying: false,
    currentTime: 0,
    duration: 0,
    progress: 0,
    currentTimeText: '0:00',
    durationText: '',
  },

  onLoad() {
    this._list = AUDIOBOOKS.novel; // 内部同步变量，避免setData异步竞态
    this._createAudio();
  },

  // 创建新的音频实例（每次切换曲目都新建，杜绝旧实例状态残留）
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
    audio.onEnded(() => this.nextTrack());
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
    audio.onError(() => {
      wx.showToast({ title: '音频文件待放入，请稍后再试', icon: 'none' });
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

  switchCategory(e) {
    const key = e.currentTarget.dataset.key;
    this._list = AUDIOBOOKS[key] || [];
    this._createAudio(); // 销毁旧实例，新建空实例
    this.setData({
      activeKey: key,
      list: this._list,
      currentIndex: 0,
      isPlaying: false,
      currentTime: 0,
      progress: 0,
      currentTimeText: '0:00',
    });
  },

  playTrack(e) {
    const index = e.currentTarget.dataset.index;
    this.setData({ currentIndex: index });
    this._playCurrent(index);
  },

  _playCurrent(idx) {
    const index = (typeof idx === 'number') ? idx : this.data.currentIndex;
    const track = this._list[index];
    if (!track) return;
    this.setData({
      currentTime: 0,
      progress: 0,
      currentTimeText: '0:00',
      durationText: track.duration,
    });
    // 每次播放都新建音频实例，彻底杜绝旧曲目状态残留
    this._createAudio();
    this._audio.src = track.url;
    this._audio.play();
  },

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

  prevTrack() {
    let idx = this.data.currentIndex - 1;
    if (idx < 0) idx = this.data.list.length - 1;
    this.setData({ currentIndex: idx });
    this._playCurrent(idx);
  },

  nextTrack() {
    let idx = this.data.currentIndex + 1;
    if (idx >= this.data.list.length) idx = 0;
    this.setData({ currentIndex: idx });
    this._playCurrent(idx);
  },

  onSliderChanging(e) {
    // 拖动中实时更新进度条显示
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

  _formatTime(sec) {
    sec = Math.floor(sec || 0);
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return `${m}:${s < 10 ? '0' + s : s}`;
  },
});
