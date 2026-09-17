// pages/nearby/nearby.js —— 附近便民
const CATEGORIES = [
  { key: 'store', name: '便利店', icon: '🏪' },
  { key: 'pharmacy', name: '药店', icon: '💊' },
  { key: 'market', name: '菜市场', icon: '🥬' },
  { key: 'community', name: '社区服务', icon: '🏛️' },
];

const SHOPS = {
  store: [
    { name: '美宜佳(阳光小区店)', address: '阳光路88号', distance: '350米', phone: '400-xxx-xxxx', hours: '06:00-24:00', img: '/assets/images/8-5.png' },
    { name: '全家便利店(幸福路店)', address: '幸福路12号', distance: '200米', phone: '400-xxx-xxxx', hours: '24小时营业', img: '/assets/images/8-6.png' },
    { name: '7-Eleven(人民路店)', address: '人民路156号', distance: '500米', phone: '400-xxx-xxxx', hours: '24小时营业', img: '/assets/images/8-7.png' },
  ],
  pharmacy: [
    { name: '老百姓大药房(幸福路店)', address: '幸福路45号', distance: '150米', phone: '022-xxxx-xxxx', hours: '08:00-22:00', img: '' },
    { name: '益丰大药房(阳光路店)', address: '阳光路66号', distance: '400米', phone: '022-xxxx-xxxx', hours: '08:30-21:30', img: '' },
    { name: '国大药房(社区店)', address: '社区服务中心1楼', distance: '600米', phone: '022-xxxx-xxxx', hours: '09:00-20:00', img: '' },
  ],
  market: [
    { name: '幸福路菜市场', address: '幸福路78号', distance: '300米', phone: '022-xxxx-xxxx', hours: '06:00-19:00', img: '' },
    { name: '阳光生鲜超市', address: '阳光路100号', distance: '450米', phone: '022-xxxx-xxxx', hours: '07:00-21:00', img: '' },
    { name: '便民早市(人民广场)', address: '人民路人民广场', distance: '800米', phone: '022-xxxx-xxxx', hours: '05:30-10:00', img: '' },
  ],
  community: [
    { name: '幸福社区服务中心', address: '幸福路1号', distance: '100米', phone: '022-xxxx-xxxx', hours: '09:00-17:00', img: '' },
    { name: '阳光社区卫生服务站', address: '阳光路20号', distance: '250米', phone: '022-xxxx-xxxx', hours: '08:00-17:00', img: '' },
    { name: '街道养老服务中心', address: '人民路88号', distance: '550米', phone: '022-xxxx-xxxx', hours: '09:00-17:30', img: '' },
  ],
};

Page({
  data: {
    categories: CATEGORIES,
    activeKey: 'store',
    shops: SHOPS.store,
  },

  switchCategory(e) {
    const key = e.currentTarget.dataset.key;
    this.setData({
      activeKey: key,
      shops: SHOPS[key] || [],
    });
  },

  callShop(e) {
    const phone = e.currentTarget.dataset.phone;
    if (!phone || phone.includes('x')) {
      wx.showToast({ title: '电话号码待补充', icon: 'none' });
      return;
    }
    wx.makePhoneCall({ phoneNumber: phone });
  },
});
