#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的模拟结果分析脚本

无需matplotlib，直接分析CSV文件，找出关键指标
"""

import pandas as pd
import os


def analyze_results():
    """分析模拟结果"""
    # 读取模拟结果，使用脚本所在目录的result文件夹
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    result_dir = os.path.join(script_dir, "result")
    daily_file = os.path.join(result_dir, "纯新患者模拟_daily.csv")
    
    if not os.path.exists(daily_file):
        print(f"错误：找不到文件 {daily_file}")
        return
    
    print("=== 牙科诊所模拟结果分析 ===")
    print(f"读取文件：{daily_file}")
    
    # 读取数据
    df = pd.read_csv(daily_file, encoding="gbk")
    
    # 计算月度数据
    monthly_df = df.groupby('Month').agg({
        'NewCustomers': 'sum',
        'TotalMembers': 'max',
        'PatientsSeen': 'sum',
        'RevenueTotal': 'sum',
        'CashFlowToday': 'sum',
        'Costs': 'sum',
        'CurrentPediatricDoctors': 'max',
        'CurrentOrthoDoctors': 'max',
        'CurrentNurses': 'max'
    }).reset_index()
    
    # 计算月度利润
    monthly_df['Profit'] = monthly_df['RevenueTotal'] - monthly_df['Costs']
    
    print(f"\n模拟总天数：{len(df)} 天")
    print(f"最终会员数：{df['TotalMembers'].iloc[-1]} 人")
    print(f"最终现金余额：{df['Cash'].iloc[-1]:.2f} 元")
    
    # 查找现金流平衡点
    cash_flow_balance = None
    for idx, row in monthly_df.iterrows():
        if row['CashFlowToday'] >= 0:
            cash_flow_balance = row['Month']
            break
    
    if cash_flow_balance:
        print(f"\n现金流平衡月份：第 {cash_flow_balance} 个月")
    else:
        print(f"\n在模拟期间未达到现金流平衡")
    
    # 查找盈亏平衡点
    profit_balance = None
    for idx, row in monthly_df.iterrows():
        if row['Profit'] >= 0:
            profit_balance = row['Month']
            break
    
    if profit_balance:
        print(f"盈亏平衡月份：第 {profit_balance} 个月")
    else:
        print(f"在模拟期间未达到盈亏平衡")
    
    # 分析人员增加节点
    print(f"\n人员增加计划：")
    
    prev_ped = monthly_df.loc[0, 'CurrentPediatricDoctors']
    prev_ortho = monthly_df.loc[0, 'CurrentOrthoDoctors']
    prev_nurse = monthly_df.loc[0, 'CurrentNurses']
    
    for idx, row in monthly_df.iterrows():
        month = row['Month']
        
        if row['CurrentPediatricDoctors'] > prev_ped:
            print(f"  第 {month} 个月：儿牙医生增加到 {row['CurrentPediatricDoctors']} 人")
            prev_ped = row['CurrentPediatricDoctors']
        
        if row['CurrentOrthoDoctors'] > prev_ortho:
            print(f"  第 {month} 个月：矫正医生增加到 {row['CurrentOrthoDoctors']} 人")
            prev_ortho = row['CurrentOrthoDoctors']
        
        if row['CurrentNurses'] > prev_nurse:
            print(f"  第 {month} 个月：护士增加到 {row['CurrentNurses']} 人")
            prev_nurse = row['CurrentNurses']
    
    # 分析关键指标趋势
    print(f"\n关键指标趋势：")
    print(f"  - 日均新客户：{df['NewCustomers'].mean():.1f} 人")
    print(f"  - 日均就诊量：{df['PatientsSeen'].mean():.1f} 人")
    print(f"  - 日均营收：{df['RevenueTotal'].mean():.1f} 元")
    print(f"  - 日均现金流：{df['CashFlowToday'].mean():.1f} 元")
    
    print(f"\n月度数据概览：")
    print(f"  - 月度平均新客户：{monthly_df['NewCustomers'].mean():.1f} 人")
    print(f"  - 月度平均营收：{monthly_df['RevenueTotal'].mean():.1f} 元")
    print(f"  - 月度平均利润：{monthly_df['Profit'].mean():.1f} 元")
    
    # 保存月度数据到CSV
    monthly_df.to_csv(os.path.join(result_dir, "纯新患者模拟_monthly_summary.csv"), encoding="gbk", index=False)
    print(f"\n月度汇总数据已保存到：{os.path.join(result_dir, '纯新患者模拟_monthly_summary.csv')}")
    
    print(f"\n=== 分析完成 ===")


if __name__ == "__main__":
    analyze_results()
