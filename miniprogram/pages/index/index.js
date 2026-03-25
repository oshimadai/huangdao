// 荒岛生存小程序 - 首页
const app = getApp()

Page({
  data: {
    testName: '荒岛测试',
    loaded: false
  },

  onLoad: function () {
    console.log('===== 页面 onLoad =====')
    console.log('app.globalData:', app.globalData)
    this.setData({ loaded: true })
    
    // 测试提示
    wx.showToast({
      title: '页面加载成功',
      icon: 'success',
      duration: 2000
    })
  },

  onReady: function () {
    console.log('===== 页面 onReady =====')
  },

  onShow: function () {
    console.log('===== 页面 onShow =====')
  },

  testTap: function () {
    console.log('按钮被点击了！')
    wx.showToast({
      title: '点击成功！🎉',
      icon: 'success',
      duration: 1500
    })
  }
})
