# -*- coding: utf-8 -*-
"""
单元测试 - 验证各系统功能
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from materials import MaterialType, MaterialTier, get_materials_by_type, get_materials_by_tier
from combat import create_weapon, FightStyle, simulate_combat, Fighter
from driftbox import DriftBoxSystem, DriftBoxTier
from economy import EconomySystem


def test_materials():
    """测试材料系统"""
    print("\n" + "="*60)
    print("【材料系统测试】")
    print("="*60)
    
    # 按类型统计
    for mtype in MaterialType:
        materials = get_materials_by_type(mtype)
        print(f"\n{mtype.value}: {len(materials)} 种")
    
    # 按等级统计
    for tier in MaterialTier:
        materials = get_materials_by_tier(tier)
        print(f"T{tier.value} 材料：{len(materials)} 种")
    
    print(f"\n✓ 材料系统正常")


def test_combat():
    """测试战斗系统"""
    print("\n" + "="*60)
    print("【战斗系统测试】")
    print("="*60)
    
    # 创建三流派武器
    for style in FightStyle:
        weapon = create_weapon(style)
        print(f"\n{style.value}:")
        print(f"  武器：{weapon.name}")
        print(f"  基础攻击：{weapon.base_attack}")
        print(f"  耐久：{weapon.max_durability}")
        print(f"  消耗系数：{weapon.durability_cost}")
        
        # 测试耐久公式
        for durability_ratio in [1.0, 0.5, 0.2, 0.0]:
            weapon.current_durability = int(weapon.max_durability * durability_ratio)
            attack = weapon.get_attack(1.0)
            print(f"  耐久{durability_ratio*100:.0f}% → 攻击：{attack}")
    
    # 模拟一场战斗
    print("\n【模拟战斗】")
    f1 = Fighter("爆发", create_weapon(FightStyle.BURST))
    f2 = Fighter("防御", create_weapon(FightStyle.DEFENSE))
    result = simulate_combat(f1, f2, max_rounds=15, damage_delta=0.05)
    print(f"结果：{result.winner} 获胜，{result.total_rounds} 回合")
    print(f"✓ 战斗系统正常")


def test_driftbox():
    """测试漂流箱系统"""
    print("\n" + "="*60)
    print("【漂流箱系统测试】")
    print("="*60)
    
    system = DriftBoxSystem()
    
    # 各等级开箱 10 次统计（排除未配置的 LEGENDARY）
    for tier in [DriftBoxTier.COMMON, DriftBoxTier.RARE, DriftBoxTier.EPIC]:
        total_value = 0
        rare_count = 0
        
        for _ in range(10):
            result = system.open_box(tier)
            total_value += result.total_value
            rare_count += len(result.rare_finds)
        
        avg_value = total_value / 10
        avg_rare = rare_count / 10
        
        print(f"{tier.value}: 平均价值 {avg_value:.0f}, 平均稀有物品 {avg_rare:.1f} 件")
    
    print(f"✓ 漂流箱系统正常")


def test_economy():
    """测试经济系统"""
    print("\n" + "="*60)
    print("【经济系统测试】")
    print("="*60)
    
    economy = EconomySystem()
    
    # 创建玩家
    for i in range(5):
        economy.register_player(f"p{i}", stage=(i // 2) + 1)
    
    # 模拟产出
    for i in range(50):
        pid = f"p{i % 5}"
        mat_id = ["wood_basic", "metal_scrap", "stone_basic"][i % 3]
        economy.produce_material(pid, mat_id, 10)
    
    # 模拟交易
    for i in range(10):
        seller = f"p{i % 2}"
        buyer = f"p{2 + i % 3}"
        economy.trade(seller, buyer, "wood_basic", 5, 6)
    
    # 生成报告
    report = economy.generate_report()
    print(f"玩家数：{report.total_players}")
    print(f"材料总价值：{report.total_material_value:,}")
    print(f"交易量：{report.trade_volume_24h}")
    
    # 检查流通次数
    wood_stats = economy.material_stats.get("wood_basic")
    if wood_stats:
        print(f"木材流通次数：{wood_stats.circulation_times:.2f}")
    
    print(f"✓ 经济系统正常")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("🧪 荒岛生存 - 系统测试")
    print("="*60)
    
    try:
        test_materials()
        test_combat()
        test_driftbox()
        test_economy()
        
        print("\n" + "="*60)
        print("✅ 所有测试通过")
        print("="*60 + "\n")
        return True
    except Exception as e:
        print(f"\n❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
