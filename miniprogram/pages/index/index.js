const app = getApp()
Page({
  data: {
    testName: '荒岛小程序'
  },
  onLoad: function () {
    console.log('页面加载成功')
  },
  testTap: function () {
    wx.showToast({
      title: '点击成功！',
      icon: 'success'
    })
  }
})
