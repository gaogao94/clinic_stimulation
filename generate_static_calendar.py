#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成静态日历文件，保存2026-2036年的真实日历数据
"""

import json
from datetime import datetime, timedelta
import os

def generate_calendar():
    """生成2026-2036年的真实日历数据"""
    calendar = []
    start_date = datetime(2026, 1, 1)
    end_date = datetime(2036, 1, 1)
    
    current_date = start_date
    day_count = 1
    
    while current_date < end_date:
        # 计算年、月、日
        year = current_date.year
        month = current_date.month
        day = current_date.day
        
        # 计算星期几（0-6，周一为0，周日为6）
        weekday = current_date.weekday()
        weekday_name = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][weekday]
        
        # 计算周数（ISO周数）
        week_num = current_date.isocalendar()[1]
        
        # 添加到日历列表，转换为JSON可序列化格式
        calendar.append({
            'simulation_day': day_count,  # 模拟天数（从1开始）
            'date': current_date.strftime('%Y-%m-%d'),  # 日期字符串
            'year': year,
            'month': month,
            'day': day,
            'weekday': weekday,
            'weekday_name': weekday_name,
            'week_num': week_num
        })
        
        # 日期加1
        current_date += timedelta(days=1)
        day_count += 1
    
    return calendar

def main():
    """生成静态日历文件"""
    print("开始生成静态日历文件...")
    
    # 生成日历数据
    calendar_data = generate_calendar()
    
    # 确定保存路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    calendar_file = os.path.join(script_dir, 'data', 'calendar.json')
    
    # 确保data目录存在
    os.makedirs(os.path.dirname(calendar_file), exist_ok=True)
    
    # 保存为JSON文件
    with open(calendar_file, 'w', encoding='utf-8') as f:
        json.dump(calendar_data, f, ensure_ascii=False, indent=2)
    
    print(f"静态日历文件生成完成！")
    print(f"保存路径：{calendar_file}")
    print(f"日历天数：{len(calendar_data)}")
    print(f"日期范围：从{calendar_data[0]['date']}到{calendar_data[-1]['date']}")

if __name__ == "__main__":
    main()
