Page({
  onLoad: function() {
    console.log('Page Load OK!')
  },
  onShow: function() {
    console.log('Page Show OK!')
  },
  onTap: function() {
    console.log('Button Tap OK!')
    wx.showToast({
      title: '点击成功',
      icon: 'success'
    })
  }
})
