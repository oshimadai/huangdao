// 极简测试页面
Page({
  onLoad: function () {
    console.log('Page Load!!!')
  },
  tap: function () {
    console.log('Tap!!!')
    wx.showToast({ title: '成功', icon: 'success' })
  }
})
