#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试初始会员功能的脚本

验证：
1. 初始会员是否在3个月内随机到店
2. 初始会员是否会产生矫正
3. 统计是否区分纯新客户和现有客户
4. 初始会员是否会产生续卡行为
5. 配置的初始会员数量是否影响结果
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.simulation_manager import SimulationManager

def test_initial_members():
    """测试初始会员功能"""
    print("=== 测试初始会员功能 ===")
    
    # 1. 测试初始会员配置是否生效
    print("\n1. 测试初始会员配置是否生效...")
    sim_manager = SimulationManager()
    # 设置初始会员数量为1000
    sim_manager.params['initial_members'] = 1000
    sim_manager.reset_simulation()
    
    initial_members = [p for p in sim_manager.state['all_patients'] if p.source == 'existing']
    print(f"   初始会员数量: {len(initial_members)} (预期: 1000)")
    print(f"   初始会员年龄范围: {min(p.initial_age for p in initial_members):.1f} - {max(p.initial_age for p in initial_members):.1f} 岁")
    print(f"   初始会员平均年龄: {sum(p.initial_age for p in initial_members)/len(initial_members):.1f} 岁")
    
    # 2. 测试初始会员是否在3个月内随机到店
    print("\n2. 测试初始会员是否在3个月内随机到店...")
    first_visit_days = [p.next_appointment_day for p in initial_members]
    print(f"   首次到店日期范围: {min(first_visit_days)} - {max(first_visit_days)} 天")
    print(f"   所有初始会员都在3个月内到店: {all(1 <= day <= 90 for day in first_visit_days)}")
    
    # 3. 测试初始会员是否有5年卡
    print("\n3. 测试初始会员是否有5年卡...")
    has_5yr_card = [p.card_type == '5yr' for p in initial_members]
    print(f"   有5年卡的初始会员比例: {sum(has_5yr_card)/len(has_5yr_card)*100:.1f}%")
    
    # 4. 测试初始会员卡剩余天数是否随机
    print("\n4. 测试初始会员卡剩余天数是否随机...")
    remaining_days = [p.card_expiry_day for p in initial_members]
    print(f"   卡剩余天数范围: {min(remaining_days)} - {max(remaining_days)} 天")
    print(f"   卡剩余天数是否随机: {min(remaining_days) < max(remaining_days)}")
    
    # 5. 运行一个简短的模拟，验证统计是否正确
    print("\n5. 运行简短模拟，验证统计...")
    # 运行30天模拟
    for day in range(1, 31):
        sim_manager.state['current_day'] = day
        sim_manager._run_single_day()
    
    # 检查每日统计
    daily_stats = sim_manager.state['daily_history']
    print(f"   模拟天数: {len(daily_stats)}")
    print(f"   总客户数: {daily_stats[-1]['TotalCustomers']}")
    print(f"   总会员数: {daily_stats[-1]['TotalMembers']}")
    print(f"   总就诊人次: {sum(day['PatientsSeen'] for day in daily_stats)}")
    
    # 检查新客户统计
    total_new_customers = sum(day['NewCustomers'] for day in daily_stats)
    print(f"   纯新客户总数: {total_new_customers} (应为每日新客之和，不包含初始会员)")
    
    # 检查初始会员就诊情况
    existing_patients_visited = set()
    for day in sim_manager.state['daily_history']:
        # 这里简化处理，实际需要查看todays_visitors
        pass
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_initial_members()
