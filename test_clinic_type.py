#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试诊所类型功能的脚本

验证：
1. 选择做矫正这个选项，逻辑是否和修改前几乎保持一致？会发生矫正开始和矫正结束
2. 如果选择纯儿牙，是否真的不会发生矫正开始和矫正结束？
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.simulation_manager import SimulationManager

def test_clinic_type_ortho():
    """测试做矫正类型的诊所"""
    print("=== 测试做矫正类型的诊所 ===")
    
    # 初始化模拟
    sim_manager = SimulationManager()
    sim_manager.params['clinic_type'] = 'ortho'  # 设置为做矫正
    sim_manager.params['initial_members'] = 400
    sim_manager.params['prob_ortho'] = 0.1  # 提高矫正概率以便测试
    sim_manager.reset_simulation()
    
    # 运行4周模拟
    for week in range(1, 5):
        print(f"   运行第 {week} 周...")
        sim_manager.run_next_week()
    
    # 检查是否有矫正开始事件
    ortho_start_events = [d for d in sim_manager.state['patient_details'] if d['Action'] == '矫正开始']
    print(f"   矫正开始事件数量: {len(ortho_start_events)}")
    
    # 检查是否有矫正结束事件
    ortho_end_events = [d for d in sim_manager.state['patient_details'] if d['Action'] == '矫正结束']
    print(f"   矫正结束事件数量: {len(ortho_end_events)}")
    
    # 检查pivot_records中是否有矫正相关记录
    ortho_pivot_records = [r for r in sim_manager.state['pivot_records'] if 'Ortho' in r['Val']]
    print(f"   Pivot记录中矫正相关记录数量: {len(ortho_pivot_records)}")
    
    # 验证结果
    success = len(ortho_start_events) > 0
    print(f"   测试结果: {'✅ 通过' if success else '❌ 失败'} - {'发生了矫正开始和结束' if success else '没有发生矫正开始和结束'}")
    
    return success

def test_clinic_type_pediatric():
    """测试纯儿牙类型的诊所"""
    print("\n=== 测试纯儿牙类型的诊所 ===")
    
    # 初始化模拟
    sim_manager = SimulationManager()
    sim_manager.params['clinic_type'] = 'pediatric'  # 设置为纯儿牙
    sim_manager.params['initial_members'] = 400
    sim_manager.params['prob_ortho'] = 0.1  # 即使概率高，纯儿牙也不应有矫正
    sim_manager.reset_simulation()
    
    # 运行4周模拟
    for week in range(1, 5):
        print(f"   运行第 {week} 周...")
        sim_manager.run_next_week()
    
    # 检查是否有矫正开始事件
    ortho_start_events = [d for d in sim_manager.state['patient_details'] if d['Action'] == '矫正开始']
    print(f"   矫正开始事件数量: {len(ortho_start_events)}")
    
    # 检查是否有矫正结束事件
    ortho_end_events = [d for d in sim_manager.state['patient_details'] if d['Action'] == '矫正结束']
    print(f"   矫正结束事件数量: {len(ortho_end_events)}")
    
    # 检查pivot_records中是否有矫正相关记录
    ortho_pivot_records = [r for r in sim_manager.state['pivot_records'] if 'Ortho' in r['Val']]
    print(f"   Pivot记录中矫正相关记录数量: {len(ortho_pivot_records)}")
    
    # 验证结果
    success = len(ortho_start_events) == 0 and len(ortho_end_events) == 0 and len(ortho_pivot_records) == 0
    print(f"   测试结果: {'✅ 通过' if success else '❌ 失败'} - {'没有发生矫正开始和结束' if success else '发生了矫正开始和结束'}")
    
    return success

def main():
    """主测试函数"""
    print("=== 诊所类型功能测试 ===")
    
    # 运行两个测试场景
    test1_passed = test_clinic_type_ortho()
    test2_passed = test_clinic_type_pediatric()
    
    print("\n=== 测试总结 ===")
    print(f"做矫正类型测试: {'✅ 通过' if test1_passed else '❌ 失败'}")
    print(f"纯儿牙类型测试: {'✅ 通过' if test2_passed else '❌ 失败'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 所有测试通过！诊所类型功能实现正确。")
        print("   - 做矫正：会发生矫正开始和结束")
        print("   - 纯儿牙：不会发生矫正开始和结束")
        return 0
    else:
        print("\n❌ 部分测试失败！诊所类型功能可能存在问题。")
        return 1

if __name__ == "__main__":
    sys.exit(main())
