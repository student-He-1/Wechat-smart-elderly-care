// index.js
const { NEWS } = require('../../services/news.js');

Page({
  data: {
    dark: false,
    greeting: '您好',
    dateText: '',
    showAiPicker: false,
    ballX: 300,
    ballY: 500,
    news: NEWS.slice(0, 4),
    unread: 0,
    // 天气+农历节气（模拟数据，后续可接真实接口）
    weather: {
      temp: '24°',
      weather: '晴',
      air: '空气优',
      lunar: '八月廿二',
      solarTerm: '白露',
      weekday: '星期三',
      tip: '天气晴朗，适合出门走走'
    },
    // 今日吃药进度
    medicineProgress: {
      taken: 2,
      total: 3,
      percent: 67
    },
    banners: [
      '/assets/images/1-1.jpg',
      '/assets/images/1-2.jpg',
      '/assets/images/1-3.jpg',
      '/assets/images/1-4.jpg',
      '/assets/images/1-5.jpg',
      '/assets/images/1-6.jpg'
    ],
    showSearch: false,
    searchKw: '',
    allSuggests: [
      { name: '医院攻略 / 挂号', url: '/pages/health/hospital/hospital' },
      { name: '吃药提醒', url: '/pages/profile/reminder/reminder' },
      { name: '社区活动', url: '/pages/activity/activity' },
      { name: '健康知识 · 高血压', url: '/pages/knowledge/detail/detail?key=bp' },
      { name: '健康知识 · 失眠', url: '/pages/knowledge/detail/detail?key=sleep' },
      { name: '健康知识 · 糖尿病饮食', url: '/pages/knowledge/detail/detail?key=diet' },
      { name: '在线问诊', url: '/pages/health/consult/consult' }
    ],
    searchSuggests: [],
    // 常用服务：2 列插画卡
    services: [
      {
        img: '/assets/images/sos.jpg',
        title: '一键呼救',
        desc: '紧急呼叫家人',
        url: '/pages/contact/contact'
      },
      {
        img: '/assets/images/medicine.jpg',
        title: '智能用药',
        desc: '定时提醒服药',
        url: '/pages/health/medicine/medicine'
      },
      {
        img: '/assets/images/assistant.jpg',
        title: '健康问答',
        desc: 'AI 解答疑问',
        url: '/pages/health/assistant/assistant'
      },
      {
        img: '/assets/images/record.jpg',
        title: '健康记录',
        desc: '体征随手记',
        url: '/pages/health/record/record'
      }
    ],
    // 今日待办
    reminders: [
      {
        id: 1,
        title: '服用降压药',
        time: '今天 08:00',
        hour: 8,
        minute: 0,
        type: 'medicine',
        status: 'done'
      },
      {
        id: 2,
        title: '喝水提醒',
        time: '今天 10:00',
        hour: 10,
        minute: 0,
        type: 'water',
        status: 'pending'
      },
      {
        id: 3,
        title: '饭后散步 30 分钟',
        time: '今天 16:00',
        hour: 16,
        minute: 0,
        type: 'walk',
        status: 'pending'
      }
    ],
    // 健康知识精选
    knowledge: [
      {
        img: '/assets/images/know-bp.jpg',
        title: '高血压日常护理',
        desc: '低盐饮食 · 定期监测',
        key: 'bp'
      },
      {
        img: '/assets/images/know-sleep.jpg',
        title: '如何改善失眠',
        desc: '规律作息 · 静心助眠',
        key: 'sleep'
      },
      {
        img: '/assets/images/know-diet.jpg',
        title: '糖尿病饮食搭配',
        desc: '少食多餐 · 粗细搭配',
        key: 'diet'
      }
    ]
  },

  onLoad() {
    // 算悬浮球初始位置：右侧、家人横滑行高度
    const win = wx.getWindowInfo ? wx.getWindowInfo() : wx.getSystemInfoSync();
    const ballSize = 38;
    const ballX = win.windowWidth - ballSize - 12;
    const ballY = win.windowHeight - ballSize - 340;
    this.setData({ ballX, ballY });

    // 生成时辰问候语与日期
    const now = new Date();
    const hour = now.getHours();
    let greeting = '您好';
    if (hour >= 5 && hour < 9) greeting = '早上好';
    else if (hour >= 9 && hour < 12) greeting = '上午好';
    else if (hour >= 12 && hour < 14) greeting = '中午好';
    else if (hour >= 14 && hour < 18) greeting = '下午好';
    else if (hour >= 18 && hour < 22) greeting = '晚上好';
    else greeting = '夜深了';

    const week = ['日', '一', '二', '三', '四', '五', '六'];
    const weekday = `星期${week[now.getDay()]}`;
    const dateText = `${now.getMonth() + 1}月${now.getDate()}日 ${weekday}`;

    this.setData({ greeting, dateText, 'weather.weekday': weekday });
    this.loadHealthData();
    this.loadReminders();
  },

  onShow() {
    this.setData({ dark: wx.getStorageSync('dark') });
    this.checkUnread();
    // 同步自定义 TabBar 选中态
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().setData({ selected: 0 });
    }
    // 从后端刷新今日待办（提醒设置页删除/修改后回来同步）
    this.loadReminders();
    this.checkDueReminders();
  },

  // 统计未读消息：子女回复 + 社区通知（分开算）
  checkUnread() {
    const msgs = wx.getStorageSync('messages') || [];
    const lastReadChild = wx.getStorageSync('lastReadChild') || '';
    const lastReadNotice = wx.getStorageSync('lastReadNotice') || '';
    let unreadChild = 0, unreadCommunity = 0;
    for (let i = msgs.length - 1; i >= 0; i--) {
      const m = msgs[i];
      if (m.channel === 'family' && m.id === lastReadChild) break;
      if (m.channel === 'notice' && m.id === lastReadNotice) break;
      if (m.channel === 'family' && m.from === 'daughter') unreadChild++;
      if (m.channel === 'notice') unreadCommunity++;
    }
    this.setData({ unread: unreadChild + unreadCommunity, unreadChild, unreadCommunity });
  },

  goChat() {
    const { unreadChild, unreadCommunity } = this.data;
    // 只有一类未读，直接去
    if (unreadChild > 0 && unreadCommunity === 0) {
      const msgs = (wx.getStorageSync('messages') || []).filter(m => m.channel === 'family');
      if (msgs.length) wx.setStorageSync('lastReadChild', msgs[msgs.length - 1].id);
      this.setData({ unread: 0, unreadChild: 0 });
      wx.navigateTo({ url: '/pages/contact/chat/chat' });
      return;
    }
    if (unreadCommunity > 0 && unreadChild === 0) {
      const msgs = (wx.getStorageSync('messages') || []).filter(m => m.channel === 'notice');
      if (msgs.length) wx.setStorageSync('lastReadNotice', msgs[msgs.length - 1].id);
      this.setData({ unread: 0, unreadCommunity: 0 });
      this.showNotices();
      return;
    }
    // 两类都有，让用户选
    wx.showActionSheet({
      itemList: [`来自子女的回复（${unreadChild}条）`, `来自社区的通知（${unreadCommunity}条）`],
      success: (res) => {
        if (res.tapIndex === 0) {
          const msgs = (wx.getStorageSync('messages') || []).filter(m => m.channel === 'family');
          if (msgs.length) wx.setStorageSync('lastReadChild', msgs[msgs.length - 1].id);
          this.setData({ unread: this.data.unreadCommunity, unreadChild: 0 });
          wx.navigateTo({ url: '/pages/contact/chat/chat' });
        } else {
          const msgs = (wx.getStorageSync('messages') || []).filter(m => m.channel === 'notice');
          if (msgs.length) wx.setStorageSync('lastReadNotice', msgs[msgs.length - 1].id);
          this.setData({ unread: this.data.unreadChild, unreadCommunity: 0 });
          this.showNotices();
        }
      }
    });
  },

  goMedicine() {
    wx.navigateTo({ url: '/pages/health/medicine/medicine' });
  },

  goNearby() {
    wx.navigateTo({ url: '/pages/nearby/nearby' });
  },

  showNotices() {
    const msgs = (wx.getStorageSync('messages') || []).filter(m => m.channel === 'notice');
    if (msgs.length === 0) {
      wx.showToast({ title: '暂无通知', icon: 'none' });
      return;
    }
    const text = msgs.map(m => `[${m.time}]\n${m.text}`).join('\n\n');
    wx.showModal({
      title: '社区通知',
      content: text,
      showCancel: false
    });
  },

  // 检查到点待办：进入前台时弹出提醒（仅小程序在前台时有效）
  checkDueReminders() {
    const now = new Date();
    const cur = now.getHours() * 60 + now.getMinutes();
    const today = `${now.getFullYear()}-${now.getMonth() + 1}-${now.getDate()}`;
    // 今天已弹过的待办 id，避免每次进首页都弹
    let fired = wx.getStorageSync('reminderFired') || {};
    if (fired.date !== today) fired = { date: today, ids: [] };

    const due = this.data.reminders.find(
      r => r.status === 'pending' && r.hour * 60 + r.minute <= cur && !fired.ids.includes(r.id)
    );
    if (!due) return;

    fired.ids.push(due.id);
    wx.setStorageSync('reminderFired', fired);

    const hh = due.hour < 10 ? '0' + due.hour : due.hour;
    const mm = due.minute < 10 ? '0' + due.minute : due.minute;
    // 震动提醒
    wx.vibrateShort({ type: 'heavy' });
    wx.showModal({
      title: '⏰ 到点提醒',
      content: `现在 ${hh}:${mm}，该「${due.title}」了`,
      confirmText: '已完成',
      cancelText: '稍后',
      success: (res) => {
        if (res.confirm) this.completeTodo(due.id);
      }
    });
  },

  // 点击待办行：pending → 弹完成确认；done → 跳提醒设置页
  toggleTodo(e) {
    const item = e.currentTarget.dataset.item;
    if (item.status === 'done') {
      this.goToReminders();
      return;
    }
    wx.showModal({
      title: '完成待办',
      content: `「${item.title}」已完成了吗？`,
      confirmText: '已完成',
      cancelText: '取消',
      success: (res) => {
        if (res.confirm) this.completeTodo(item.id);
      }
    });
  },

  completeTodo(id) {
    const reminders = this.data.reminders.map(r =>
      r.id === id ? { ...r, status: 'done' } : r
    );
    this.setData({ reminders });
    // 完成状态持久化，避免从提醒设置页回来后被重置
    const doneIds = wx.getStorageSync('doneTodoIds') || [];
    if (!doneIds.includes(id)) {
      doneIds.push(id);
      wx.setStorageSync('doneTodoIds', doneIds);
    }
    wx.showToast({ title: '已完成', icon: 'success' });
  },

  // 加载健康数据
  loadHealthData() {
    // 模拟API调用
    setTimeout(() => {
      console.log('健康数据加载完成');
    }, 1000);
  },

  // 从后端加载今日待办（与提醒设置页联动，删除/修改后回首页自动刷新）
  loadReminders() {
    wx.request({
      url: 'http://localhost:8000/api/health/reminder-settings',
      method: 'GET',
      success: (res) => {
        if (res.data.code === 200 && res.data.data && res.data.data.length > 0) {
          const doneIds = wx.getStorageSync('doneTodoIds') || [];
          const reminders = res.data.data
            .filter(s => s.enabled && s.times && s.times.length > 0)
            .map(setting => {
              const t = setting.times[0];
              const parts = t.split(':');
              return {
                id: setting.reminder_type,
                title: setting.reminder_name,
                time: '今天 ' + t,
                hour: parseInt(parts[0], 10),
                minute: parseInt(parts[1], 10),
                type: setting.reminder_type,
                status: doneIds.includes(setting.reminder_type) ? 'done' : 'pending'
              };
            });
          if (reminders.length > 0) {
            this.setData({ reminders });
          }
        }
      },
      fail: () => {
        // 后端不可用时保持 data 里的默认数据
      }
    });
  },

  // 点击待办/铃铛 → 提醒设置页
  goToReminders() {
    wx.navigateTo({
      url: '/pages/profile/reminder/reminder'
    });
  },

  // 点击健康知识 → 进入健康助手
  askKnowledge() {
    wx.navigateTo({
      url: '/pages/health/assistant/assistant'
    });
  },

  // 常联系的人：跳联系人页
  goToContacts() {
    wx.navigateTo({
      url: '/pages/contact/contact'
    });
  },

  // 拨号占位（后续接真实号码）
  callSon() {
    wx.showActionSheet({
      itemList: ['拨打儿子电话', '给儿子留言'],
      success: (res) => {
        if (res.tapIndex === 0) {
          wx.makePhoneCall({ phoneNumber: '13800138000' });
        } else {
          wx.navigateTo({ url: '/pages/contact/chat/chat?name=儿子&target=son&phone=13800138000' });
        }
      }
    });
  },
  callDaughter() {
    wx.showActionSheet({
      itemList: ['拨打女儿电话', '给女儿留言'],
      success: (res) => {
        if (res.tapIndex === 0) {
          wx.makePhoneCall({ phoneNumber: '13900139000' });
        } else {
          wx.navigateTo({ url: '/pages/contact/chat/chat?name=女儿&target=daughter&phone=13900139000' });
        }
      }
    });
  },
  callDoctor() {
    wx.navigateTo({
      url: '/pages/contact/contact'
    });
  },
  callWorker() {
    wx.showActionSheet({
      itemList: ['拨打王师傅电话', '给王师傅留言'],
      success: (res) => {
        if (res.tapIndex === 0) {
          wx.makePhoneCall({ phoneNumber: '13800000000' });
        } else {
          wx.navigateTo({ url: '/pages/contact/worker/worker' });
        }
      }
    });
  },
  call120() {
    wx.showModal({
      title: '紧急呼叫',
      content: '确定要拨打 120 急救电话吗？',
      confirmText: '拨打',
      success: (res) => {
        if (res.confirm) {
          // 写告警到 storage，子女端可见
          const alerts = wx.getStorageSync('alerts') || [];
          alerts.unshift({
            id: Date.now(),
            title: '妈妈按下了紧急求助',
            time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
            level: 'urgent',
            handled: false
          });
          wx.setStorageSync('alerts', alerts);
          wx.makePhoneCall({ phoneNumber: '120' });
        }
      }
    });
  },

  goNewsList() {
    wx.navigateTo({ url: '/pages/news/index' });
  },

  goConsult() {
    wx.navigateTo({ url: '/pages/health/consult/consult' });
  },

  openDoctor(e) {
    const { name, avatar } = e.currentTarget.dataset;
    wx.navigateTo({ url: '/pages/health/consult/doctor/doctor?name=' + name + '&avatar=' + (avatar || '') });
  },

  goActivity() {
    wx.navigateTo({ url: '/pages/activity/activity' });
  },

  openKnowledge(e) {
    wx.navigateTo({ url: '/pages/knowledge/detail/detail?key=' + e.currentTarget.dataset.key });
  },

  openSearch() {
    this.setData({ showSearch: true, searchSuggests: this.data.allSuggests, searchKw: '' });
  },
  closeSearch() {
    this.setData({ showSearch: false });
  },
  onSearchInput(e) {
    const kw = e.detail.value.trim();
    if (!kw) {
      this.setData({ searchKw: kw, searchSuggests: this.data.allSuggests });
      return;
    }
    const list = this.data.allSuggests.filter(s => s.name.includes(kw));
    this.setData({ searchKw: kw, searchSuggests: list });
  },
  goSuggest(e) {
    const url = e.currentTarget.dataset.url;
    this.setData({ showSearch: false });
    wx.navigateTo({ url });
  },
  doSearch() {
    const kw = this.data.searchKw.trim();
    if (!kw) return;
    if (kw.includes('医院') || kw.includes('挂号') || kw.includes('就医')) {
      this.goSuggest({ currentTarget: { dataset: { url: '/pages/health/hospital/hospital' } } });
    } else if (kw.includes('药') || kw.includes('提醒')) {
      this.goSuggest({ currentTarget: { dataset: { url: '/pages/profile/reminder/reminder' } } });
    } else if (kw.includes('活动')) {
      this.goSuggest({ currentTarget: { dataset: { url: '/pages/activity/activity' } } });
    } else {
      this.goSuggest({ currentTarget: { dataset: { url: '/pages/health/consult/consult' } } });
    }
  },

  openNews(e) {
    wx.navigateTo({ url: '/pages/news/detail/detail?id=' + e.currentTarget.dataset.id });
  },

  // 悬浮球拖动：记录当前位置
  onBallMove(e) {
    this._ballX = e.detail.x;
    this._ballY = e.detail.y;
  },

  // 松手：吸附到最近左/右边缘，上下位置限制在安全区
  onBallEnd() {
    const win = wx.getWindowInfo ? wx.getWindowInfo() : wx.getSystemInfoSync();
    const ballSize = 38;
    const safeTop = 120; // 避开顶栏
    const safeBottom = win.windowHeight - 180; // 避开底部 tabbar
    const curX = this._ballX !== undefined ? this._ballX : (win.windowWidth - ballSize - 12);
    let curY = this._ballY !== undefined ? this._ballY : (win.windowHeight - ballSize - 340);
    if (curY < safeTop) curY = safeTop;
    if (curY > safeBottom) curY = safeBottom;
    const snapX = curX < win.windowWidth / 2 ? 12 : win.windowWidth - ballSize - 12;
    this.setData({ ballX: snapX, ballY: curY });
  },

  // 悬浮球：打开居中选择弹窗
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
