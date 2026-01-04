#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊所模拟结果可视化与分析

用于生成直观的图表，帮助用户观察关键指标的变化趋势
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os

# 设置中文显示 - 确保所有图表元素（包括图例）都能正确显示中文
# 全面的中文显示设置，针对不同环境
plt.rcParams['font.family'] = ['SimHei', 'WenQuanYi Micro Hei', 'Heiti TC', 'Microsoft YaHei']
plt.rcParams['font.sans-serif'] = ['SimHei', 'WenQuanYi Micro Hei', 'Heiti TC', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
plt.rcParams['legend.fontsize'] = 10  # 设置图例字体大小
plt.rcParams['axes.titlesize'] = 14  # 设置标题字体大小
plt.rcParams['axes.labelsize'] = 12  # 设置坐标轴标签字体大小
plt.rcParams['xtick.labelsize'] = 10  # 设置x轴刻度字体大小
plt.rcParams['ytick.labelsize'] = 10  # 设置y轴刻度字体大小

# 确保Seaborn也使用正确的字体
sns.set(font=plt.rcParams['font.family'])


def analyze_simulation_results(daily_stats):
    """
    分析模拟结果，生成关键指标
    
    参数：
    - daily_stats: 每日统计数据，DataFrame格式
    
    返回：
    - analysis_results: 分析结果字典
    """
    # 计算月度数据
    monthly_stats = daily_stats.groupby('Month').agg({
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
    
    # 计算盈亏平衡点
    monthly_stats['Profit'] = monthly_stats['RevenueTotal'] - monthly_stats['Costs']
    
    # 查找现金流平衡月份
    cash_flow_balance_month = None
    for idx, row in monthly_stats.iterrows():
        if row['CashFlowToday'] >= 0:
            cash_flow_balance_month = row['Month']
            break
    
    # 查找盈亏平衡月份
    profit_balance_month = None
    for idx, row in monthly_stats.iterrows():
        if row['Profit'] >= 0:
            profit_balance_month = row['Month']
            break
    
    # 查找需要加人的关键节点
    staff_increase_points = []
    prev_pediatric = monthly_stats.loc[0, 'CurrentPediatricDoctors']
    prev_ortho = monthly_stats.loc[0, 'CurrentOrthoDoctors']
    prev_nurses = monthly_stats.loc[0, 'CurrentNurses']
    
    for idx, row in monthly_stats.iterrows():
        month = row['Month']
        if row['CurrentPediatricDoctors'] > prev_pediatric:
            staff_increase_points.append({
                'Month': month,
                'Change': f'Pediatric Doctors: {prev_pediatric} → {row["CurrentPediatricDoctors"]}'
            })
        if row['CurrentOrthoDoctors'] > prev_ortho:
            staff_increase_points.append({
                'Month': month,
                'Change': f'Orthodontic Doctors: {prev_ortho} → {row["CurrentOrthoDoctors"]}'
            })
        if row['CurrentNurses'] > prev_nurses:
            staff_increase_points.append({
                'Month': month,
                'Change': f'Nurses: {prev_nurses} → {row["CurrentNurses"]}'
            })
        
        prev_pediatric = row['CurrentPediatricDoctors']
        prev_ortho = row['CurrentOrthoDoctors']
        prev_nurses = row['CurrentNurses']
    
    # 计算利用率
    monthly_stats['PatientPerDoctor'] = monthly_stats['PatientsSeen'] / \
        (monthly_stats['CurrentPediatricDoctors'] + monthly_stats['CurrentOrthoDoctors'])
    
    analysis_results = {
        'monthly_stats': monthly_stats,
        'cash_flow_balance_month': cash_flow_balance_month,
        'profit_balance_month': profit_balance_month,
        'staff_increase_points': staff_increase_points
    }
    
    return analysis_results


def plot_key_metrics(daily_stats, analysis_results, output_dir=None):
    """
    绘制关键指标图表
    
    参数：
    - daily_stats: 每日统计数据，DataFrame格式
    - analysis_results: 分析结果字典
    - output_dir: 图表输出目录，默认使用脚本所在目录的result/plots
    """
    # 如果未提供输出目录，使用脚本所在目录的result/plots
    if output_dir is None:
        import os
        script_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.join(os.path.dirname(script_dir), "result", "plots")
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    monthly_stats = analysis_results['monthly_stats']
    cash_flow_balance_month = analysis_results['cash_flow_balance_month']
    profit_balance_month = analysis_results['profit_balance_month']
    staff_increase_points = analysis_results['staff_increase_points']
    
    # 设置图表风格
    plt.style.use('seaborn-v0_8-whitegrid')
    sns.set_palette('Set2')
    
    # 1. Monthly Revenue and Costs
    plt.figure(figsize=(12, 6))
    plt.plot(monthly_stats['Month'], monthly_stats['RevenueTotal'], label='Monthly Revenue', marker='o')
    plt.plot(monthly_stats['Month'], monthly_stats['Costs'], label='Monthly Costs', marker='o')
    plt.axhline(y=0, color='r', linestyle='--', alpha=0.7)
    
    # Mark profit balance point
    if profit_balance_month:
        plt.axvline(x=profit_balance_month, color='g', linestyle='--', alpha=0.7, label=f'Profit Balance (Month {profit_balance_month})')
    
    for point in staff_increase_points:
        plt.axvline(x=point['Month'], color='orange', linestyle=':', alpha=0.5, label=point['Change'])
    
    plt.title('Monthly Revenue and Costs Trend')
    plt.xlabel('Month')
    plt.ylabel('Amount (CNY)')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'monthly_revenue_cost.png'), dpi=300)
    plt.close()
    
    # 2. Monthly Cash Flow
    plt.figure(figsize=(12, 6))
    plt.plot(monthly_stats['Month'], monthly_stats['CashFlowToday'], label='Monthly Cash Flow', marker='o', color='blue')
    plt.axhline(y=0, color='r', linestyle='--', alpha=0.7)
    
    # Mark cash flow balance point
    if cash_flow_balance_month:
        plt.axvline(x=cash_flow_balance_month, color='g', linestyle='--', alpha=0.7, label=f'Cash Flow Balance (Month {cash_flow_balance_month})')
    
    for point in staff_increase_points:
        plt.axvline(x=point['Month'], color='orange', linestyle=':', alpha=0.5, label=point['Change'])
    
    plt.title('Monthly Cash Flow Trend')
    plt.xlabel('Month')
    plt.ylabel('Cash Flow (CNY)')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'monthly_cash_flow.png'), dpi=300)
    plt.close()
    
    # 3. Members and Patients Seen
    plt.figure(figsize=(12, 6))
    ax1 = plt.gca()
    ax2 = ax1.twinx()
    
    ax1.plot(monthly_stats['Month'], monthly_stats['TotalMembers'], label='Total Members', marker='o', color='blue')
    ax2.plot(monthly_stats['Month'], monthly_stats['PatientsSeen'], label='Monthly Patients Seen', marker='o', color='green')
    
    for point in staff_increase_points:
        ax1.axvline(x=point['Month'], color='orange', linestyle=':', alpha=0.5, label=point['Change'])
    
    ax1.set_title('Members and Monthly Patients Seen Trend')
    ax1.set_xlabel('Month')
    ax1.set_ylabel('Total Members', color='blue')
    ax2.set_ylabel('Monthly Patients Seen', color='green')
    ax1.legend(loc='upper left')
    ax2.legend(loc='upper right')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'members_patients.png'), dpi=300)
    plt.close()
    
    # 4. Staffing Levels
    plt.figure(figsize=(12, 6))
    plt.plot(monthly_stats['Month'], monthly_stats['CurrentPediatricDoctors'], label='Pediatric Doctors', marker='o')
    plt.plot(monthly_stats['Month'], monthly_stats['CurrentOrthoDoctors'], label='Orthodontic Doctors', marker='o')
    plt.plot(monthly_stats['Month'], monthly_stats['CurrentNurses'], label='Nurses', marker='o')
    
    plt.title('Staffing Levels Trend')
    plt.xlabel('Month')
    plt.ylabel('Number of Staff')
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'staffing_levels.png'), dpi=300)
    plt.close()
    
    # 5. Patients Per Doctor
    plt.figure(figsize=(12, 6))
    plt.plot(monthly_stats['Month'], monthly_stats['PatientPerDoctor'], label='Patients Per Doctor', marker='o', color='purple')
    
    for point in staff_increase_points:
        plt.axvline(x=point['Month'], color='orange', linestyle=':', alpha=0.5, label=point['Change'])
    
    plt.title('Monthly Patients Per Doctor Trend')
    plt.xlabel('Month')
    plt.ylabel('Patients Per Doctor (persons/month)')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'patient_per_doctor.png'), dpi=300)
    plt.close()
    
    print("Charts generated successfully!")
    print(f"Cash flow balance month: {cash_flow_balance_month} months")
    print(f"Profit balance month: {profit_balance_month} months")
    print("Staff increase points:")
    for point in staff_increase_points:
        print(f"  Month {point['Month']}: {point['Change']}")
    
    return {
        'cash_flow_balance_month': cash_flow_balance_month,
        'profit_balance_month': profit_balance_month,
        'staff_increase_points': staff_increase_points,
        'monthly_stats': monthly_stats
    }


def generate_summary_report(analysis_results, output_dir=None):
    """
    生成分析报告
    
    参数：
    - analysis_results: 分析结果字典
    - output_dir: 报告输出目录，默认使用脚本所在目录的result/reports
    """
    # 如果未提供输出目录，使用脚本所在目录的result/reports
    if output_dir is None:
        import os
        script_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.join(os.path.dirname(script_dir), "result", "reports")
    os.makedirs(output_dir, exist_ok=True)
    
    cash_flow_balance_month = analysis_results['cash_flow_balance_month']
    profit_balance_month = analysis_results['profit_balance_month']
    staff_increase_points = analysis_results['staff_increase_points']
    monthly_stats = analysis_results['monthly_stats']
    
    # 生成HTML报告
    report_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Clinic Simulation Results Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1 {{ color: #2c3e50; }}
            h2 {{ color: #3498db; }}
            .summary {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            .highlight {{ color: #e74c3c; font-weight: bold; }}
            table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            .chart {{ margin: 20px 0; text-align: center; }}
            img {{ max-width: 100%; height: auto; border: 1px solid #ddd; padding: 5px; }}
        </style>
    </head>
    <body>
        <h1>Clinic Simulation Results Report</h1>
        
        <div class="summary">
            <h2>Key Metrics Summary</h2>
            <p>Cash Flow Balance: <span class="highlight">Month {cash_flow_balance_month}</span></p>
            <p>Profit Balance: <span class="highlight">Month {profit_balance_month}</span></p>
        </div>
        
        <h2>Staffing Increase Plan</h2>
        <ul>
    """
    
    for point in staff_increase_points:
        report_html += f"<li>第 {point['Month']} 个月: {point['Change']}</li>"
    
    report_html += f"""
        </ul>
        
        <h2>Monthly Key Data</h2>
        <table>
            <tr>
                <th>Month</th>
                <th>New Customers</th>
                <th>Total Members</th>
                <th>Patients Seen</th>
                <th>Monthly Revenue</th>
                <th>Monthly Costs</th>
                <th>Monthly Profit</th>
                <th>Monthly Cash Flow</th>
                <th>Pediatric Doctors</th>
                <th>Orthodontic Doctors</th>
                <th>Nurses</th>
            </tr>
    """
    
    for idx, row in monthly_stats.iterrows():
        report_html += f"""
            <tr>
                <td>{int(row['Month'])}</td>
                <td>{int(row['NewCustomers'])}</td>
                <td>{int(row['TotalMembers'])}</td>
                <td>{int(row['PatientsSeen'])}</td>
                <td>{int(row['RevenueTotal'])}</td>
                <td>{int(row['Costs'])}</td>
                <td>{int(row['Profit'])}</td>
                <td>{int(row['CashFlowToday'])}</td>
                <td>{int(row['CurrentPediatricDoctors'])}</td>
                <td>{int(row['CurrentOrthoDoctors'])}</td>
                <td>{int(row['CurrentNurses'])}</td>
            </tr>
        """
    
    report_html += f"""
        </table>
        
        <h2>Trend Charts</h2>
        
        <div class="chart">
            <h3>Monthly Revenue and Costs</h3>
            <img src="../plots/monthly_revenue_cost.png" alt="Monthly Revenue and Costs">
        </div>
        
        <div class="chart">
            <h3>Monthly Cash Flow</h3>
            <img src="../plots/monthly_cash_flow.png" alt="Monthly Cash Flow">
        </div>
        
        <div class="chart">
            <h3>Members and Patients Seen</h3>
            <img src="../plots/members_patients.png" alt="Members and Patients Seen">
        </div>
        
        <div class="chart">
            <h3>Staffing Levels</h3>
            <img src="../plots/staffing_levels.png" alt="Staffing Levels">
        </div>
        
        <div class="chart">
            <h3>Patients Per Doctor</h3>
            <img src="../plots/patient_per_doctor.png" alt="Patients Per Doctor">
        </div>
        
        <footer>
            <p>Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </footer>
    </body>
    </html>
    """
    
    with open(os.path.join(output_dir, 'simulation_report.html'), 'w', encoding='utf-8') as f:
        f.write(report_html)
    
    print(f"分析报告已生成: {os.path.join(output_dir, 'simulation_report.html')}")
    
    return report_html
