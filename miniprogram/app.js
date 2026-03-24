App({
  onLaunch: function () {
    console.log('荒岛生存小程序启动')
    this.initGameData()
  },
  globalData: {
    player: null
  },
  initGameData: function() {
    const playerData = wx.getStorageSync('player')
    if (playerData) {
      this.globalData.player = playerData
    } else {
      this.globalData.player = {
        name: '呆汪',
        stage: 2,
        hp: 100,
        maxHp: 100,
        gold: 500,
        materials: {},
        fightStyle: 'sustain'
      }
    }
  }
})
