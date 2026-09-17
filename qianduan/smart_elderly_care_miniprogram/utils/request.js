// request.js —— 统一网络请求封装（所有后端接口都在 FastAPI 8000）
const { BASE_URL } = require('./config');

/**
 * 通用请求
 * @param {string} url  以 / 开头的接口路径，如 /health-agent/chat
 * @param {object} options { method, data, loading(是否显示全局加载), hideError }
 * @returns {Promise<object>} 后端统一返回体 { message, data }
 */
function request(url, options = {}) {
  const {
    method = 'GET',
    data = {},
    loading = false,
    hideError = false,
    header = {}
  } = options;

  if (loading) {
    wx.showLoading({ title: '加载中...', mask: true });
  }

  return new Promise((resolve, reject) => {
    wx.request({
      url: BASE_URL + url,
      method,
      data,
      timeout: 40000,
      header: { 'Content-Type': 'application/json', ...header },
      success: (res) => {
        if (loading) wx.hideLoading();
        if (res.statusCode === 200) {
          resolve(res.data);
        } else {
          if (!hideError) {
            const detail = (res.data && res.data.detail) || `请求失败(${res.statusCode})`;
            wx.showToast({ title: String(detail).slice(0, 20), icon: 'none' });
          }
          reject(new Error(`请求失败: ${res.statusCode}`));
        }
      },
      fail: (err) => {
        if (loading) wx.hideLoading();
        if (!hideError) {
          wx.showToast({ title: '网络异常，请确认后端已启动', icon: 'none' });
        }
        reject(err);
      }
    });
  });
}

/**
 * 上传文件（语音识别用）
 * @param {string} url 接口路径
 * @param {string} filePath 本地临时文件路径
 * @param {string} name 文件字段名
 * @param {object} formData 额外表单字段
 */
function upload(url, filePath, name = 'audio', formData = {}) {
  return new Promise((resolve, reject) => {
    wx.uploadFile({
      url: BASE_URL + url,
      filePath,
      name,
      formData,
      timeout: 40000,
      success: (res) => {
        if (res.statusCode === 200) {
          // uploadFile 返回的是字符串，需要解析
          try {
            resolve(JSON.parse(res.data));
          } catch (e) {
            reject(new Error('返回数据解析失败'));
          }
        } else {
          wx.showToast({ title: `上传失败(${res.statusCode})`, icon: 'none' });
          reject(new Error(`上传失败: ${res.statusCode}`));
        }
      },
      fail: (err) => {
        wx.showToast({ title: '网络异常，请确认后端已启动', icon: 'none' });
        reject(err);
      }
    });
  });
}

module.exports = {
  request,
  upload,
  get: (url, options) => request(url, { ...options, method: 'GET' }),
  post: (url, data, options) => request(url, { ...options, method: 'POST', data })
};
