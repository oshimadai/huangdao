# -*- coding: utf-8 -*-
"""
远航系统 - 深渊沉船争夺战 (Deep Sea Contention)

核心机制:
- 镜像驻守：玩家作为 Boss 驻守沉船
- 维保过载：驻守时间越长，战前修复成本非线性上升
- 产出与耐久挂钩：耐久% → 产出速率%
- 战地背包：手动装填维修耗材，耗尽则强制结束
"""

import random
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum

from materials import Material, MaterialTier, MaterialType, MATERIALS, get_material


class ShipwreckTier(Enum):
    """沉船等级"""
    T1 = "T1 沉船"  # 新手区
    T2 = "T2 沉船"  # 竞争区
    T3 = "T3 沉船"  # 深渊区


@dataclass
class ShipwreckConfig:
    """沉船配置"""
    tier: ShipwreckTier
    base_output_value: int  # 基础产出价值/小时
    guard_slots: int  # 护卫位数量（固定 2）
    min_repair_cost_multiplier: float  # 最小维修倍率
    max_repair_cost_multiplier: float  # 最大维修倍率（维保过载上限）
    decay_rate: float  # 成本衰减率（指数曲线）


# 沉船配置表
SHIPWRECK_CONFIGS = {
    ShipwreckTier.T1: ShipwreckConfig(
        tier=ShipwreckTier.T1,
        base_output_value=100,
        guard_slots=2,
        min_repair_cost_multiplier=1.0,
        max_repair_cost_multiplier=3.0,
        decay_rate=0.1,
    ),
    ShipwreckTier.T2: ShipwreckConfig(
        tier=ShipwreckTier.T2,
        base_output_value=300,
        guard_slots=2,
        min_repair_cost_multiplier=1.0,
        max_repair_cost_multiplier=5.0,
        decay_rate=0.08,
    ),
    ShipwreckTier.T3: ShipwreckConfig(
        tier=ShipwreckTier.T3,
        base_output_value=1000,
        guard_slots=2,
        min_repair_cost_multiplier=1.0,
        max_repair_cost_multiplier=10.0,  # T3 维保过载最严重
        decay_rate=0.05,
    ),
}


@dataclass
class MirrorGuard:
    """镜像护卫"""
    player_id: str
    role: str  # "boss" / "guard"
    weapon_durability: int
    weapon_max_durability: int
    armor_durability: int
    armor_max_durability: int
    fight_style: str  # "burst" / "sustain" / "defense"
    
    def get_durability_ratio(self) -> float:
        """获取平均耐久百分比"""
        weapon_ratio = self.weapon_durability / self.weapon_max_durability if self.weapon_max_durability > 0 else 0
        armor_ratio = self.armor_durability / self.armor_max_durability if self.armor_max_durability > 0 else 0
        return (weapon_ratio + armor_ratio) / 2


@dataclass
class SupplyPack:
    """战地背包（维修耗材包）"""
    materials: Dict[str, int]  # material_id -> count
    
    def has_materials(self, required: Dict[str, int]) -> bool:
        """检查是否有足够材料"""
        for mat_id, count in required.items():
            if self.materials.get(mat_id, 0) < count:
                return False
        return True
    
    def consume(self, required: Dict[str, int]) -> bool:
        """消耗材料"""
        if not self.has_materials(required):
            return False
        for mat_id, count in required.items():
            self.materials[mat_id] -= count
            if self.materials[mat_id] <= 0:
                del self.materials[mat_id]
        return True
    
    def is_empty(self) -> bool:
        """是否为空"""
        return len(self.materials) == 0


@dataclass
class Shipwreck:
    """沉船实例"""
    id: str
    tier: ShipwreckTier
    location: Tuple[int, int]  # 地图坐标
    boss: Optional[MirrorGuard] = None
    guards: List[MirrorGuard] = field(default_factory=list)
    spawn_time: float = 0.0  # 刷新时间戳
    last_output_time: float = 0.0  # 上次产出时间
    total_output_value: int = 0  # 累计产出价值
    total_repair_cost: int = 0  # 累计维修成本
    
    def is_occupied(self) -> bool:
        """是否被占领"""
        return self.boss is not None
    
    def get_output_multiplier(self) -> float:
        """获取产出倍率（基于 Boss 耐久）"""
        if not self.boss:
            return 0.0
        return self.boss.get_durability_ratio()
    
    def add_guard(self, guard: MirrorGuard) -> bool:
        """添加护卫"""
        if len(self.guards) >= 2:
            return False
        self.guards.append(guard)
        return True
    
    def remove_guard(self, player_id: str) -> bool:
        """移除护卫"""
        for i, guard in enumerate(self.guards):
            if guard.player_id == player_id:
                self.guards.pop(i)
                return True
        return False


@dataclass
class BattleResult:
    """战斗结果"""
    winner_id: str
    loser_id: str
    attacker_durability_loss: int
    defender_durability_loss: int
    t1_success: bool  # T1 是否成功"刮痧"（即使战败）
    economic_damage: int  # 对防守方造成的经济损失


class VoyageSystem:
    """远航系统"""
    
    def __init__(self):
        self.shipwrecks: Dict[str, Shipwreck] = {}
        self.player_outposts: Dict[str, Tuple[int, int]] = {}  # player_id -> 据点坐标
        self.battle_records: List[BattleResult] = []
    
    def create_shipwreck(self, wreck_id: str, tier: ShipwreckTier, x: int, y: int) -> Shipwreck:
        """创建沉船"""
        wreck = Shipwreck(
            id=wreck_id,
            tier=tier,
            location=(x, y),
        )
        self.shipwrecks[wreck_id] = wreck
        return wreck
    
    def occupy_shipwreck(self, wreck_id: str, boss: MirrorGuard, guards: List[MirrorGuard]) -> bool:
        """占领沉船"""
        if wreck_id not in self.shipwrecks:
            return False
        
        wreck = self.shipwrecks[wreck_id]
        if wreck.is_occupied():
            return False  # 已被占领
        
        wreck.boss = boss
        for guard in guards[:2]:  # 最多 2 个护卫
            wreck.add_guard(guard)
        
        wreck.spawn_time = random.random()  # 简化时间戳
        wreck.last_output_time = wreck.spawn_time
        
        return True
    
    def calculate_repair_cost(
        self, 
        wreck: Shipwreck, 
        current_time: float,
        base_material_id: str = "repair_basic"
    ) -> Dict[str, int]:
        """
        计算战前自动修复成本（维保过载核心机制）
        
        公式：基础成本 × min(最大倍率，1 + (驻守时长^衰减率))
        
        驻守时间越长，成本非线性上升，最终超过产出收益
        """
        config = SHIPWRECK_CONFIGS[wreck.tier]
        
        # 计算驻守时长（小时）
        hold_duration = current_time - wreck.spawn_time
        if hold_duration < 0:
            hold_duration = 0
        
        # 非线性成本曲线（指数增长）
        cost_multiplier = 1 + math.pow(hold_duration, config.decay_rate)
        cost_multiplier = min(config.max_repair_cost_multiplier, cost_multiplier)
        
        # 基础修复成本（基于沉船等级）
        base_cost = {
            ShipwreckTier.T1: 10,
            ShipwreckTier.T2: 30,
            ShipwreckTier.T3: 100,
        }[wreck.tier]
        
        # 最终成本
        total_cost = int(base_cost * cost_multiplier)
        
        # 转换为材料需求（简化：全部用基础修复包）
        material_cost = {base_material_id: total_cost}
        
        # 记录累计成本
        wreck.total_repair_cost += total_cost
        
        return material_cost
    
    def produce_resources(self, wreck: Shipwreck, current_time: float) -> Dict[str, int]:
        """
        产出资源（基于 Boss 耐久百分比）
        """
        if not wreck.is_occupied():
            return {}
        
        config = SHIPWRECK_CONFIGS[wreck.tier]
        
        # 时间间隔（小时）
        time_delta = current_time - wreck.last_output_time
        if time_delta <= 0:
            return {}
        
        # 产出倍率（基于耐久）
        output_multiplier = wreck.get_output_multiplier()
        
        # 基础产出
        base_output = config.base_output_value * time_delta * output_multiplier
        
        # 转换为材料（简化：按沉船等级产出对应材料）
        output_materials = {
            ShipwreckTier.T1: [("wood_basic", 0.5), ("stone_basic", 0.3)],
            ShipwreckTier.T2: [("metal_iron", 0.2), ("fiber_cloth", 0.2)],
            ShipwreckTier.T3: [("metal_titanium", 0.05), ("collect_relic", 0.01)],
        }[wreck.tier]
        
        result = {}
        for mat_id, ratio in output_materials:
            count = int(base_output * ratio)
            if count > 0:
                result[mat_id] = count
                wreck.total_output_value += get_material(mat_id).base_value * count
        
        wreck.last_output_time = current_time
        
        return result
    
    def challenge_shipwreck(
        self, 
        wreck_id: str, 
        attacker: MirrorGuard,
        attacker_tier: int,  # 玩家阶段 T1/T2/T3
        defender_tier: int,
    ) -> Optional[BattleResult]:
        """
        挑战沉船
        
        核心：非对称战争
        T1 挑战 T3 即使战败，也能通过触发 T3 的高溢价修复来"经济剥蚀"大佬
        """
        if wreck_id not in self.shipwrecks:
            return None
        
        wreck = self.shipwrecks[wreck_id]
        if not wreck.is_occupied():
            return None
        
        defender = wreck.boss
        
        # 简化战斗模拟（实际应调用 combat.py）
        attack_power = self._calculate_power(attacker)
        defend_power = self._calculate_power(defender)
        
        # 耐久损耗
        attacker_loss = int(attacker.weapon_max_durability * 0.3)  # 攻击方损耗 30%
        defender_loss = int(defender.weapon_max_durability * 0.5)  # 防守方损耗 50%
        
        # 判定胜负
        if attack_power > defend_power:
            winner = attacker.player_id
            loser = defender.player_id
        else:
            winner = defender.player_id
            loser = attacker.player_id
        
        # T1 成功判定：即使战败，只要造成足够耐久损耗就算"刮痧成功"
        t1_success = False
        if attacker_tier == 1 and defender_tier == 3:
            if defender_loss >= defender.weapon_max_durability * 0.3:
                t1_success = True  # 成功刮痧
        
        # 经济损失（触发 T3 高溢价修复）
        economic_damage = 0
        if defender_tier == 3:
            # T3 被挑战后需要高成本修复
            repair_cost = self.calculate_repair_cost(wreck, random.random())
            economic_damage = sum(
                get_material(mat_id).base_value * count
                for mat_id, count in repair_cost.items()
            )
        
        result = BattleResult(
            winner_id=winner,
            loser_id=loser,
            attacker_durability_loss=attacker_loss,
            defender_durability_loss=defender_loss,
            t1_success=t1_success,
            economic_damage=economic_damage,
        )
        
        self.battle_records.append(result)
        
        # 如果攻击方胜利，占领沉船
        if winner == attacker.player_id:
            wreck.boss = attacker
        
        return result
    
    def _calculate_power(self, guard: MirrorGuard) -> int:
        """计算战力（简化）"""
        durability_ratio = guard.get_durability_ratio()
        base_power = {
            "burst": 25,
            "sustain": 18,
            "defense": 15,
        }.get(guard.fight_style, 15)
        
        return int(base_power * durability_ratio * 100)
    
    def get_battle_statistics(self) -> Dict:
        """获取战斗统计"""
        if not self.battle_records:
            return {"total_battles": 0}
        
        t1_success_count = sum(1 for r in self.battle_records if r.t1_success)
        total_economic_damage = sum(r.economic_damage for r in self.battle_records)
        
        return {
            "total_battles": len(self.battle_records),
            "t1_success_count": t1_success_count,
            "t1_success_rate": t1_success_count / len(self.battle_records),
            "total_economic_damage": total_economic_damage,
        }


def print_shipwreck_status(wreck: Shipwreck):
    """打印沉船状态"""
    print(f"\n【{wreck.tier.value}】{wreck.id}")
    print(f"位置：{wreck.location}")
    print(f"占领状态：{'已占领' if wreck.is_occupied() else '无人占领'}")
    
    if wreck.boss:
        print(f"Boss: {wreck.boss.player_id} ({wreck.boss.fight_style})")
        print(f"  耐久：{wreck.boss.get_durability_ratio()*100:.0f}%")
    
    if wreck.guards:
        print(f"护卫：{len(wreck.guards)}/2")
        for guard in wreck.guards:
            print(f"  - {guard.player_id} ({guard.fight_style})")
    
    print(f"累计产出：{wreck.total_output_value:,}")
    print(f"累计维修成本：{wreck.total_repair_cost:,}")


if __name__ == "__main__":
    # 测试远航系统
    print("=== 远航系统测试 ===\n")
    
    system = VoyageSystem()
    
    # 创建沉船
    wreck1 = system.create_shipwreck("wreck_001", ShipwreckTier.T1, 100, 200)
    wreck2 = system.create_shipwreck("wreck_002", ShipwreckTier.T2, 300, 400)
    wreck3 = system.create_shipwreck("wreck_003", ShipwreckTier.T3, 500, 600)
    
    # 创建镜像护卫
    boss_t1 = MirrorGuard(
        player_id="T1_玩家",
        role="boss",
        weapon_durability=100,
        weapon_max_durability=100,
        armor_durability=100,
        armor_max_durability=100,
        fight_style="sustain",
    )
    
    boss_t3 = MirrorGuard(
        player_id="T3_大佬",
        role="boss",
        weapon_durability=150,
        weapon_max_durability=150,
        armor_durability=150,
        armor_max_durability=150,
        fight_style="burst",
    )
    
    # 占领沉船
    system.occupy_shipwreck("wreck_001", boss_t1, [])
    system.occupy_shipwreck("wreck_003", boss_t3, [])
    
    # 打印状态
    for wreck in system.shipwrecks.values():
        print_shipwreck_status(wreck)
    
    # 测试维保过载
    print(f"\n{'='*60}")
    print("【维保过载测试】")
    print(f"{'='*60}")
    
    wreck = system.shipwrecks["wreck_003"]
    for hold_time in [0, 1, 5, 10, 20, 50]:
        wreck.spawn_time = 0  # 重置
        cost = system.calculate_repair_cost(wreck, hold_time)
        print(f"驻守{hold_time}小时 → 维修成本：{cost}")
    
    # 测试产出
    print(f"\n{'='*60}")
    print("【产出测试】")
    print(f"{'='*60}")
    
    for wreck in system.shipwrecks.values():
        if wreck.is_occupied():
            # 模拟耐久损耗
            if wreck.boss:
                wreck.boss.weapon_durability = int(wreck.boss.weapon_max_durability * 0.7)
            
            output = system.produce_resources(wreck, 1.0)  # 1 小时后
            print(f"{wreck.tier.value}: 产出 {output} (耐久{wreck.boss.get_durability_ratio()*100:.0f}%)")
    
    # 测试 T1 挑战 T3（非对称战争）
    print(f"\n{'='*60}")
    print("【非对称战争测试】T1 vs T3")
    print(f"{'='*60}")
    
    challenger = MirrorGuard(
        player_id="T1_挑战者",
        role="boss",
        weapon_durability=80,
        weapon_max_durability=80,
        armor_durability=80,
        armor_max_durability=80,
        fight_style="defense",
    )
    
    result = system.challenge_shipwreck("wreck_003", challenger, attacker_tier=1, defender_tier=3)
    
    if result:
        print(f"战斗结果：{result.winner_id} 获胜")
        print(f"T1 刮痧成功：{result.t1_success}")
        print(f"T3 经济损失：{result.economic_damage:,}")
    
    # 战斗统计
    print(f"\n{'='*60}")
    print("【战斗统计】")
    stats = system.get_battle_statistics()
    for key, value in stats.items():
        print(f"{key}: {value}")
