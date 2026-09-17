// pages/companion/game/match/match.js —— 对对消（点两个相同图案消除，三关难度）
const ICONS = ['🍎', '🍊', '🍇', '🍉', '🐱', '🐶', '🐰', '🐔', '🌸', '🌻', '🍓', '🥕'];

const LEVELS = [
  { level: 1, name: '第一关·热身', cols: 3, pairs: 3 },
  { level: 2, name: '第二关·进阶', cols: 4, pairs: 6 },
  { level: 3, name: '第三关·挑战', cols: 4, pairs: 8 },
];

Page({
  data: {
    cards: [],
    cols: 3,
    selected: -1,
    steps: 0,
    matchedCount: 0,
    totalPairs: 0,
    isComplete: false,
    isAllClear: false,
    isChecking: false,
    currentLevel: 1,
    levelName: '',
  },

  onLoad() {
    this.startLevel(1);
  },

  startLevel(level) {
    const cfg = LEVELS[level - 1];
    const icons = ICONS.slice(0, cfg.pairs);
    const pairs = [...icons, ...icons];
    const shuffled = pairs
      .map((icon, idx) => ({ id: idx, icon, pairId: icons.indexOf(icon), isMatched: false }))
      .sort(() => Math.random() - 0.5);
    this.setData({
      cards: shuffled,
      cols: cfg.cols,
      selected: -1,
      steps: 0,
      matchedCount: 0,
      totalPairs: cfg.pairs,
      isComplete: false,
      isAllClear: false,
      isChecking: false,
      currentLevel: level,
      levelName: cfg.name,
    });
  },

  tapCard(e) {
    if (this.data.isChecking) return;
    const index = e.currentTarget.dataset.index;
    const card = this.data.cards[index];
    if (card.isMatched) return;
    if (this.data.selected === index) {
      this.setData({ selected: -1 });
      return;
    }
    // 第一次选
    if (this.data.selected < 0) {
      this.setData({ selected: index });
      return;
    }
    // 第二次选，比对
    const first = this.data.cards[this.data.selected];
    this.setData({ isChecking: true, steps: this.data.steps + 1 });
    if (first.pairId === card.pairId) {
      // 配对成功，消除
      setTimeout(() => {
        const cards = [...this.data.cards];
        cards[this.data.selected] = { ...cards[this.data.selected], isMatched: true };
        cards[index] = { ...cards[index], isMatched: true };
        const matchedCount = cards.filter(c => c.isMatched).length / 2;
        this.setData({ cards, matchedCount, selected: -1, isChecking: false });
        if (matchedCount === this.data.totalPairs) {
          this._onLevelComplete();
        }
      }, 400);
    } else {
      // 配对失败，取消选中
      setTimeout(() => {
        this.setData({ selected: -1, isChecking: false });
      }, 600);
    }
  },

  // 提示：自动消除一对
  useHint() {
    const remaining = [];
    this.data.cards.forEach((c, i) => { if (!c.isMatched) remaining.push(i); });
    if (remaining.length < 2) return;
    // 找一对相同的
    for (let i = 0; i < remaining.length; i++) {
      for (let j = i + 1; j < remaining.length; j++) {
        if (this.data.cards[remaining[i]].pairId === this.data.cards[remaining[j]].pairId) {
          const cards = [...this.data.cards];
          cards[remaining[i]] = { ...cards[remaining[i]], isMatched: true };
          cards[remaining[j]] = { ...cards[remaining[j]], isMatched: true };
          const matchedCount = cards.filter(c => c.isMatched).length / 2;
          this.setData({ cards, matchedCount, selected: -1 });
          wx.showToast({ title: '已帮您消除一对', icon: 'none' });
          if (matchedCount === this.data.totalPairs) {
            this._onLevelComplete();
          }
          return;
        }
      }
    }
  },

  _onLevelComplete() {
    const cur = this.data.currentLevel;
    if (cur < LEVELS.length) {
      this.setData({ isComplete: true });
    } else {
      this.setData({ isComplete: true, isAllClear: true });
    }
    wx.vibrateShort && wx.vibrateShort({ type: 'medium' });
  },

  nextLevel() {
    this.startLevel(this.data.currentLevel + 1);
  },

  restart() {
    this.startLevel(this.data.currentLevel);
  },

  restartAll() {
    this.startLevel(1);
  },
});
