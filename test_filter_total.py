#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试过滤功能和合计功能的脚本

验证：
1. 模拟3个月的数据
2. 过滤第2月，查看合计是否会根据过滤条件变化而变化
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.simulation_manager import SimulationManager

def test_filter_total():
    """测试过滤功能和合计功能"""
    print("=== 测试过滤功能和合计功能 ===")
    
    # 1. 初始化模拟
    print("\n1. 初始化模拟...")
    sim_manager = SimulationManager()
    # 设置初始会员数量为400
    sim_manager.params['initial_members'] = 400
    sim_manager.reset_simulation()
    
    # 2. 运行12周模拟（约3个月）
    print("\n2. 运行12周模拟...")
    for week in range(1, 13):
        print(f"   运行第 {week} 周...")
        sim_manager.run_next_week()
    
    print(f"   模拟天数: {sim_manager.state['current_day']} 天")
    print(f"   模拟周数: {sim_manager.state['current_week']} 周")
    print(f"   模拟月数: {sim_manager.state['current_month']} 月")
    
    # 3. 获取每日数据
    print("\n3. 获取每日数据...")
    daily_data = sim_manager.get_results(type="daily")
    print(f"   每日数据记录数: {len(daily_data)}")
    
    # 4. 按第2月过滤数据
    print("\n4. 按第2月过滤数据...")
    # 计算第2月的天数范围（假设每月31天）
    month_2_start = 32  # 第2个月从第32天开始
    month_2_end = 62    # 第2个月到第62天结束
    
    # 过滤第2月的数据
    month_2_data = [d for d in daily_data if month_2_start <= d['Day'] <= month_2_end]
    print(f"   第2月数据记录数: {len(month_2_data)}")
    
    # 5. 计算全部数据的合计
    print("\n5. 计算全部数据的合计...")
    sum_fields = ['NewCustomers', 'PatientsSeen', 'RevenueTotal', 'Costs', 'CashFlowToday', 
                'RevenueCard', 'RevenueTreatment', 'RevenueOrtho', 
                'CashFlowCard', 'CashFlowTreatment', 'CashFlowOrtho', 
                'DoctorSalary', 'NurseSalary']
    
    # 计算全部数据的合计
    all_sums = {}
    for field in sum_fields:
        all_sums[field] = sum(d.get(field, 0) for d in daily_data)
    
    # 6. 计算第2月数据的合计
    print("\n6. 计算第2月数据的合计...")
    month_2_sums = {}
    for field in sum_fields:
        month_2_sums[field] = sum(d.get(field, 0) for d in month_2_data)
    
    # 7. 比较合计结果
    print("\n7. 比较合计结果...")
    print("   字段名 | 全部数据合计 | 第2月数据合计 | 是否不同")
    print("   --------|-------------|---------------|--------")
    all_different = True
    for field in sum_fields:
        all_total = all_sums[field]
        month_2_total = month_2_sums[field]
        different = all_total != month_2_total
        if not different:
            all_different = False
        print(f"   {field:8} | {all_total:11.2f} | {month_2_total:13.2f} | {'是' if different else '否'}")
    
    # 8. 输出测试结果
    print("\n8. 测试结果...")
    if all_different:
        print("✅ 所有字段的合计都根据过滤条件变化而变化，测试通过！")
    else:
        print("❌ 部分字段的合计没有根据过滤条件变化而变化，测试失败！")
    
    # 9. 保存数据用于前端测试
    print("\n9. 保存数据用于前端测试...")
    import json
    with open('test_data.json', 'w', encoding='utf-8') as f:
        json.dump({
            'all_daily_data': daily_data,
            'month_2_data': month_2_data,
            'all_sums': all_sums,
            'month_2_sums': month_2_sums
        }, f, ensure_ascii=False, indent=2)
    print("   测试数据已保存到 test_data.json")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_filter_total()
