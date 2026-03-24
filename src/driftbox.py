# -*- coding: utf-8 -*-
"""
漂流箱系统
海滩漂流箱开箱 - 前期核心产出
包含：基础材料 / 收藏物件 / 事件组件 / 稀有物品
"""

import random
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
from enum import Enum

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from materials import Material, MaterialTier, MaterialType, MATERIALS, get_material


class DriftBoxTier(Enum):
    """漂流箱等级"""
    COMMON = "普通"      # 浅海，新人层
    RARE = "稀有"        # 深海，竞争层
    EPIC = "史诗"        # 深渊，顶级层
    LEGENDARY = "传说"   # 特殊事件


@dataclass
class DropEntry:
    """掉落条目"""
    material_id: str
    min_count: int
    max_count: int
    weight: float  # 权重
    tier_required: MaterialTier = MaterialTier.T1


@dataclass
class DriftBoxConfig:
    """漂流箱配置"""
    tier: DriftBoxTier
    name: str
    drop_table: List[DropEntry]
    guaranteed_slots: int = 3  # 保底格子数
    bonus_slots: int = 2  # 额外随机格子


# ============ 漂流箱掉落表 ============

def create_drop_tables() -> Dict[DriftBoxTier, DriftBoxConfig]:
    """创建各等级漂流箱掉落表"""
    
    # 普通箱（浅海）- 基础材料为主
    common_drops = [
        DropEntry("wood_basic", 5, 15, 30),
        DropEntry("stone_basic", 3, 10, 25),
        DropEntry("metal_scrap", 2, 6, 20),
        DropEntry("fiber_rope", 2, 5, 15),
        DropEntry("collect_shell_common", 1, 3, 10),
        DropEntry("repair_basic", 1, 2, 8),
        DropEntry("event_compass", 0, 1, 5),
        DropEntry("collect_shell_rare", 0, 1, 3),
    ]
    
    # 稀有箱（深海）- 进阶材料 + 收藏
    rare_drops = [
        DropEntry("wood_hard", 3, 8, 20),
        DropEntry("stone_marble", 2, 6, 18),
        DropEntry("metal_iron", 2, 5, 20),
        DropEntry("fiber_cloth", 2, 5, 15),
        DropEntry("repair_advanced", 1, 2, 12),
        DropEntry("collect_bottle_message", 0, 1, 8),
        DropEntry("event_key", 0, 1, 5),
        DropEntry("collect_treasure_map", 0, 1, 4),
        DropEntry("consumable_oil", 1, 3, 10),
    ]
    
    # 史诗箱（深渊）- 高级材料 + 稀有收藏
    epic_drops = [
        DropEntry("wood_iron", 2, 5, 15),
        DropEntry("stone_obsidian", 1, 4, 15),
        DropEntry("metal_steel", 1, 3, 18),
        DropEntry("fiber_kevlar", 1, 3, 15),
        DropEntry("repair_premium", 1, 2, 12),
        DropEntry("collect_ancient_coin", 0, 1, 8),
        DropEntry("event_crystal", 0, 1, 5),
        DropEntry("metal_titanium", 0, 2, 10),
        DropEntry("collect_relic", 0, 1, 2),
    ]
    
    return {
        DriftBoxTier.COMMON: DriftBoxConfig(DriftBoxTier.COMMON, "普通漂流箱", common_drops),
        DriftBoxTier.RARE: DriftBoxConfig(DriftBoxTier.RARE, "稀有漂流箱", rare_drops),
        DriftBoxTier.EPIC: DriftBoxConfig(DriftBoxTier.EPIC, "史诗漂流箱", epic_drops),
    }


@dataclass
class DriftBoxResult:
    """开箱结果"""
    box_tier: DriftBoxTier
    items: List[Tuple[str, int]]  # (material_id, count)
    rare_finds: List[str]  # 稀有物品 ID 列表
    total_value: int  # 总价值


class DriftBoxSystem:
    """漂流箱系统"""
    
    def __init__(self):
        self.configs = create_drop_tables()
        self.stats = {
            "total_opened": 0,
            "by_tier": {tier: 0 for tier in DriftBoxTier},
        }
    
    def open_box(self, tier: DriftBoxTier, beach_level: int = 1) -> DriftBoxResult:
        """
        开启漂流箱
        beach_level: 沙滩等级，影响产出上限
        """
        config = self.configs[tier]
        items = []
        rare_finds = []
        
        # 保底格子
        for _ in range(config.guaranteed_slots):
            item = self._roll_drop(config.drop_table, tier)
            if item:
                items.append(item)
                if self._is_rare(item[0]):
                    rare_finds.append(item[0])
        
        # 额外随机格子（概率触发）
        for _ in range(config.bonus_slots):
            if random.random() < 0.6:  # 60% 概率触发额外格子
                item = self._roll_drop(config.drop_table, tier)
                if item:
                    items.append(item)
                    if self._is_rare(item[0]):
                        rare_finds.append(item[0])
        
        # 计算总价值
        total_value = sum(
            get_material(mat_id).base_value * count 
            for mat_id, count in items
        )
        
        # 更新统计
        self.stats["total_opened"] += 1
        self.stats["by_tier"][tier] += 1
        
        return DriftBoxResult(
            box_tier=tier,
            items=items,
            rare_finds=rare_finds,
            total_value=total_value,
        )
    
    def _roll_drop(self, drop_table: List[DropEntry], box_tier: DriftBoxTier) -> Optional[Tuple[str, int]]:
        """根据权重随机选择掉落"""
        total_weight = sum(entry.weight for entry in drop_table)
        if total_weight == 0:
            return None
        
        roll = random.uniform(0, total_weight)
        cumulative = 0
        
        for entry in drop_table:
            cumulative += entry.weight
            if roll <= cumulative:
                # 检查是否可能掉落 0 个
                if entry.min_count == 0 and random.random() < 0.5:
                    return None
                
                count = random.randint(entry.min_count, entry.max_count)
                return (entry.material_id, count)
        
        return None
    
    def _is_rare(self, material_id: str) -> bool:
        """判断是否为稀有物品"""
        mat = get_material(material_id)
        return (
            mat.type == MaterialType.COLLECTIBLE or
            mat.type == MaterialType.EVENT or
            mat.tier in [MaterialTier.T3, MaterialTier.T4]
        )
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return self.stats.copy()


def print_open_result(result: DriftBoxResult):
    """打印开箱结果"""
    print(f"\n【{result.box_tier.value}漂流箱】")
    print("-" * 40)
    
    # 按类型分组显示
    by_type: Dict[str, List[Tuple[str, int]]] = {}
    for mat_id, count in result.items:
        mat = get_material(mat_id)
        type_name = mat.type.value
        if type_name not in by_type:
            by_type[type_name] = []
        by_type[type_name].append((mat.name, count))
    
    for type_name, items in by_type.items():
        print(f"\n{type_name}:")
        for name, count in items:
            print(f"  • {name} ×{count}")
    
    if result.rare_finds:
        print(f"\n⭐ 稀有发现：{len(result.rare_finds)} 件")
        for rare_id in result.rare_finds:
            print(f"  ✨ {get_material(rare_id).name}")
    
    print(f"\n💰 总价值：{result.total_value}")


if __name__ == "__main__":
    # 测试开箱系统
    print("=== 漂流箱系统测试 ===\n")
    
    system = DriftBoxSystem()
    
    # 模拟各等级开箱
    for tier in DriftBoxTier:
        print(f"\n{'='*60}")
        result = system.open_box(tier)
        print_open_result(result)
    
    # 显示统计
    print(f"\n{'='*60}")
    print("\n【开箱统计】")
    stats = system.get_stats()
    print(f"总开箱数：{stats['total_opened']}")
    for tier, count in stats['by_tier'].items():
        print(f"  {tier.value}: {count}")
