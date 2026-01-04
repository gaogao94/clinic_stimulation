#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细测试初始会员功能的脚本

验证：
1. 初始会员是否会产生矫正
2. 初始会员在1年内是否有部分人产生了续卡行为
3. 配置的初始会员数量是否影响结果
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.simulation_manager import SimulationManager

def test_detailed_initial_members():
    """详细测试初始会员功能"""
    print("=== 详细测试初始会员功能 ===")
    
    # 测试1：初始会员是否会产生矫正
    print("\n1. 测试初始会员是否会产生矫正...")
    sim_manager = SimulationManager()
    sim_manager.params['initial_members'] = 500
    sim_manager.params['num_ortho_doctors'] = 1  # 确保有矫正医生
    sim_manager.reset_simulation()
    
    # 运行180天模拟，给足够时间让初始会员到店并产生矫正
    for day in range(1, 181):
        sim_manager.state['current_day'] = day
        sim_manager._run_single_day()
    
    # 检查矫正情况
    all_patients = sim_manager.state['all_patients']
    existing_patients = [p for p in all_patients if p.source == 'existing']
    ortho_patients = [p for p in existing_patients if p.has_ortho or p.ortho_completed]
    
    print(f"   初始会员总数: {len(existing_patients)}")
    print(f"   产生矫正的初始会员数: {len(ortho_patients)}")
    print(f"   初始会员矫正比例: {len(ortho_patients)/len(existing_patients)*100:.1f}%")
    
    if ortho_patients:
        print(f"   矫正年龄范围: {min(p.ortho_age for p in ortho_patients):.1f} - {max(p.ortho_age for p in ortho_patients):.1f} 岁")
    
    # 测试2：初始会员在1年内是否有部分人产生了续卡行为
    print("\n2. 测试初始会员在1年内是否有部分人产生了续卡行为...")
    # 重置模拟，设置初始会员卡剩余天数较短，以便在1年内到期
    sim_manager2 = SimulationManager()
    sim_manager2.params['initial_members'] = 500
    sim_manager2.reset_simulation()
    
    # 手动设置初始会员的卡剩余天数为100-200天，以便在1年内到期
    for p in sim_manager2.state['all_patients']:
        if p.source == 'existing':
            p.card_expiry_day = 150  # 设置为150天后到期
    
    # 运行365天模拟
    for day in range(1, 366):
        sim_manager2.state['current_day'] = day
        sim_manager2._run_single_day()
    
    # 检查续卡情况
    existing_patients2 = [p for p in sim_manager2.state['all_patients'] if p.source == 'existing']
    renewed_patients = []
    for p in existing_patients2:
        # 续卡后，card_expiry_day会大于初始的150天
        if p.card_expiry_day > 150:
            renewed_patients.append(p)
    
    print(f"   初始会员总数: {len(existing_patients2)}")
    print(f"   产生续卡行为的初始会员数: {len(renewed_patients)}")
    print(f"   初始会员续卡比例: {len(renewed_patients)/len(existing_patients2)*100:.1f}%")
    
    # 测试3：配置的初始会员数量是否影响结果
    print("\n3. 测试配置的初始会员数量是否影响结果...")
    # 使用不同的初始会员数量运行模拟，检查结果是否不同
    test_cases = [0, 100, 1000, 10000]  # 0个、100个、1000个、10000个初始会员
    results = []
    
    for initial_members in test_cases:
        sim = SimulationManager()
        sim.params['initial_members'] = initial_members
        sim.reset_simulation()
        
        # 运行30天模拟
        for day in range(1, 31):
            sim.state['current_day'] = day
            sim._run_single_day()
        
        total_customers = sim.state['daily_history'][-1]['TotalCustomers']
        total_members = sim.state['daily_history'][-1]['TotalMembers']
        patients_seen = sum(day['PatientsSeen'] for day in sim.state['daily_history'])
        
        results.append({
            'initial_members': initial_members,
            'total_customers': total_customers,
            'total_members': total_members,
            'patients_seen': patients_seen
        })
    
    # 输出结果
    print("   不同初始会员数量的模拟结果:")
    print("   初始会员数 | 总客户数 | 总会员数 | 就诊人次")
    print("   -----------|---------|---------|--------")
    for result in results:
        print(f"   {result['initial_members']:11d} | {result['total_customers']:7d} | {result['total_members']:7d} | {result['patients_seen']:8d}")
    
    # 检查结果是否随初始会员数量变化
    all_same = all(result['total_customers'] == results[0]['total_customers'] for result in results)
    print(f"   结果随初始会员数量变化: {not all_same}")
    print(f"   初始会员数量影响结果: {not all_same}")
    
    print("\n=== 详细测试完成 ===")

if __name__ == "__main__":
    test_detailed_initial_members()
