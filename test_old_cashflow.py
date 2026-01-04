#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试老店现金流是否正常
"""

from src.simulation_manager import SimulationManager

def test_old_cashflow():
    """测试老店现金流是否正常"""
    print("=== 测试老店现金流 ===")
    
    # 创建模拟管理器
    sim = SimulationManager()
    
    # 确保初始会员设置正确
    assert sim.params['initial_members'] == 400, f"初始会员数应为400，实际为{sim.params['initial_members']}"
    
    print(f"初始会员数: {sim.params['initial_members']}")
    print(f"初始患者数: {len(sim.state['all_patients'])}")
    
    # 运行4周模拟
    for week in range(4):
        result = sim.run_next_week()
        print(f"运行第{week+1}周: {result['message']}")
    
    # 获取患者详细记录
    patient_details = sim.get_patient_details()
    print(f"\n模拟结束，总记录数: {len(patient_details)}")
    
    # 计算老店和新店的现金流
    old_cashflow = 0
    new_cashflow = 0
    
    for record in patient_details:
        cashflow = record.get('CashFlow', 0)
        source = record.get('Source', 'unknown')
        
        if source == 'existing':
            old_cashflow += cashflow
        elif source == 'native':
            new_cashflow += cashflow
    
    print(f"\n老店现金流: {old_cashflow:.2f}元")
    print(f"新店现金流: {new_cashflow:.2f}元")
    
    # 验证老店现金流不为0
    assert old_cashflow > 0, f"老店现金流应为正数，实际为{old_cashflow:.2f}元"
    print(f"\n✅ 测试通过：老店现金流正常，为{old_cashflow:.2f}元")
    
    return True

if __name__ == "__main__":
    test_old_cashflow()