# -*- coding: utf-8 -*-
"""
荒岛生存 - 核心循环 Demo
漂流箱供给 → 加工/制作 → 战斗消耗 → 修复 → 交易 → 更高风险区域
"""

import random
import sys
import os
from typing import List, Dict

# 添加 src 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from materials import MaterialTier, MATERIALS, get_material
from driftbox import DriftBoxSystem, DriftBoxTier, print_open_result
from combat import (
    Fighter, Weapon, create_weapon, FightStyle, 
    simulate_combat, CombatResult
)
from economy import EconomySystem


class GameDemo:
    """游戏核心循环 Demo"""
    
    def __init__(self):
        self.driftbox_system = DriftBoxSystem()
        self.economy = EconomySystem()
        self.players: Dict[str, PlayerData] = {}
    
    def create_player(self, player_id: str, stage: int = 1):
        """创建玩家"""
        self.players[player_id] = PlayerData(player_id, stage)
        self.economy.register_player(player_id, stage)
        print(f"\n✓ 玩家 {player_id} 创建成功（阶段{stage}）")
    
    def run_drift_phase(self, player_id: str, box_tier: DriftBoxTier):
        """漂流箱阶段"""
        if player_id not in self.players:
            print(f"✗ 玩家 {player_id} 不存在")
            return
        
        player = self.players[player_id]
        print(f"\n{'='*60}")
        print(f"【漂流阶段】{player_id} 开启 {box_tier.value}漂流箱")
        print(f"{'='*60}")
        
        result = self.driftbox_system.open_box(box_tier)
        print_open_result(result)
        
        # 添加到玩家库存和经济系统
        for mat_id, count in result.items:
            player.add_material(mat_id, count)
            self.economy.produce_material(player_id, mat_id, count)
        
        print(f"\n📦 {player_id} 当前库存价值：{player.get_total_value():,}")
    
    def run_combat_phase(self, player1_id: str, player2_id: str):
        """战斗阶段"""
        if player1_id not in self.players or player2_id not in self.players:
            print("✗ 玩家不存在")
            return
        
        p1 = self.players[player1_id]
        p2 = self.players[player2_id]
        
        print(f"\n{'='*60}")
        print(f"【战斗阶段】{player1_id} vs {player2_id}")
        print(f"{'='*60}")
        
        # 创建战士（根据玩家流派偏好）
        fighter1 = Fighter(player1_id, p1.get_weapon(), hp=100)
        fighter2 = Fighter(player2_id, p2.get_weapon(), hp=100)
        
        # 模拟战斗
        result = simulate_combat(fighter1, fighter2)
        result.print_report()
        
        # 记录耐久消耗（简化：假设消耗了修复材料）
        for fighter in [fighter1, fighter2]:
            durability_lost = fighter.weapon.max_durability - fighter.weapon.current_durability
            if durability_lost > 0:
                print(f"\n⚔️ {fighter.name} 武器耐久损耗：{durability_lost:.0f}")
    
    def run_repair_phase(self, player_id: str):
        """修复阶段"""
        if player_id not in self.players:
            return
        
        player = self.players[player_id]
        print(f"\n{'='*60}")
        print(f"【修复阶段】{player_id}")
        print(f"{'='*60}")
        
        # 检查是否有修复材料
        repair_mats = ["repair_basic", "repair_advanced", "repair_premium"]
        available = [(mat_id, player.materials.get(mat_id, 0)) for mat_id in repair_mats if player.materials.get(mat_id, 0) > 0]
        
        if not available:
            print("⚠️ 没有修复材料，需要制作或购买")
            return
        
        print(f"可用修复材料：{available}")
        
        # 修复武器
        for mat_id, count in available:
            if player.weapon_durability < player.weapon_max_durability:
                repair_amount = min(count * 20, player.weapon_max_durability - player.weapon_durability)
                player.repair_weapon(repair_amount)
                self.economy.consume_material(player_id, mat_id, count)
                print(f"✓ 使用 {get_material(mat_id).name} ×{count}，修复耐久 {repair_amount}")
        
        print(f"当前武器耐久：{player.weapon_durability}/{player.weapon_max_durability}")
    
    def run_trade_phase(self, seller_id: str, buyer_id: str, material_id: str, count: int):
        """交易阶段"""
        print(f"\n{'='*60}")
        print(f"【交易阶段】{seller_id} → {buyer_id}")
        print(f"{'='*60}")
        
        mat = get_material(material_id)
        base_price = mat.base_value
        actual_price = int(base_price * random.uniform(0.9, 1.3))  # 价格波动
        
        print(f"物品：{mat.name} ×{count}")
        print(f"单价：{actual_price}（基准：{base_price}）")
        print(f"总价：{actual_price * count:,}")
        
        success = self.economy.trade(seller_id, buyer_id, material_id, count, actual_price)
        
        if success:
            print("✓ 交易成功")
            # 更新玩家库存
            self.players[seller_id].remove_material(material_id, count)
            self.players[buyer_id].add_material(material_id, count)
        else:
            print("✗ 交易失败（库存不足）")
    
    def print_economy_report(self):
        """打印经济报告"""
        report = self.economy.generate_report()
        self.economy.print_report(report)
    
    def print_all_players(self):
        """打印所有玩家状态"""
        print(f"\n{'='*60}")
        print("【玩家状态】")
        print(f"{'='*60}")
        
        for player_id, player in self.players.items():
            print(f"\n{player_id} (阶段{player.stage}):")
            print(f"  流派：{player.fight_style.value}")
            print(f"  武器耐久：{player.weapon_durability:.0f}/{player.weapon_max_durability}")
            print(f"  库存价值：{player.get_total_value():,}")
            print(f"  主要材料：{dict(list(player.materials.items())[:5])}")


class PlayerData:
    """玩家数据"""
    
    def __init__(self, player_id: str, stage: int = 1):
        self.player_id = player_id
        self.stage = stage
        self.fight_style = random.choice(list(FightStyle))
        self.materials: Dict[str, int] = {}
        
        # 武器数据
        weapon = create_weapon(self.fight_style)
        self.weapon_max_durability = weapon.max_durability
        self.weapon_durability = weapon.max_durability
    
    def get_weapon(self) -> Weapon:
        """获取武器对象"""
        return create_weapon(self.fight_style)
    
    def add_material(self, material_id: str, count: int):
        """添加材料"""
        if material_id not in self.materials:
            self.materials[material_id] = 0
        self.materials[material_id] += count
    
    def remove_material(self, material_id: str, count: int) -> bool:
        """移除材料"""
        if material_id not in self.materials or self.materials[material_id] < count:
            return False
        self.materials[material_id] -= count
        return True
    
    def repair_weapon(self, amount: int):
        """修复武器"""
        self.weapon_durability = min(self.weapon_max_durability, self.weapon_durability + amount)
    
    def get_total_value(self) -> int:
        """计算库存总价值"""
        return sum(
            get_material(mat_id).base_value * count
            for mat_id, count in self.materials.items()
        )


def run_demo():
    """运行完整 Demo"""
    print("\n" + "="*60)
    print("🏝️  荒岛生存 - 核心循环 Demo")
    print("="*60)
    
    game = GameDemo()
    
    # 创建玩家
    print("\n【阶段 1: 创建玩家】")
    game.create_player("呆汪", stage=2)
    game.create_player("玩家 B", stage=1)
    game.create_player("玩家 C", stage=3)
    
    # 漂流箱阶段
    print("\n\n【阶段 2: 漂流箱产出】")
    game.run_drift_phase("呆汪", DriftBoxTier.RARE)
    game.run_drift_phase("玩家 B", DriftBoxTier.COMMON)
    game.run_drift_phase("玩家 C", DriftBoxTier.EPIC)
    
    # 战斗阶段
    print("\n\n【阶段 3: 战斗消耗】")
    game.run_combat_phase("呆汪", "玩家 B")
    
    # 修复阶段
    print("\n\n【阶段 4: 修复】")
    game.run_repair_phase("呆汪")
    
    # 交易阶段
    print("\n\n【阶段 5: 玩家交易】")
    game.run_trade_phase("玩家 B", "呆汪", "wood_basic", 20)
    game.run_trade_phase("呆汪", "玩家 C", "metal_iron", 5)
    
    # 最终状态
    print("\n\n【最终状态】")
    game.print_all_players()
    
    # 经济报告
    print("\n\n")
    game.print_economy_report()
    
    print("\n" + "="*60)
    print("✅ Demo 完成")
    print("="*60 + "\n")


if __name__ == "__main__":
    run_demo()
