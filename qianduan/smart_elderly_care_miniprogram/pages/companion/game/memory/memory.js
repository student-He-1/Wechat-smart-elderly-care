// pages/companion/game/memory/memory.js —— 翻牌记忆游戏（适老化，三关难度）
const CARD_ICONS = ['🍎', '🍊', '🍇', '🍉', '🐱', '🐶', '🐰', '🐔'];

// 关卡配置：列数、对数
const LEVELS = [
  { level: 1, cols: 2, pairs: 2, name: '第一关·热身' },
  { level: 2, cols: 4, pairs: 6, name: '第二关·进阶' },
  { level: 3, cols: 4, pairs: 8, name: '第三关·挑战' },
];

Page({
  data: {
    cards: [],
    steps: 0,
    matchedCount: 0,
    totalPairs: 0,
    currentLevel: 1,
    levelName: '',
    cols: 2,
    isComplete: false,
    isChecking: false,
    isAllClear: false, // 全部通关
  },

  onLoad() {
    this.startLevel(1);
  },

  // 开始指定关卡
  startLevel(level) {
    const cfg = LEVELS[level - 1];
    const icons = CARD_ICONS.slice(0, cfg.pairs);
    const pairs = [...icons, ...icons];
    const shuffled = pairs
      .map((icon, idx) => ({
        id: idx,
        icon,
        pairId: icons.indexOf(icon),
        isFlipped: false,
        isMatched: false,
      }))
      .sort(() => Math.random() - 0.5);
    this.setData({
      cards: shuffled,
      steps: 0,
      matchedCount: 0,
      totalPairs: cfg.pairs,
      currentLevel: level,
      levelName: cfg.name,
      cols: cfg.cols,
      isComplete: false,
      isChecking: false,
      isAllClear: false,
    });
    this._flippedIndices = [];
  },

  // 点击翻牌
  flipCard(e) {
    if (this.data.isChecking) return;
    const index = e.currentTarget.dataset.index;
    const card = this.data.cards[index];
    if (card.isFlipped || card.isMatched) return;

    const cards = [...this.data.cards];
    cards[index] = { ...card, isFlipped: true };
    this._flippedIndices.push(index);
    this.setData({ cards });

    if (this._flippedIndices.length === 2) {
      this.setData({ isChecking: true, steps: this.data.steps + 1 });
      const [i1, i2] = this._flippedIndices;
      if (cards[i1].pairId === cards[i2].pairId) {
        // 配对成功：消掉
        setTimeout(() => {
          const updated = [...this.data.cards];
          updated[i1] = { ...updated[i1], isMatched: true };
          updated[i2] = { ...updated[i2], isMatched: true };
          const matchedCount = updated.filter(c => c.isMatched).length / 2;
          this.setData({ cards: updated, matchedCount, isChecking: false });
          this._flippedIndices = [];
          // 本关完成
          if (matchedCount === this.data.totalPairs) {
            this._onLevelComplete();
          }
        }, 500);
      } else {
        // 配对失败，翻回
        setTimeout(() => {
          const updated = [...this.data.cards];
          updated[i1] = { ...updated[i1], isFlipped: false };
          updated[i2] = { ...updated[i2], isFlipped: false };
          this.setData({ cards: updated, isChecking: false });
          this._flippedIndices = [];
        }, 900);
      }
    }
  },

  // 本关完成
  _onLevelComplete() {
    const cur = this.data.currentLevel;
    if (cur < LEVELS.length) {
      this.setData({ isComplete: true });
      wx.vibrateShort && wx.vibrateShort({ type: 'medium' });
    } else {
      // 全部通关
      this.setData({ isComplete: true, isAllClear: true });
      wx.vibrateShort && wx.vibrateShort({ type: 'heavy' });
    }
  },

  // 下一关
  nextLevel() {
    this.startLevel(this.data.currentLevel + 1);
  },

  // 重新开始当前关
  restart() {
    this.startLevel(this.data.currentLevel);
  },

  // 重玩全部（从第一关开始）
  restartAll() {
    this.startLevel(1);
  },
});
