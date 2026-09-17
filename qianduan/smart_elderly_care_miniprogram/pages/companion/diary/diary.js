// pages/companion/diary/diary.js —— 心情日记
const MOODS = [
  { key: 'happy', emoji: '😊', text: '开心', color: '#fbbf24' },
  { key: 'calm', emoji: '😌', text: '平静', color: '#60a5fa' },
  { key: 'sad', emoji: '😢', text: '难过', color: '#a78bfa' },
  { key: 'angry', emoji: '😠', text: '生气', color: '#f87171' },
  { key: 'tired', emoji: '😴', text: '疲惫', color: '#94a3b8' },
];

const STORAGE_KEY = 'companion_diaries';

Page({
  data: {
    moods: MOODS,
    diaries: [],
    filteredDiaries: [],
    showEditor: false,
    selectedMood: null,
    diaryContent: '',
    filterKey: 'all',
    filterOptions: [
      { key: 'all', text: '全部' },
      ...MOODS.map(m => ({ key: m.key, text: m.text })),
    ],
  },

  onLoad() {
    this.loadDiaries();
  },

  onShow() {
    this.loadDiaries();
  },

  // 加载日记
  loadDiaries() {
    const list = wx.getStorageSync(STORAGE_KEY) || [];
    this.setData({ diaries: list });
    this.applyFilter();
  },

  // 打开写日记
  openEditor() {
    this.setData({ showEditor: true, selectedMood: null, diaryContent: '' });
  },

  // 关闭写日记
  closeEditor() {
    this.setData({ showEditor: false });
  },

  // 选择心情
  selectMood(e) {
    const key = e.currentTarget.dataset.key;
    this.setData({ selectedMood: key });
  },

  // 输入内容
  bindInput(e) {
    this.setData({ diaryContent: e.detail.value });
  },

  // 保存日记
  saveDiary() {
    if (!this.data.selectedMood) {
      wx.showToast({ title: '请先选一个心情', icon: 'none' });
      return;
    }
    const content = this.data.diaryContent.trim();
    if (!content) {
      wx.showToast({ title: '写点什么吧', icon: 'none' });
      return;
    }
    const mood = MOODS.find(m => m.key === this.data.selectedMood);
    const now = new Date();
    const date = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
    const time = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
    const entry = {
      id: Date.now(),
      mood: mood.key,
      moodText: mood.text,
      emoji: mood.emoji,
      content,
      date,
      time,
    };
    const list = [entry, ...this.data.diaries];
    wx.setStorageSync(STORAGE_KEY, list);
    this.setData({ diaries: list, showEditor: false });
    this.applyFilter();
    wx.showToast({ title: '已保存', icon: 'success' });
  },

  // 删除日记
  deleteDiary(e) {
    const id = e.currentTarget.dataset.id;
    wx.showModal({
      title: '删除日记',
      content: '确定要删除这条日记吗？',
      confirmText: '删除',
      confirmColor: '#ef4444',
      success: (res) => {
        if (res.confirm) {
          const list = this.data.diaries.filter(d => d.id !== id);
          wx.setStorageSync(STORAGE_KEY, list);
          this.setData({ diaries: list });
          this.applyFilter();
          wx.showToast({ title: '已删除', icon: 'none' });
        }
      },
    });
  },

  // 筛选
  changeFilter(e) {
    const key = e.currentTarget.dataset.key;
    this.setData({ filterKey: key });
    this.applyFilter();
  },

  applyFilter() {
    const { diaries, filterKey } = this.data;
    const filtered = filterKey === 'all' ? diaries : diaries.filter(d => d.mood === filterKey);
    this.setData({ filteredDiaries: filtered });
  },

  stopPropagation() {},
});
