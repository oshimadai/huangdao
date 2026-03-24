# -*- coding: utf-8 -*-
"""
材料体系定义
制造材料 / 修复材料 / 工具耗材 / 收藏物件 / 事件组件
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List


class MaterialTier(Enum):
    """材料等级"""
    T1 = 1  # 基础
    T2 = 2  # 进阶
    T3 = 3  # 高级
    T4 = 4  # 顶级（深渊）


class MaterialType(Enum):
    """材料类型"""
    MANUFACTURING = "制造材料"  # 用于制作武器/工具
    REPAIR = "修复材料"  # 用于修复耐久
    CONSUMABLE = "工具耗材"  # 采集消耗品
    COLLECTIBLE = "收藏物件"  # 可交易收藏品
    EVENT = "事件组件"  # 漂流箱事件触发


@dataclass
class Material:
    """材料定义"""
    id: str
    name: str
    type: MaterialType
    tier: MaterialTier
    base_value: int  # 基础价值（交易参考）
    stack_size: int = 99  # 堆叠上限
    tradable: bool = True  # 是否可交易
    description: str = ""


# ============ 材料清单 ============

MATERIALS: Dict[str, Material] = {
    # === 制造材料 ===
    "wood_basic": Material("wood_basic", "普通木材", MaterialType.MANUFACTURING, MaterialTier.T1, 5, description="基础建筑材料"),
    "wood_hard": Material("wood_hard", "硬木", MaterialType.MANUFACTURING, MaterialTier.T2, 15, description="制作高级武器"),
    "wood_iron": Material("wood_iron", "铁木", MaterialType.MANUFACTURING, MaterialTier.T3, 40, description="稀有木材，极硬"),
    
    "stone_basic": Material("stone_basic", "普通石材", MaterialType.MANUFACTURING, MaterialTier.T1, 8, description="基础建筑材料"),
    "stone_marble": Material("stone_marble", "大理石", MaterialType.MANUFACTURING, MaterialTier.T2, 20, description="精美石材"),
    "stone_obsidian": Material("stone_obsidian", "黑曜石", MaterialType.MANUFACTURING, MaterialTier.T3, 50, description="火山玻璃，锋利"),
    
    "metal_scrap": Material("metal_scrap", "废金属", MaterialType.MANUFACTURING, MaterialTier.T1, 12, description="回收金属"),
    "metal_iron": Material("metal_iron", "铁锭", MaterialType.MANUFACTURING, MaterialTier.T2, 30, description="精炼铁"),
    "metal_steel": Material("metal_steel", "钢锭", MaterialType.MANUFACTURING, MaterialTier.T3, 80, description="高强度钢"),
    "metal_titanium": Material("metal_titanium", "钛合金", MaterialType.MANUFACTURING, MaterialTier.T4, 200, description="深渊特产，极轻极强"),
    
    "fiber_rope": Material("fiber_rope", "绳索", MaterialType.MANUFACTURING, MaterialTier.T1, 10, description="基础编织物"),
    "fiber_cloth": Material("fiber_cloth", "布料", MaterialType.MANUFACTURING, MaterialTier.T2, 25, description="精细布料"),
    "fiber_kevlar": Material("fiber_kevlar", "凯夫拉纤维", MaterialType.MANUFACTURING, MaterialTier.T3, 70, description="防弹纤维"),
    
    # === 修复材料 ===
    "repair_basic": Material("repair_basic", "基础修复包", MaterialType.REPAIR, MaterialTier.T1, 20, description="修复基础耐久"),
    "repair_advanced": Material("repair_advanced", "高级修复包", MaterialType.REPAIR, MaterialTier.T2, 50, description="修复进阶耐久"),
    "repair_premium": Material("repair_premium", "特级修复包", MaterialType.REPAIR, MaterialTier.T3, 120, description="完全修复"),
    
    # === 工具耗材 ===
    "consumable_oil": Material("consumable_oil", "润滑油", MaterialType.CONSUMABLE, MaterialTier.T1, 15, description="采集工具润滑"),
    "consumable_whetstone": Material("consumable_whetstone", "磨刀石", MaterialType.CONSUMABLE, MaterialTier.T1, 18, description="打磨工具"),
    "consumable_battery": Material("consumable_battery", "电池", MaterialType.CONSUMABLE, MaterialTier.T2, 35, description="电动工具能源"),
    
    # === 收藏物件（可交易，带传播属性）===
    "collect_shell_common": Material("collect_shell_common", "普通贝壳", MaterialType.COLLECTIBLE, MaterialTier.T1, 3, description="常见贝壳"),
    "collect_shell_rare": Material("collect_shell_rare", "彩虹贝壳", MaterialType.COLLECTIBLE, MaterialTier.T2, 25, description="稀有贝壳，编号收藏"),
    "collect_bottle_message": Material("collect_bottle_message", "漂流瓶", MaterialType.COLLECTIBLE, MaterialTier.T2, 40, description="内含神秘信息"),
    "collect_treasure_map": Material("collect_treasure_map", "藏宝图碎片", MaterialType.COLLECTIBLE, MaterialTier.T3, 60, description="集齐可兑换奖励"),
    "collect_ancient_coin": Material("collect_ancient_coin", "古金币", MaterialType.COLLECTIBLE, MaterialTier.T3, 100, description="古代文明遗物"),
    "collect_relic": Material("collect_relic", "深渊遗物", MaterialType.COLLECTIBLE, MaterialTier.T4, 500, description="深渊控制者专属，编号唯一"),
    
    # === 事件组件（用于漂流箱事件）===
    "event_compass": Material("event_compass", "旧罗盘", MaterialType.EVENT, MaterialTier.T1, 15, description="触发导航事件"),
    "event_key": Material("event_key", "生锈钥匙", MaterialType.EVENT, MaterialTier.T2, 30, description="触发宝藏事件"),
    "event_crystal": Material("event_crystal", "能量水晶", MaterialType.EVENT, MaterialTier.T3, 80, description="触发特殊事件"),
}


def get_material(material_id: str) -> Material:
    """获取材料定义"""
    if material_id not in MATERIALS:
        raise ValueError(f"未知材料：{material_id}")
    return MATERIALS[material_id]


def get_materials_by_type(material_type: MaterialType) -> List[Material]:
    """按类型获取材料列表"""
    return [m for m in MATERIALS.values() if m.type == material_type]


def get_materials_by_tier(tier: MaterialTier) -> List[Material]:
    """按等级获取材料列表"""
    return [m for m in MATERIALS.values() if m.tier == tier]


if __name__ == "__main__":
    # 测试输出
    print("=== 材料体系 ===\n")
    for mtype in MaterialType:
        print(f"\n【{mtype.value}】")
        materials = get_materials_by_type(mtype)
        for mat in materials:
            print(f"  {mat.name} (T{mat.tier.value}) - 价值：{mat.base_value}")
