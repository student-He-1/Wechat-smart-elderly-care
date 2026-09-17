// chat.js —— 关爱陪伴首页
const { MUSIC_LIST } = require('../../utils/music-config');
const { PHOTOS } = require('../../utils/album-config');

// 每日暖心语录（老人向）
const DAILY_QUOTES = [
  '今天天气好，出去走走吧，晒晒太阳对身体好',
  '孩子们都在忙，您照顾好自己就是对他们最大的支持',
  '吃好睡好，身体棒棒，比什么都强',
  '今天给自己做顿好吃的，好好犒劳一下自己',
  '老朋友多久没联系了？打个电话聊聊吧',
  '年纪大了更要多笑笑，笑一笑十年少',
  '慢慢来，不着急，日子一天一天过',
  '您辛苦了一辈子，现在该享享清福了',
  '多喝温水，少操心，身体是自己的',
  '今天的您真棒，又开开心心过了一天',
  '公园里的花开了，去看看吧，心情会变好',
  '中午记得睡个午觉，下午精神好',
  '儿女再忙也惦记着您，您好好的他们就放心',
  '今天想吃什么就吃什么，别舍不得',
];

Page({
  data: {
    showAiPicker: false,
    ballX: 300,
    ballY: 500,
    photoCount: 0,
    diaryCount: 0,
    musicCount: 0,
    dailyQuote: ''
  },

  onLoad() {
    const win = wx.getWindowInfo ? wx.getWindowInfo() : wx.getSystemInfoSync();
    const ballSize = 38;
    // 每日语录：根据日期选一条，每天不一样
    const today = new Date();
    const dayOfYear = Math.floor((today - new Date(today.getFullYear(), 0, 0)) / 86400000);
    const quote = DAILY_QUOTES[dayOfYear % DAILY_QUOTES.length];
    this.setData({
      ballX: win.windowWidth - ballSize - 12,
      ballY: win.windowHeight - ballSize - 340,
      dailyQuote: quote
    });
    this._refreshStats();
  },

  onShow() {
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().setData({ selected: 2 });
    }
    this._refreshStats();
  },

  // 刷新顶部统计数字（照片从公共配置读，日记从本地存储读，音乐从公共配置读）
  _refreshStats() {
    const diaries = wx.getStorageSync('companion_diaries') || [];
    this.setData({
      photoCount: PHOTOS.length,
      diaryCount: diaries.length,
      musicCount: MUSIC_LIST.length
    });
  },

  showDemo() {
    wx.showToast({ title: '演示功能，敬请期待', icon: 'none' });
  },

  goToTalk() {
    wx.navigateTo({ url: '/pages/chat/talk/talk?type=companion' });
  },

  goMusic() {
    wx.navigateTo({ url: '/pages/companion/music/music' });
  },

  goGameSelect() {
    wx.navigateTo({ url: '/pages/companion/game/index/index' });
  },

  goAlbum() {
    wx.navigateTo({ url: '/pages/companion/album/album' });
  },

  goDiary() {
    wx.navigateTo({ url: '/pages/companion/diary/diary' });
  },

  goAudiobook() {
    wx.navigateTo({ url: '/pages/companion/audiobook/audiobook' });
  },

  onBallMove(e) {
    this._ballX = e.detail.x;
  },

  onBallEnd() {
    const win = wx.getWindowInfo ? wx.getWindowInfo() : wx.getSystemInfoSync();
    const ballSize = 38;
    const curX = this._ballX !== undefined ? this._ballX : (win.windowWidth - ballSize - 12);
    const snapX = curX < win.windowWidth / 2 ? 12 : win.windowWidth - ballSize - 12;
    this.setData({ ballX: snapX });
  },

  openAiPicker() {
    this.setData({ showAiPicker: true });
  },

  closeAiPicker() {
    this.setData({ showAiPicker: false });
  },

  pickCompanion() {
    this.setData({ showAiPicker: false });
    wx.navigateTo({ url: '/pages/chat/talk/talk?type=companion' });
  },

  pickHealth() {
    this.setData({ showAiPicker: false });
    wx.navigateTo({ url: '/pages/health/assistant/assistant' });
  }
});
