# -*- coding: utf-8 -*-
"""
战斗系统模拟
回合制，15 回合，60 秒目标
三流派：爆发 / 消耗 / 防御
耐久公式：实际攻击 = 基础攻击 × ((1-n) + n×(当前耐久/最大耐久)) × R
"""

import random
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum


class FightStyle(Enum):
    """战斗流派"""
    BURST = "爆发"  # 高攻击，高耐久消耗
    SUSTAIN = "消耗"  # 稳定输出，中等消耗
    DEFENSE = "防御"  # 格挡减伤，低消耗


@dataclass
class Weapon:
    """武器"""
    name: str
    base_attack: int  # 基础攻击
    max_durability: int  # 最大耐久
    current_durability: int  # 当前耐久
    fight_style: FightStyle
    durability_cost: float  # 每次攻击耐久消耗系数
    
    def get_attack(self, damage_random_factor: float = 1.0) -> int:
        """
        计算实际攻击力
        公式：实际攻击 = 基础攻击 × ((1-n) + n×(当前耐久/最大耐久)) × R
        n 默认 0.8（耐久 0 仍有 20% 底座输出）
        """
        n = 0.8  # 耐久系数
        if self.max_durability == 0:
            durability_ratio = 0
        else:
            durability_ratio = self.current_durability / self.max_durability
        
        base_multiplier = (1 - n) + n * durability_ratio
        actual_attack = int(self.base_attack * base_multiplier * damage_random_factor)
        return max(1, actual_attack)  # 至少造成 1 点伤害
    
    def take_durability_damage(self, damage_random_factor: float = 1.0):
        """承受耐久损耗"""
        cost = self.durability_cost * damage_random_factor
        self.current_durability = max(0, self.current_durability - cost)
    
    def is_broken(self) -> bool:
        """是否损坏（耐久为 0）"""
        return self.current_durability <= 0
    
    def repair(self, amount: int):
        """修复耐久"""
        self.current_durability = min(self.max_durability, self.current_durability + amount)
    
    def get_status(self) -> str:
        """获取状态描述"""
        ratio = self.current_durability / self.max_durability if self.max_durability > 0 else 0
        if ratio > 0.7:
            return "完好"
        elif ratio > 0.3:
            return "破损"
        else:
            return "损坏"


@dataclass
class Armor:
    """防具"""
    name: str
    base_defense: int
    max_durability: int
    current_durability: int
    
    def get_defense_multiplier(self) -> float:
        """
        获取防御倍率
        三状态：完好 100% / 破损 70% / 损坏 40%
        """
        ratio = self.current_durability / self.max_durability if self.max_durability > 0 else 0
        if ratio > 0.7:
            return 1.0
        elif ratio > 0.3:
            return 0.7
        else:
            return 0.4
    
    def take_damage(self, damage: int) -> int:
        """
        承受伤害，返回实际受到伤害
        """
        actual_damage = int(damage * self.get_defense_multiplier())
        # 防具耐久损耗
        durability_loss = damage * 0.5  # 简化：伤害的 50% 转为耐久损耗
        self.current_durability = max(0, self.current_durability - durability_loss)
        return actual_damage
    
    def repair(self, amount: int):
        """修复耐久"""
        self.current_durability = min(self.max_durability, self.current_durability + amount)


@dataclass
class Fighter:
    """战斗者"""
    name: str
    weapon: Weapon
    armor: Optional[Armor] = None
    hp: int = 100
    max_hp: int = 100
    
    def is_alive(self) -> bool:
        return self.hp > 0
    
    def take_damage(self, damage: int) -> int:
        """承受伤害，返回实际损失 HP"""
        if self.armor:
            actual_damage = self.armor.take_damage(damage)
        else:
            actual_damage = damage
        self.hp = max(0, self.hp - actual_damage)
        return actual_damage


@dataclass
class CombatLog:
    """战斗日志"""
    round: int
    attacker: str
    defender: str
    damage_random_factor: float  # R 值
    raw_attack: int  # 原始攻击
    actual_damage: int  # 实际伤害
    weapon_durability_after: int  # 攻击后武器耐久
    armor_status: str  # 防具状态
    defender_hp_after: int  # 防御者 HP
    notes: str = ""


@dataclass
class CombatResult:
    """战斗结果"""
    winner: str
    total_rounds: int
    logs: List[CombatLog] = field(default_factory=list)
    
    def print_report(self):
        """打印战斗复盘报告"""
        print(f"\n{'='*60}")
        print(f"战斗结果：{self.winner} 获胜")
        print(f"总回合数：{self.total_rounds}")
        print(f"{'='*60}\n")
        
        print("【战斗复盘】")
        print(f"{'回合':<6} {'攻击方':<10} {'R 值':<8} {'原始攻击':<10} {'实际伤害':<10} {'武器耐久':<10} {'防具':<8} {'对方 HP':<8}")
        print("-" * 80)
        
        for log in self.logs:
            print(f"{log.round:<6} {log.attacker:<10} {log.damage_random_factor:<8.3f} {log.raw_attack:<10} {log.actual_damage:<10} {int(log.weapon_durability_after):<10} {log.armor_status:<8} {log.defender_hp_after:<8}")


def create_weapon(fight_style: FightStyle) -> Weapon:
    """根据流派创建武器"""
    configs = {
        FightStyle.BURST: {
            "name": "爆裂之刃",
            "base_attack": 25,
            "max_durability": 80,
            "durability_cost": 8.0,  # 高消耗
        },
        FightStyle.SUSTAIN: {
            "name": "持久之矛",
            "base_attack": 18,
            "max_durability": 120,
            "durability_cost": 4.0,  # 中等消耗
        },
        FightStyle.DEFENSE: {
            "name": "守护之剑",
            "base_attack": 15,
            "max_durability": 150,
            "durability_cost": 2.5,  # 低消耗
        },
    }
    cfg = configs[fight_style]
    return Weapon(
        name=cfg["name"],
        base_attack=cfg["base_attack"],
        max_durability=cfg["max_durability"],
        current_durability=cfg["max_durability"],
        fight_style=fight_style,
        durability_cost=cfg["durability_cost"],
    )


def simulate_combat(fighter1: Fighter, fighter2: Fighter, max_rounds: int = 15, damage_delta: float = 0.05) -> CombatResult:
    """
    模拟战斗
    damage_delta: 伤害随机因子区间（例如 0.05 表示 ±5%）
    """
    logs = []
    
    for round_num in range(1, max_rounds + 1):
        if not fighter1.is_alive() or not fighter2.is_alive():
            break
        
        # 决定先手（简化：轮流攻击）
        attacker = fighter1 if round_num % 2 == 1 else fighter2
        defender = fighter2 if round_num % 2 == 1 else fighter1
        
        # 计算伤害随机因子 R (1 ± delta)
        R = 1.0 + random.uniform(-damage_delta, damage_delta)
        
        # 计算原始攻击力（未考虑防御）
        raw_attack = attacker.weapon.get_attack(R)
        
        # 承受伤害
        actual_damage = defender.take_damage(raw_attack)
        
        # 武器耐久损耗
        attacker.weapon.take_durability_damage(R)
        
        # 记录日志
        armor_status = defender.armor.get_status() if defender.armor else "无"
        log = CombatLog(
            round=round_num,
            attacker=attacker.name,
            defender=defender.name,
            damage_random_factor=R,
            raw_attack=raw_attack,
            actual_damage=actual_damage,
            weapon_durability_after=attacker.weapon.current_durability,
            armor_status=armor_status,
            defender_hp_after=defender.hp,
        )
        logs.append(log)
        
        # 检查是否结束
        if defender.hp <= 0:
            break
    
    # 判定胜负
    if fighter1.hp > fighter2.hp:
        winner = fighter1.name
    elif fighter2.hp > fighter1.hp:
        winner = fighter2.name
    else:
        winner = "平局"
    
    return CombatResult(winner=winner, total_rounds=len(logs), logs=logs)


if __name__ == "__main__":
    # 测试战斗模拟
    print("=== 战斗系统测试 ===\n")
    
    # 创建三流派战士
    burst_fighter = Fighter("爆发战士", create_weapon(FightStyle.BURST), hp=100)
    sustain_fighter = Fighter("消耗战士", create_weapon(FightStyle.SUSTAIN), hp=100)
    defense_fighter = Fighter("防御战士", create_weapon(FightStyle.DEFENSE), hp=100)
    
    # 模拟克制关系：爆发 > 防御 > 消耗 > 爆发
    print("\n【爆发 vs 防御】")
    result = simulate_combat(burst_fighter, defense_fighter)
    result.print_report()
    
    print("\n【消耗 vs 爆发】")
    result = simulate_combat(sustain_fighter, burst_fighter)
    result.print_report()
