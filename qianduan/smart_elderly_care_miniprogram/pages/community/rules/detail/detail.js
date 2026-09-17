// community/rules/detail.js
const { RULES } = require('../../../../services/community.js');
Page({
  data: { item: {} },
  onLoad(opt) {
    const item = RULES.find(r => r.id === parseInt(opt.id)) || RULES[0];
    this.setData({ item });
  }
});
