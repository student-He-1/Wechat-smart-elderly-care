// pages/companion/game/index/index.js —— 健脑游戏选择页
Page({
  data: {
    games: [
      {
        id: 'memory',
        icon: '🃏',
        title: '翻牌记忆',
        desc: '配对消除 · 三关难度 · 锻炼记忆力',
        color: 'green',
        url: '/pages/companion/game/memory/memory',
      },
      {
        id: 'sudoku',
        icon: '🔢',
        title: '趣味数独',
        desc: '4×4 简化版 · 三关难度 · 锻炼逻辑思维',
        color: 'blue',
        url: '/pages/companion/game/sudoku/sudoku',
      },
      {
        id: 'idiom',
        icon: '📖',
        title: '成语接龙',
        desc: '选择题形式 · 10题一轮 · 积累成语',
        color: 'purple',
        url: '/pages/companion/game/idiom/idiom',
      },
      {
        id: 'match',
        icon: '🎯',
        title: '对对消',
        desc: '点相同图案消除 · 三关难度 · 锻炼观察力',
        color: 'orange',
        url: '/pages/companion/game/match/match',
      },
      {
        id: 'math',
        icon: '🔢',
        title: '算术小能手',
        desc: '100以内加减法 · 三关难度 · 锻炼计算',
        color: 'cyan',
        url: '/pages/companion/game/math/math',
      },
    ],
  },

  goGame(e) {
    const url = e.currentTarget.dataset.url;
    wx.navigateTo({ url });
  },
});
