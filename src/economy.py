# -*- coding: utf-8 -*-
"""
经济追踪系统
监控：材料产出量 / 消耗量 / 存量 / 流通次数 / 集中度
用于宏观调控（而非直接调价）
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from collections import defaultdict
import json
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from materials import Material, MaterialTier, MaterialType, MATERIALS, get_material


@dataclass
class TransactionRecord:
    """交易记录"""
    timestamp: float
    seller_id: str
    buyer_id: str
    material_id: str
    count: int
    price_per_unit: int
    total_price: int


@dataclass
class MaterialStats:
    """材料统计"""
    material_id: str
    total_produced: int = 0  # 总产出
    total_consumed: int = 0  # 总消耗
    total_traded: int = 0  # 总交易量
    trade_count: int = 0  # 交易次数
    avg_price: float = 0.0  # 平均交易价
    circulation_times: float = 0.0  # 流通次数（交易量/产出量）
    concentration: float = 0.0  # 集中度（头部玩家持有比例）


@dataclass
class PlayerInventory:
    """玩家库存"""
    player_id: str
    stage: int = 1  # 玩家阶段（影响产出上限）
    materials: Dict[str, int] = field(default_factory=dict)
    total_value: int = 0
    
    def add_material(self, material_id: str, count: int):
        """添加材料"""
        if material_id not in self.materials:
            self.materials[material_id] = 0
        self.materials[material_id] += count
        self._update_value()
    
    def remove_material(self, material_id: str, count: int) -> bool:
        """消耗材料"""
        if material_id not in self.materials or self.materials[material_id] < count:
            return False
        self.materials[material_id] -= count
        if self.materials[material_id] <= 0:
            del self.materials[material_id]
        self._update_value()
        return True
    
    def _update_value(self):
        """更新总价值"""
        self.total_value = sum(
            get_material(mat_id).base_value * count
            for mat_id, count in self.materials.items()
        )


@dataclass
class EconomyReport:
    """经济报告"""
    timestamp: str
    total_players: int
    total_material_value: int
    material_stats: List[MaterialStats]
    trade_volume_24h: int  # 24 小时交易量
    player_stage_distribution: Dict[int, int]  # 玩家阶段分布


class EconomySystem:
    """经济系统"""
    
    def __init__(self):
        self.players: Dict[str, PlayerInventory] = {}
        self.transactions: List[TransactionRecord] = []
        self.material_stats: Dict[str, MaterialStats] = {}
        self.production_limits: Dict[str, Dict[int, int]] = {}  # 阶段产出上限
        
        # 初始化材料统计
        for mat_id in MATERIALS:
            self.material_stats[mat_id] = MaterialStats(material_id=mat_id)
        
        # 配置阶段产出上限（防止小号刷材料）
        self._setup_production_limits()
    
    def _setup_production_limits(self):
        """设置阶段产出上限"""
        # 格式：material_id -> {stage: limit}
        # 低阶段达到上限后收益递减
        self.production_limits = {
            "wood_basic": {1: 1000, 2: 5000, 3: 999999},
            "stone_basic": {1: 800, 2: 4000, 3: 999999},
            "metal_scrap": {1: 500, 2: 2500, 3: 999999},
            "metal_titanium": {1: 0, 2: 0, 3: 500},  # 顶级材料只能阶段 3 产出
        }
    
    def register_player(self, player_id: str, stage: int = 1):
        """注册玩家"""
        if player_id not in self.players:
            self.players[player_id] = PlayerInventory(player_id=player_id, stage=stage)
    
    def produce_material(self, player_id: str, material_id: str, count: int) -> int:
        """
        产出材料（受阶段上限限制）
        返回实际产出数量
        """
        if player_id not in self.players:
            self.register_player(player_id)
        
        player = self.players[player_id]
        mat = get_material(material_id)
        
        # 检查阶段产出上限
        if material_id in self.production_limits:
            limits = self.production_limits[material_id]
            limit = limits.get(player.stage, limits.get(1, 999999))
            
            current_owned = player.materials.get(material_id, 0)
            if current_owned >= limit:
                # 已达到上限，收益大幅降低
                count = max(0, count // 10)  # 降至 10%
        
        # 添加材料
        player.add_material(material_id, count)
        
        # 更新统计
        self.material_stats[material_id].total_produced += count
        
        return count
    
    def consume_material(self, player_id: str, material_id: str, count: int) -> bool:
        """消耗材料（制作/修复等）"""
        if player_id not in self.players:
            return False
        
        player = self.players[player_id]
        if player.remove_material(material_id, count):
            self.material_stats[material_id].total_consumed += count
            return True
        return False
    
    def trade(
        self, 
        seller_id: str, 
        buyer_id: str, 
        material_id: str, 
        count: int, 
        price_per_unit: int
    ) -> bool:
        """
        玩家间交易
        """
        if seller_id not in self.players or buyer_id not in self.players:
            return False
        
        seller = self.players[seller_id]
        buyer = self.players[buyer_id]
        
        # 检查卖家是否有足够材料
        if not seller.remove_material(material_id, count):
            return False
        
        # 简化：不追踪货币，只转移材料
        buyer.add_material(material_id, count)
        
        # 记录交易
        total_price = count * price_per_unit
        record = TransactionRecord(
            timestamp=datetime.now().timestamp(),
            seller_id=seller_id,
            buyer_id=buyer_id,
            material_id=material_id,
            count=count,
            price_per_unit=price_per_unit,
            total_price=total_price,
        )
        self.transactions.append(record)
        
        # 更新统计
        stats = self.material_stats[material_id]
        stats.total_traded += count
        stats.trade_count += 1
        # 更新平均价格
        stats.avg_price = (stats.avg_price * (stats.trade_count - 1) + price_per_unit) / stats.trade_count
        
        return True
    
    def get_circulation_times(self, material_id: str) -> float:
        """计算流通次数（交易量/产出量）"""
        stats = self.material_stats[material_id]
        if stats.total_produced == 0:
            return 0.0
        return stats.total_traded / stats.total_produced
    
    def get_concentration(self, material_id: str, top_percent: float = 0.2) -> float:
        """
        计算集中度（头部玩家持有比例）
        """
        if material_id not in MATERIALS:
            return 0.0
        
        # 获取所有玩家该材料持有量
        holdings = [
            (player_id, inv.materials.get(material_id, 0))
            for player_id, inv in self.players.items()
        ]
        
        if not holdings or sum(h[1] for h in holdings) == 0:
            return 0.0
        
        # 排序
        holdings.sort(key=lambda x: x[1], reverse=True)
        total = sum(h[1] for h in holdings)
        
        # 计算头部玩家持有比例
        top_count = max(1, int(len(holdings) * top_percent))
        top_holding = sum(h[1] for h in holdings[:top_count])
        
        return top_holding / total
    
    def generate_report(self) -> EconomyReport:
        """生成经济报告"""
        # 更新流通次数和集中度
        for mat_id in self.material_stats:
            self.material_stats[mat_id].circulation_times = self.get_circulation_times(mat_id)
            self.material_stats[mat_id].concentration = self.get_concentration(mat_id)
        
        # 计算 24 小时交易量（简化：全部）
        trade_volume_24h = sum(t.count for t in self.transactions)
        
        # 玩家阶段分布
        stage_dist = defaultdict(int)
        for player in self.players.values():
            stage_dist[player.stage] += 1
        
        # 总材料价值
        total_value = sum(p.total_value for p in self.players.values())
        
        return EconomyReport(
            timestamp=datetime.now().isoformat(),
            total_players=len(self.players),
            total_material_value=total_value,
            material_stats=list(self.material_stats.values()),
            trade_volume_24h=trade_volume_24h,
            player_stage_distribution=dict(stage_dist),
        )
    
    def print_report(self, report: EconomyReport):
        """打印经济报告"""
        print(f"\n{'='*60}")
        print(f"【经济报告】{report.timestamp}")
        print(f"{'='*60}")
        
        print(f"\n玩家总数：{report.total_players}")
        print(f"材料总价值：{report.total_material_value:,}")
        print(f"24h 交易量：{report.trade_volume_24h:,}")
        
        print(f"\n【玩家阶段分布】")
        for stage, count in sorted(report.player_stage_distribution.items()):
            print(f"  阶段{stage}: {count} 人")
        
        print(f"\n【关键材料监控】")
        print(f"{'材料':<15} {'产出':<10} {'消耗':<10} {'交易':<10} {'流通':<8} {'集中':<8}")
        print("-" * 60)
        
        # 筛选重要材料
        key_materials = [
            "wood_basic", "metal_scrap", "metal_iron", "metal_steel", "metal_titanium",
            "repair_basic", "repair_advanced", "collect_relic"
        ]
        
        for mat_id in key_materials:
            if mat_id in self.material_stats:
                stats = self.material_stats[mat_id]
                mat = get_material(mat_id)
                print(f"{mat.name:<15} {stats.total_produced:<10} {stats.total_consumed:<10} {stats.total_traded:<10} {stats.circulation_times:<8.2f} {stats.concentration:<8.2f}")


if __name__ == "__main__":
    # 测试经济系统
    print("=== 经济追踪系统测试 ===\n")
    
    economy = EconomySystem()
    
    # 模拟玩家
    for i in range(10):
        stage = 1 if i < 5 else (2 if i < 8 else 3)
        economy.register_player(f"player_{i}", stage=stage)
    
    # 模拟产出
    import random
    for i in range(100):
        player_id = f"player_{random.randint(0, 9)}"
        mat_id = random.choice(["wood_basic", "metal_scrap", "metal_iron"])
        count = random.randint(5, 20)
        economy.produce_material(player_id, mat_id, count)
    
    # 模拟交易
    for i in range(30):
        seller = f"player_{random.randint(0, 4)}"
        buyer = f"player_{random.randint(5, 9)}"
        mat_id = random.choice(["wood_basic", "metal_scrap"])
        count = random.randint(1, 10)
        price = get_material(mat_id).base_value * random.uniform(0.8, 1.5)
        economy.trade(seller, buyer, mat_id, count, int(price))
    
    # 生成报告
    report = economy.generate_report()
    economy.print_report(report)
