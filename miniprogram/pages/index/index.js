const app = getApp()
Page({
  data: {
    playerName: '呆汪',
    playerStage: 2,
    playerHp: 100,
    playerMaxHp: 100,
    playerGold: 500,
    inventoryCount: 15,
    inventoryMax: 50
  },
  onLoad: function () {
    this.loadPlayerData()
  },
  loadPlayerData: function () {
    const player = app.globalData.player
    if (player) {
      this.setData({
        playerName: player.name,
        playerStage: player.stage,
        playerHp: player.hp,
        playerMaxHp: player.maxHp,
        playerGold: player.gold,
        inventoryCount: Object.keys(player.materials || {}).length
      })
    }
  },
  goToDrift: function () {
    wx.showToast({ title: '漂流功能开发中', icon: 'none' })
  },
  goToBattle: function () {
    wx.showToast({ title: '战斗功能开发中', icon: 'none' })
  },
  goToVoyage: function () {
    wx.showToast({ title: '远航功能开发中', icon: 'none' })
  }
})
