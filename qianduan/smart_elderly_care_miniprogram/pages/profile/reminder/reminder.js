// pages/profile/reminder/reminder.js
Page({
  data: {
    // 提醒设置
    reminders: [
      {
        id: 'water',
        name: '喝水提醒',
        enabled: true,
        times: ['09:00', '11:30', '14:00', '16:30']
      },
      {
        id: 'activity',
        name: '活动提醒',
        enabled: true,
        times: ['10:00', '15:00']
      },
      {
        id: 'ventilation',
        name: '通风提醒',
        enabled: true,
        times: ['08:00', '12:00', '18:00']
      },
      {
        id: 'light',
        name: '夜间开灯提醒',
        enabled: true,
        times: ['19:00']
      },
      {
        id: 'medicine',
        name: '吃药提醒',
        enabled: true,
        times: ['08:00', '12:00', '18:00']
      },
      {
        id: 'sitting',
        name: '久坐提醒',
        enabled: true,
        times: ['09:30', '11:00', '14:30', '16:00']
      }
    ],
    // 新时间输入
    newTime: '',
    // 新提醒项目名称
    newReminderName: '',
    // 当前编辑的提醒ID
    currentReminderId: ''
  },

  onLoad() {
    console.log('提醒设置页面加载');
    this.loadReminderSettings();
  },

  // 从后端加载提醒设置
  loadReminderSettings() {
    wx.request({
      url: 'http://localhost:8000/api/health/reminder-settings',
      method: 'GET',
      success: (res) => {
        console.log('获取提醒设置成功:', res.data);
        if (res.data.code === 200 && res.data.data && res.data.data.length > 0) {
          // 将后端返回的设置转换为前端格式
          const reminders = res.data.data.map(setting => ({
            id: setting.reminder_type,
            name: setting.reminder_name,
            enabled: setting.enabled,
            times: setting.times
          }));
          this.setData({ reminders });
        }
      },
      fail: (err) => {
        console.error('获取提醒设置失败:', err);
        // 加载失败时使用默认设置
      }
    });
  },

  // 切换提醒开关
  toggleReminder(e) {
    const { id, enabled } = e.currentTarget.dataset;
    const reminders = this.data.reminders.map(reminder => {
      if (reminder.id === id) {
        return { ...reminder, enabled: !enabled };
      }
      return reminder;
    });
    this.setData({ reminders });
    
    wx.showToast({
      title: !enabled ? '已开启提醒' : '已关闭提醒',
      icon: 'success'
    });
  },

  // 添加提醒时间
  addTime(e) {
    const { id } = e.currentTarget.dataset;
    this.setData({ 
      currentReminderId: id,
      newTime: ''
    });
    
    wx.showModal({
      title: '添加提醒时间',
      content: '请输入提醒时间（格式：HH:MM）',
      inputPlaceholder: '例如：08:30',
      success: (res) => {
        if (res.confirm) {
          const newTime = res.content;
          if (this.validateTime(newTime)) {
            const reminders = this.data.reminders.map(reminder => {
              if (reminder.id === id) {
                // 检查时间是否已存在
                if (!reminder.times.includes(newTime)) {
                  return { ...reminder, times: [...reminder.times, newTime].sort() };
                }
              }
              return reminder;
            });
            this.setData({ reminders });
            wx.showToast({ title: '添加成功', icon: 'success' });
          } else {
            wx.showToast({ title: '时间格式错误', icon: 'none' });
          }
        }
      }
    });
  },

  // 删除提醒时间
  deleteTime(e) {
    const { id, time } = e.currentTarget.dataset;
    const reminders = this.data.reminders.map(reminder => {
      if (reminder.id === id) {
        return { ...reminder, times: reminder.times.filter(t => t !== time) };
      }
      return reminder;
    });
    this.setData({ reminders });
    wx.showToast({ title: '删除成功', icon: 'success' });
  },

  // 添加新提醒项目
  addReminder() {
    wx.showModal({
      title: '添加提醒项目',
      content: '请输入提醒项目名称',
      inputPlaceholder: '例如：吃药提醒',
      success: (res) => {
        if (res.confirm) {
          const newName = res.content.trim();
          if (newName) {
            // 生成唯一ID
            const newId = 'reminder_' + Date.now();
            const newReminder = {
              id: newId,
              name: newName,
              enabled: true,
              times: []
            };
            
            const reminders = [...this.data.reminders, newReminder];
            this.setData({ reminders });
            wx.showToast({ title: '添加成功', icon: 'success' });
          } else {
            wx.showToast({ title: '名称不能为空', icon: 'none' });
          }
        }
      }
    });
  },

  // 删除提醒项目
  deleteReminder(e) {
    const { id } = e.currentTarget.dataset;
    wx.showModal({
      title: '删除提醒项目',
      content: '确定要删除这个提醒项目吗？',
      success: (res) => {
        if (res.confirm) {
          const reminders = this.data.reminders.filter(reminder => reminder.id !== id);
          this.setData({ reminders });
          wx.showToast({ title: '删除成功', icon: 'success' });
        }
      }
    });
  },

  // 验证时间格式
  validateTime(time) {
    const regex = /^([01]?[0-9]|2[0-3]):[0-5][0-9]$/;
    return regex.test(time);
  },

  // 保存设置
  saveSettings() {
    // 转换为后端需要的格式
    const reminders = this.data.reminders.map(reminder => ({
      reminder_type: reminder.id,
      reminder_name: reminder.name,
      enabled: reminder.enabled,
      times: reminder.times
    }));
    
    wx.request({
      url: 'http://localhost:8000/api/health/reminder-settings',
      method: 'POST',
      data: { reminders },
      success: (res) => {
        console.log('保存提醒设置成功:', res.data);
        wx.showToast({ title: '设置已保存', icon: 'success' });
      },
      fail: (err) => {
        console.error('保存提醒设置失败:', err);
        wx.showToast({ title: '保存失败，请重试', icon: 'none' });
      }
    });
  }
});