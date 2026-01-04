#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊所运营模拟主脚本

运行牙科诊所模拟系统，协调各模块工作：
1. 调用核心模拟逻辑生成模拟数据
2. 保存模拟结果到CSV文件
3. 调用分析模块进行结果分析
4. 生成可视化图表和HTML报告

系统架构：
- run_simulation.py: 主入口，协调各模块
- src/simulation.py: 核心模拟逻辑
- src/patient.py: 患者类定义
- src/visualization.py: 可视化和报告生成
- analyze_results.py: 独立的结果分析脚本
"""

import pandas as pd
import os
from src.simulation import run_simulation


def main():
    """主函数
    
    运行牙科诊所模拟系统，包括：
    1. 启动模拟过程
    2. 保存模拟结果到CSV文件
    3. 分析模拟结果
    4. 生成可视化图表和报告
    """
    print("=== 牙科诊所运营模拟系统 ===")
    print("正在运行模拟...")
    
    # 运行模拟
    pivot_table, daily_stats, age_dist = run_simulation(
        years=5, 
        daily_new_leads_base=3,
        num_pediatric_doctors=1,
        num_ortho_doctors=0,
        num_nurses=4
    )
    
    # 保存结果到CSV文件
    print("保存模拟结果...")
    # 使用脚本所在目录作为基础路径，确保结果文件写入到正确位置
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    result_dir = os.path.join(script_dir, "result")
    # 确保result目录存在
    os.makedirs(result_dir, exist_ok=True)
    pivot_table.to_csv(f"{result_dir}/纯新患者模拟_pivot.csv", encoding="gbk")
    daily_stats.to_csv(f"{result_dir}/纯新患者模拟_daily.csv", encoding="gbk", index=False)
    
    print("模拟完成！")
    print(f"- 生成患者记录: {len(pivot_table)} 人")
    print(f"- 模拟天数: {len(daily_stats)} 天")
    print(f"- 最终会员数: {daily_stats['TotalMembers'].iloc[-1]} 人")
    print(f"- 最终现金余额: {daily_stats['Cash'].iloc[-1]:.2f} 元")
    
    # 分析结果
    print("\n=== 结果分析 ===")
    try:
        from src.visualization import analyze_simulation_results, plot_key_metrics, generate_summary_report
        
        # 分析结果
        analysis_results = analyze_simulation_results(daily_stats)
        
        # 生成图表和报告
        try:
            print("生成可视化图表...")
            plot_results = plot_key_metrics(daily_stats, analysis_results)
            
            print("生成分析报告...")
            generate_summary_report(plot_results)
            
            print("\n=== 模拟结束 ===")
            print("结果文件:")
            print("- result/纯新患者模拟_pivot.csv: 患者行为透视表")
            print("- result/纯新患者模拟_daily.csv: 每日统计数据")
            print("- result/纯新患者模拟_with_age.csv: 包含年龄信息的原始记录")
            print("- result/plots/: 可视化图表目录")
            print("- result/reports/simulation_report.html: 分析报告")
            print("\n请打开 result/reports/simulation_report.html 查看详细分析报告。")
        except ImportError:
            print("警告: 无法生成可视化图表 (缺少matplotlib库)")
            print("\n=== 模拟结束 ===")
            print("结果文件:")
            print("- result/纯新患者模拟_pivot.csv: 患者行为透视表")
            print("- result/纯新患者模拟_daily.csv: 每日统计数据")
            print("- result/纯新患者模拟_with_age.csv: 包含年龄信息的原始记录")
    except ImportError:
        print("警告: 无法进行结果分析 (缺少相关库)")
        print("\n=== 模拟结束 ===")
        print("结果文件:")
        print("- result/纯新患者模拟_pivot.csv: 患者行为透视表")
        print("- result/纯新患者模拟_daily.csv: 每日统计数据")
        print("- result/纯新患者模拟_with_age.csv: 包含年龄信息的原始记录")


if __name__ == "__main__":
    main()
