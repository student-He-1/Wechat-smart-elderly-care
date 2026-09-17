// pages/companion/game/sudoku/sudoku.js —— 趣味数独（4×4简化版，三关难度，适老化）

// 关卡配置：每关2道题，空格数递增
const LEVELS = [
  {
    level: 1, name: '第一关·入门',
    puzzles: [
      { puzzle: [1,2,0,4, 3,4,1,0, 0,1,4,3, 4,3,2,0], solution: [1,2,3,4, 3,4,1,2, 2,1,4,3, 4,3,2,1] },
      { puzzle: [0,1,4,3, 4,3,0,1, 1,0,3,4, 3,4,1,0], solution: [2,1,4,3, 4,3,2,1, 1,2,3,4, 3,4,1,2] },
    ],
  },
  {
    level: 2, name: '第二关·进阶',
    puzzles: [
      { puzzle: [1,0,3,0, 0,4,0,2, 2,0,4,0, 0,3,0,1], solution: [1,2,3,4, 3,4,1,2, 2,1,4,3, 4,3,2,1] },
      { puzzle: [0,1,0,3, 4,0,2,0, 0,2,0,4, 3,0,1,0], solution: [2,1,4,3, 4,3,2,1, 1,2,3,4, 3,4,1,2] },
    ],
  },
  {
    level: 3, name: '第三关·挑战',
    puzzles: [
      { puzzle: [1,2,0,0, 0,4,0,0, 0,0,4,0, 0,0,2,1], solution: [1,2,3,4, 3,4,1,2, 2,1,4,3, 4,3,2,1] },
      { puzzle: [0,0,4,0, 4,0,0,1, 1,0,0,4, 0,4,0,0], solution: [2,1,4,3, 4,3,2,1, 1,2,3,4, 3,4,1,2] },
    ],
  },
];

Page({
  data: {
    board: [],
    fixed: [],
    errors: [],
    selectedIndex: -1,
    numbers: [1, 2, 3, 4],
    isComplete: false,
    isAllClear: false,
    currentLevel: 1,
    levelName: '',
    _puzzle: null, // 当前题目对象
  },

  onLoad() {
    this.startLevel(1);
  },

  // 开始指定关卡
  startLevel(level) {
    const cfg = LEVELS[level - 1];
    const p = cfg.puzzles[Math.floor(Math.random() * cfg.puzzles.length)];
    this.setData({
      board: [...p.puzzle],
      fixed: p.puzzle.map(n => n !== 0),
      errors: new Array(16).fill(false),
      selectedIndex: -1,
      isComplete: false,
      isAllClear: false,
      currentLevel: level,
      levelName: cfg.name,
    });
    this._puzzle = p;
  },

  // 选中格子
  selectCell(e) {
    const index = e.currentTarget.dataset.index;
    if (this.data.fixed[index]) return;
    this.setData({ selectedIndex: index });
  },

  // 填入数字
  fillNumber(e) {
    const num = e.currentTarget.dataset.num;
    const idx = this.data.selectedIndex;
    if (idx < 0) {
      wx.showToast({ title: '请先点一个空格', icon: 'none' });
      return;
    }
    const board = [...this.data.board];
    const errors = [...this.data.errors];
    board[idx] = num;
    errors[idx] = num !== this._puzzle.solution[idx];
    this.setData({ board, errors });
    this._checkComplete();
  },

  // 清除当前格
  clearCell() {
    const idx = this.data.selectedIndex;
    if (idx < 0) return;
    const board = [...this.data.board];
    const errors = [...this.data.errors];
    board[idx] = 0;
    errors[idx] = false;
    this.setData({ board, errors, selectedIndex: -1 });
  },

  // 提示：自动填一个空格
  useHint() {
    const emptyIndices = [];
    this.data.board.forEach((n, i) => { if (n === 0) emptyIndices.push(i); });
    if (emptyIndices.length === 0) return;
    const randomIdx = emptyIndices[Math.floor(Math.random() * emptyIndices.length)];
    const board = [...this.data.board];
    const errors = [...this.data.errors];
    board[randomIdx] = this._puzzle.solution[randomIdx];
    errors[randomIdx] = false;
    this.setData({ board, errors, selectedIndex: randomIdx });
    wx.showToast({ title: '已帮您填一个', icon: 'none' });
    this._checkComplete();
  },

  // 检查是否全部完成
  _checkComplete() {
    const allCorrect = this.data.board.every((n, i) => n === this._puzzle.solution[i]);
    if (allCorrect) {
      const cur = this.data.currentLevel;
      if (cur < LEVELS.length) {
        this.setData({ isComplete: true, selectedIndex: -1 });
      } else {
        this.setData({ isComplete: true, isAllClear: true, selectedIndex: -1 });
      }
      wx.vibrateShort && wx.vibrateShort({ type: 'medium' });
    }
  },

  // 下一关
  nextLevel() {
    this.startLevel(this.data.currentLevel + 1);
  },

  // 重玩本关
  restart() {
    this.startLevel(this.data.currentLevel);
  },

  // 从头再玩
  restartAll() {
    this.startLevel(1);
  },
});
