// pages/companion/game/math/math.js —— 算术小能手（100以内加减法，三关难度，选择题）

const LEVELS = [
  { level: 1, name: '第一关·入门', max: 20 },
  { level: 2, name: '第二关·进阶', max: 50 },
  { level: 3, name: '第三关·挑战', max: 100 },
];

const TOTAL_QUESTIONS = 10;

function randInt(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

// 生成一道题
function genQuestion(max) {
  const isAdd = Math.random() > 0.5;
  let a, b, answer, text;
  if (isAdd) {
    a = randInt(1, max - 1);
    b = randInt(1, max - a);
    answer = a + b;
    text = `${a} + ${b} = ?`;
  } else {
    a = randInt(2, max);
    b = randInt(1, a);
    answer = a - b;
    text = `${a} - ${b} = ?`;
  }
  // 生成4个选项（1正确+3干扰）
  const options = new Set([answer]);
  const offsets = [1, -1, 2, -2, 3, -3];
  for (const off of offsets) {
    if (options.size >= 4) break;
    const v = answer + off;
    if (v >= 0 && v <= max + 5) options.add(v);
  }
  while (options.size < 4) {
    options.add(randInt(0, max + 5));
  }
  const optionArr = [...options].sort(() => Math.random() - 0.5);
  return { text, answer, options: optionArr };
}

Page({
  data: {
    questions: [],
    currentIndex: 0,
    score: 0,
    selectedIndex: -1,
    isAnswered: false,
    isFinished: false,
    currentQuestion: null,
    levelName: '',
    currentLevel: 1,
  },

  onLoad() {
    this.startLevel(1);
  },

  startLevel(level) {
    const cfg = LEVELS[level - 1];
    const questions = [];
    for (let i = 0; i < TOTAL_QUESTIONS; i++) {
      questions.push(genQuestion(cfg.max));
    }
    this.setData({
      questions,
      currentIndex: 0,
      score: 0,
      selectedIndex: -1,
      isAnswered: false,
      isFinished: false,
      currentQuestion: questions[0],
      levelName: cfg.name,
      currentLevel: level,
    });
  },

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
