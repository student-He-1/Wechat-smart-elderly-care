// pages/companion/game/idiom/idiom.js —— 成语接龙（选择题形式，适老化）

// 题库：current是当前成语，answer是正确接龙（以上一个尾字同音开头）
// 每轮随机选10题
const QUESTION_BANK = [
  { current: '一心一意', answer: '意气风发', options: ['守株待兔', '意气风发', '画蛇添足', '亡羊补牢'] },
  { current: '意气风发', answer: '发扬光大', options: ['发扬光大', '掩耳盗铃', '刻舟求剑', '井底之蛙'] },
  { current: '发扬光大', answer: '大材小用', options: ['对牛弹琴', '大材小用', '叶公好龙', '愚公移山'] },
  { current: '大材小用', answer: '用兵如神', options: ['精卫填海', '夸父追日', '用兵如神', '八仙过海'] },
  { current: '用兵如神', answer: '神清气爽', options: ['神清气爽', '女娲补天', '后羿射日', '嫦娥奔月'] },
  { current: '神清气爽', answer: '爽然若失', options: ['爽然若失', '画蛇添足', '守株待兔', '亡羊补牢'] },
  { current: '爽然若失', answer: '失而复得', options: ['掩耳盗铃', '失而复得', '刻舟求剑', '井底之蛙'] },
  { current: '失而复得', answer: '得心应手', options: ['对牛弹琴', '叶公好龙', '得心应手', '愚公移山'] },
  { current: '得心应手', answer: '手到擒来', options: ['精卫填海', '手到擒来', '夸父追日', '八仙过海'] },
  { current: '手到擒来', answer: '来日方长', options: ['女娲补天', '后羿射日', '嫦娥奔月', '来日方长'] },
  { current: '来日方长', answer: '长驱直入', options: ['长驱直入', '画蛇添足', '守株待兔', '亡羊补牢'] },
  { current: '长驱直入', answer: '入木三分', options: ['掩耳盗铃', '刻舟求剑', '入木三分', '井底之蛙'] },
  { current: '入木三分', answer: '分秒必争', options: ['对牛弹琴', '分秒必争', '叶公好龙', '愚公移山'] },
  { current: '分秒必争', answer: '争先恐后', options: ['精卫填海', '夸父追日', '八仙过海', '争先恐后'] },
  { current: '争先恐后', answer: '后来居上', options: ['后来居上', '女娲补天', '后羿射日', '嫦娥奔月'] },
];

const TOTAL_QUESTIONS = 10; // 每轮题数

Page({
  data: {
    questions: [],
    currentIndex: 0,
    score: 0,
    selectedIndex: -1,
    isAnswered: false,
    isFinished: false,
    currentQuestion: null,
  },

  onLoad() {
    this.startGame();
  },

  // 开始游戏（随机选题）
  startGame() {
    const shuffled = [...QUESTION_BANK].sort(() => Math.random() - 0.5);
    const questions = shuffled.slice(0, TOTAL_QUESTIONS);
    this.setData({
      questions,
      currentIndex: 0,
      score: 0,
      selectedIndex: -1,
      isAnswered: false,
      isFinished: false,
      currentQuestion: questions[0],
    });
  },

  // 选择答案
  selectOption(e) {
    if (this.data.isAnswered) return;
    const idx = e.currentTarget.dataset.index;
    const q = this.data.currentQuestion;
    const isCorrect = q.options[idx] === q.answer;
    this.setData({
      selectedIndex: idx,
      isAnswered: true,
      score: isCorrect ? this.data.score + 1 : this.data.score,
    });
    if (isCorrect) {
      wx.vibrateShort && wx.vibrateShort({ type: 'light' });
    }
  },

  // 下一题
  nextQuestion() {
    const next = this.data.currentIndex + 1;
    if (next >= this.data.questions.length) {
      this.setData({ isFinished: true });
      return;
    }
    this.setData({
      currentIndex: next,
      currentQuestion: this.data.questions[next],
      selectedIndex: -1,
      isAnswered: false,
    });
  },

  // 再玩一轮
  restart() {
    this.startGame();
  },
});
