#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模拟管理器类

负责管理模拟状态、参数和执行逻辑，支持按周步进模拟
"""

import random
import numpy as np
import pandas as pd
import os
import patient
from patient import Patient
from datetime import datetime, timedelta


class SimulationManager:
    """
    模拟管理器类，负责管理模拟状态、参数和执行逻辑
    """
    
    # 类属性：静态日历数据，从文件加载一次
    _calendar = None
    
    def __init__(self):
        """初始化模拟管理器"""
        # 模拟参数默认值
        self.default_params = {
            'years': 10,  # 模拟时长（年）
            'invest_decoration': 280000,  # 装修投资（元）
            'invest_hardware': 300000,  # 设备投资（元）
            'pre_opening_investment': 0,  # 开业前期投入：0元（一次性投入）
            'num_chairs': 4,  # 诊疗椅数量（把）
            'num_pediatric_doctors': 0,  # 儿牙医生数量（人）
            'num_ortho_doctors': 1,  # 矫正医生数量（人）
            'num_nurses': 4,  # 护士数量（人）
            'daily_new_leads_base': 3,  # 每日新客流入（人）
            'initial_members': 400,  # 初始会员数量，默认400人
            'prob_card_1yr': 0.2,  # 新客办1年卡概率
            'prob_card_5yr': 0.4,  # 新客办5年卡概率
            'price_card_1yr': 1000,  # 1年卡价格（元）
            'price_card_5yr': 5000,  # 5年卡价格（元）
            'prob_treatment': 0.10,  # 治疗概率
            'price_treatment': 800,  # 治疗价格（元）
            'prob_ortho': 0.01,  # 矫正概率
            'price_ortho': 25000,  # 矫正价格（元）
            'follow_up_cycle': 90,  # 复诊周期（天）
            'prob_follow_up': 0.95,  # 老客户复诊率
            'prob_renew_1yr': 0.15,  # 老客户续1年卡概率
            'prob_renew_5yr': 0.3,  # 老客户续5年卡概率
            'rent_per_sqm_per_day': 6,  # 租金：元每平米每天（按照建筑面积计算）
            'building_area': 150,  # 建筑面积：143平米（不可调整）
            'occupancy_rate': 0.7,  # 得房率：70%（不可调整，仅展示使用面积）
            'monthly_utilities': 2000,  # 每月水电费：2000元（固定）
            'monthly_marketing': 10000,  # 每月市场费用：10000元（固定）
            'monthly_other_costs': 0,  # 每月其他成本：0元（固定）
            'doctor_base_salary': 15000,  # 医生底薪（元）
            'doctor_guaranteed_salary': 15000,  # 医生保底工资（元）
            'doctor_commission_rate': 0.15,  # 医生提成比例
            'nurse_base_salary': 7000,  # 护士底薪（元）
            'nurse_guaranteed_salary': 7000,  # 护士保底工资（元）
            'nurse_commission_rate': 0.03,  # 护士提成比例
            'ops_base_salary': 5000,  # 运营底薪（元）
            'ops_guaranteed_salary': 10000,  # 运营保底工资（元）
            'ops_commission_rate': 0.05,  # 运营提成比例
            'pediatric_material_ratio': 0.05,  # 儿牙耗材比例
            'ortho_material_ratio': 0.30,  # 矫正耗材比例
            'card_revenue_recognition_ratio': 0.2,  # 会员卡办卡当日确认营收比例，默认20%
            'doctor_threshold': 800,  # 增加医生阈值：平均单医生会员总数>800时增加儿牙医生
            'clinic_type': 'ortho'  # 诊所类型：'ortho'做矫正，'pediatric'纯儿牙
        }
        
        self.params = self.default_params.copy()  # 初始化params为默认值
        
        # 从静态文件加载日历数据，只加载一次
        if SimulationManager._calendar is None:
            SimulationManager._calendar = self._load_calendar()
        self.calendar = SimulationManager._calendar
        
        self.reset_simulation()  # 初始化模拟状态
    
    def _load_calendar(self):
        """从静态JSON文件加载日历数据"""
        import json
        import os
        
        # 确定日历文件路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)  # 回到项目根目录
        calendar_file = os.path.join(project_root, 'data', 'calendar.json')
        
        # 加载JSON文件
        with open(calendar_file, 'r', encoding='utf-8') as f:
            calendar_data = json.load(f)
        
        # 将date字段从字符串转换为datetime对象
        for item in calendar_data:
            item['date'] = datetime.strptime(item['date'], '%Y-%m-%d')
        
        return calendar_data
    
    def get_date_info(self, simulation_day):
        """根据模拟天数获取真实日期信息"""
        if simulation_day > len(self.calendar):
            # 如果超过生成的日历范围，计算扩展日期
            extra_days = simulation_day - len(self.calendar)
            start_date = self.calendar[-1]['date'] + timedelta(days=1)
            extra_date = start_date + timedelta(days=extra_days - 1)
            
            year = extra_date.year
            month = extra_date.month
            day = extra_date.day
            weekday = extra_date.weekday()
            weekday_name = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][weekday]
            week_num = extra_date.isocalendar()[1]
            
            return {
                'simulation_day': simulation_day,
                'date': extra_date,
                'year': year,
                'month': month,
                'day': day,
                'weekday': weekday,
                'weekday_name': weekday_name,
                'week_num': week_num
            }
        
        return self.calendar[simulation_day - 1]
    
    def reset_simulation(self):
        """重置模拟状态"""
        # 重置模拟状态，但保留当前参数
        self.state = {
            'current_day': 0,  # 当前模拟天数
            'current_week': 0,  # 当前模拟周数
            'current_month': 0,  # 当前模拟月数
            'all_patients': [],  # 所有患者列表
            'pivot_records': [],  # 患者行为透视表数据
            'patient_details': [],  # 患者详细记录，包括每个患者的行为和财务数据
            'daily_history': [],  # 每日统计数据
            'weekly_history': [],  # 每周统计数据
            'monthly_history': [],  # 每月统计数据
            'patient_counter': 0,  # 患者ID计数器
            # 包含开业前期投入的初始现金
            'current_cash': -(self.params['invest_decoration'] + self.params['invest_hardware'] + self.params['pre_opening_investment']),
            'current_pediatric_doctors': self.params['num_pediatric_doctors'],  # 当前儿牙医生数
            'current_ortho_doctors': self.params['num_ortho_doctors'],  # 当前矫正医生数
            'current_nurses': self.params['num_nurses'],  # 当前护士数
            'current_ops': 1,  # 当前运营人数，默认为1人
            'card_1yr_total': 0,  # 1年卡总收入
            'card_5yr_total': 0,  # 5年卡总收入
            'monthly_card_revenue': 0,  # 月度卡类分摊收入
            'ortho_started_revenue': 0,  # 已开始矫正的收入
            'ortho_completed_revenue': 0,  # 已完成矫正的收入
            'monthly_cash_flow': 0,  # 月度现金流
            'monthly_revenue': 0,  # 月度营收
            'monthly_pediatric_revenue': 0,  # 月度儿牙营收
            'monthly_ortho_revenue': 0,  # 月度矫正营收
            'monthly_card_sales': 0,  # 月度卡类销售
            'contract_liability': 0,  # 合同负债总额
            'ortho_contract_liability': 0,  # 矫正合同负债
            'card_contract_liability': 0,  # 卡类合同负债
        }
        
        # 初始化现有会员
        initial_members_count = self.params['initial_members']
        if initial_members_count > 0:
            for i in range(initial_members_count):
                self.state['patient_counter'] += 1  # 增加患者ID计数器
                age = max(0.1, np.random.normal(9, 2))  # 生成平均9岁，标准差2岁的年龄
                
                # 创建现有会员，join_day设为0表示初始就存在
                p = Patient(self.state['patient_counter'], 0, age, source="existing")
                
                # 所有现有会员都有5年卡，剩余到期天数随机
                total_5yr_days = 365 * 5
                remaining_days = random.randint(1, total_5yr_days)
                p.card_type = '5yr'  # 设置为5年卡
                p.card_expiry_day = remaining_days  # 设置剩余到期天数
                p.remaining_prevention = -1  # 5年卡无限次免费预防
                
                # 安排在3个月内（90天）随机到店
                first_visit_day = random.randint(1, 90)
                p.next_appointment_day = first_visit_day  # 设置首次到店日期
                
                self.state['all_patients'].append(p)  # 添加到患者列表
        
        # 年龄分布数据，用于生成新患者年龄
        self.age_distribution = {
            1: 1000, 2: 2700, 3: 2600, 4: 1800, 5: 1800, 6: 1700,
            7: 1200, 8: 1100, 9: 800, 10: 600, 11: 600, 12: 300,
            13: 200, 14: 100
        }
        self.total_patients = sum(self.age_distribution.values())  # 总患者数
        self.age_list = list(self.age_distribution.keys())  # 年龄列表
        # 计算各年龄概率
        self.age_probs = [count / self.total_patients for count in self.age_distribution.values()]
        
        return {'status': 'success', 'message': 'Simulation reset successfully'}
    
    def get_params(self):
        """获取当前模拟参数"""
        return self.params
    
    def set_params(self, params):
        """设置模拟参数并重置模拟"""
        # 首先更新当前参数
        for key, value in params.items():
            if key in self.params:
                self.params[key] = value
        
        # 然后重置模拟状态，使用更新后的参数
        self.reset_simulation()
        
        return {'status': 'success', 'message': 'Parameters updated successfully'}
    
    def get_state(self):
        """获取当前模拟状态"""
        return {
            'current_day': self.state['current_day'],
            'current_week': self.state['current_week'],
            'total_days': self.params['years'] * 365,
            'current_pediatric_doctors': self.state['current_pediatric_doctors'],
            'current_ortho_doctors': self.state['current_ortho_doctors'],
            'current_nurses': self.state['current_nurses'],
            'current_cash': self.state['current_cash']
        }
    
    def run_next_week(self):
        """运行下一周（7天）的模拟"""
        # 检查模拟是否已完成
        if self.state['current_day'] >= self.params['years'] * 365:
            return {'status': 'error', 'message': 'Simulation has completed'}
        
        # 运行7天模拟
        for _ in range(7):
            if self.state['current_day'] >= self.params['years'] * 365:
                break
            self._run_single_day()  # 运行单日模拟
        
        self.state['current_week'] += 1  # 更新周数
        self._calculate_weekly_stats()  # 计算每周统计数据
        
        return {
            'status': 'success',
            'message': f'Week {self.state["current_week"]} simulated',
            'current_week': self.state['current_week'],
            'current_day': self.state['current_day']
        }
    
    def _run_single_day(self):
        """运行单日模拟"""
        day = self.state['current_day'] + 1  # 当前模拟天数
        self.state['current_day'] = day  # 更新当前天数
        
        # 今日财务数据初始化
        cash_today = 0  # 今日现金流
        revenue_today = 0  # 今日营收
        
        # 分类收入和现金流初始化
        revenue_treatment = 0  # 治疗营收
        revenue_ortho = 0  # 矫正营收
        revenue_card_immediate = 0  # 卡类收入的当日确认部分
        revenue_card_amortized = 0  # 卡类收入的分摊部分
        
        cash_new_card = 0  # 新办卡现金流
        cash_renew_card = 0  # 续卡现金流
        cash_treatment = 0  # 治疗现金流
        cash_ortho = 0  # 矫正现金流
        
        todays_visitors = []  # 今日到店患者列表
        new_customers = 0  # 今日新客户数
        
        card_sales_today = 0  # 今日新办卡和续卡的总金额
        
        # 患者分类处理列表
        pediatric_patients = []  # 儿牙患者列表
        ortho_patients = []  # 矫正患者列表
        
        # 计算当日卡类分摊收入（权责发生制）
        daily_card_revenue = 0  # 当日卡类分摊收入
        if day % 30 == 1 or day == 1:  # 每月第一天或模拟第一天
            card_recognition_ratio = self.params['card_revenue_recognition_ratio']  # 办卡当日确认营收比例
            
            # 计算需要摊销的卡类收入：总卡类收入 - 办卡当日已确认的部分
            card_1yr_amortize = self.state['card_1yr_total'] * (1 - card_recognition_ratio)
            card_5yr_amortize = self.state['card_5yr_total'] * (1 - card_recognition_ratio)
            
            # 1年卡分摊到12个月，5年卡分摊到60个月
            self.state['monthly_card_revenue'] = (card_1yr_amortize / 12) + (card_5yr_amortize / 60)
        daily_card_revenue = self.state['monthly_card_revenue'] / 30  # 日均卡类分摊收入
        
        revenue_card_amortized = daily_card_revenue  # 记录卡类分摊收入
        
        # 更新合同负债：卡类收入的未确认部分
        card_recognition_ratio = self.params['card_revenue_recognition_ratio']  # 办卡当日确认营收比例
        months_passed = day // 30  # 已过月数
        
        # 已确认的卡类收入 = 办卡当日确认的部分 + 已摊销的部分
        recognized_immediate = (self.state['card_1yr_total'] + self.state['card_5yr_total']) * card_recognition_ratio
        recognized_amortized = (self.state['card_1yr_total'] * (1 - card_recognition_ratio) / 12 * min(months_passed, 12)) + \
                               (self.state['card_5yr_total'] * (1 - card_recognition_ratio) / 60 * min(months_passed, 60))
        recognized_card_revenue = recognized_immediate + recognized_amortized
        
        # 更新卡类合同负债
        self.state['card_contract_liability'] = (self.state['card_1yr_total'] + self.state['card_5yr_total']) - recognized_card_revenue
        
        # 1. 老患者复诊处理（仅处理到店患者的复诊）
        # 注：原续卡逻辑已删除，新续卡逻辑移至患者就诊处理中
        for p in self.state['all_patients']:  # 遍历所有患者
            if not p.is_active: continue  # 跳过非活跃患者
            
            # 复诊判定：如果今天有常规预约或矫正复诊
            is_ortho_appointment = False  # 标记是否为矫正复诊
            # 只有当诊所类型是ortho时才处理矫正复诊
            if p.next_appointment_day == day or (self.params['clinic_type'] == 'ortho' and p.next_ortho_appointment == day):
                # 处理矫正复诊
                if self.params['clinic_type'] == 'ortho' and p.next_ortho_appointment == day:
                    is_ortho_appointment = True  # 标记为矫正复诊
                    
                    # 检查是否是最后一次矫正复诊（矫正完成）
                    # 假设总共24次复诊，每次间隔45天，总时长约3年
                    total_ortho_days = 45 * 24
                    if day - p.ortho_start_day >= total_ortho_days and not getattr(p, 'ortho_completed', False):
                        # 矫正完成，不产生耗材费用，营收记入剩余的45%
                        if hasattr(p, 'ortho_revenue_remaining') and p.ortho_revenue_remaining > 0:
                            # 记录矫正完成的营收
                            revenue_ortho += p.ortho_revenue_remaining
                            
                            week_num = (day - 1) // 7 + 1  # 计算当前周数
                            
                            # 获取日期信息，包括星期几
                            date_info = self.get_date_info(day)
                            formatted_date = date_info['date'].strftime('%Y-%m-%d')
                            
                            # 记录患者详细信息
                            self.state['patient_details'].append({
                                'PatientID': p.id,  # 患者ID
                                'Day': day,  # 模拟天数
                                'Date': formatted_date,  # 实际日期
                                'Week': week_num,  # 周数
                                'Weekday': date_info['weekday_name'],  # 星期几
                                'Age': p.initial_age + (day - p.join_day) // 365,  # 当前年龄
                                'Action': '矫正结束',  # 行为类型
                                'CardType': p.card_type,  # 卡类型
                                'Amount': p.ortho_total_cost,  # 总费用
                                'RevenueType': '矫正收入',  # 收入类型
                                'CashFlow': 0,  # 矫正结束不产生现金流
                                'Costs': 0,  # 矫正结束不产生耗材费用
                                'Profit': p.ortho_revenue_remaining,  # 利润为剩余营收
                                'Description': f'患者矫正完成，记入剩余营收{p.ortho_revenue_remaining:.2f}元（45%），无额外耗材费用'
                            })
                            
                            # 记录患者行为透视表数据
                            self.state['pivot_records'].append({
                                'PatientID': f'P{p.id:03}', 
                                'Day': f'D{day:03}', 
                                'Val': f'Ortho End(rev:+{p.ortho_revenue_remaining:.2f})', 
                                'Age': p.initial_age + (day - p.join_day) // 365, 
                                'Source': p.source
                            })
                            
                            # 标记矫正已完成
                            p.ortho_completed = True  # 标记矫正已完成
                            p.ortho_end_day = day  # 记录矫正结束日期
                            p.ortho_revenue_remaining = 0  # 剩余营收清零
                        
                        p.next_ortho_appointment = None  # 矫正完成后不再有矫正复诊
                    else:
                        p.next_ortho_appointment = day + 45  # 不是最后一次复诊，继续预约下一次
                    
                    todays_visitors.append(p)  # 添加到今日到店患者列表
                
                # 处理常规复诊
                if p.next_appointment_day == day:
                    if random.random() < self.params['prob_follow_up']:  # 判定是否复诊
                        todays_visitors.append(p)  # 添加到今日到店患者列表
                    else:
                        p.next_appointment_day = day + 30  # 未赴约，推迟30天再联系
        
        # 2. 获取新初诊客户
        growth_factor = min(1.0, 0.4 + (day / 180) * 0.6)  # 增长因子，随时间递增，上限为1.0
        # 生成每日新客数量，基于高斯分布
        num_new_leads = max(0, int(random.gauss(self.params['daily_new_leads_base'], 1) * growth_factor))
        new_customers = 0  # 初始化为0，实际新客户数
        
        # 处理每个新客户
        for _ in range(num_new_leads):
            self.state['patient_counter'] += 1  # 增加患者ID计数器
            # 根据年龄分布随机选择初始年龄
            initial_age = random.choices(self.age_list, weights=self.age_probs, k=1)[0]
            new_p = Patient(self.state['patient_counter'], day, initial_age)  # 创建新患者对象
            
            roll = random.random()  # 生成随机数用于判定办卡类型
            action_desc = "Initial visit"  # 患者行为描述
            card_rev = 0  # 卡类收入
            card_type = None  # 卡类型
            
            # 判定是否办1年卡
            if roll < self.params['prob_card_1yr']:
                card_rev = new_p.buy_card('1yr', day, self.params['price_card_1yr'])  # 患者购买1年卡
                action_desc += f"+Buy 1yr card(+{card_rev})"  # 更新行为描述
                cash_today += card_rev  # 更新今日现金流
                cash_new_card += card_rev  # 更新新办卡现金流
                self.state['card_1yr_total'] += card_rev  # 更新1年卡总收入
                card_sales_today += card_rev  # 更新今日卡类销售总额
                card_type = '1年卡'  # 设置卡类型
            
            # 判定是否办5年卡
            elif roll < (self.params['prob_card_1yr'] + self.params['prob_card_5yr']):
                card_rev = new_p.buy_card('5yr', day, self.params['price_card_5yr'])  # 患者购买5年卡
                action_desc += f"+Buy 5yr card(+{card_rev})"  # 更新行为描述
                cash_today += card_rev  # 更新今日现金流
                cash_new_card += card_rev  # 更新新办卡现金流
                self.state['card_5yr_total'] += card_rev  # 更新5年卡总收入
                card_sales_today += card_rev  # 更新今日卡类销售总额
                card_type = '5年卡'  # 设置卡类型
            
            week_num = (day - 1) // 7 + 1  # 计算当前周数
            
            # 获取日期信息，包括星期几
            date_info = self.get_date_info(day)
            formatted_date = date_info['date'].strftime('%Y-%m-%d')
            
            # 记录患者详细信息
            self.state['patient_details'].append({
                'PatientID': new_p.id,  # 患者ID
                'Day': day,  # 模拟天数
                'Date': formatted_date,  # 实际日期
                'Week': week_num,  # 周数
                'Weekday': date_info['weekday_name'],  # 星期几
                'Age': initial_age,  # 初始年龄
                'Action': '初诊',  # 行为类型
                'CardType': card_type,  # 卡类型
                'Amount': card_rev,  # 金额
                'RevenueType': '卡类收入' if card_rev > 0 else '初诊',  # 收入类型
                'CashFlow': card_rev,  # 现金流
                'Costs': 0,  # 初诊成本已包含在固定成本中
                'Profit': card_rev,  # 利润
                'Description': f'患者初诊，{f"购买{card_type}，" if card_type else ""}金额{card_rev}元',  # 描述
                'Source': new_p.source  # 患者来源
            })
            
            # 记录患者行为透视表数据
            self.state['pivot_records'].append({
                'PatientID': f'P{new_p.id:03}', 
                'Day': f'D{day:03}', 
                'Val': action_desc, 
                'Age': initial_age, 
                'Source': new_p.source
            })
            
            # 设置新患者的初始复诊日期
            follow_up_cycle = self.params['follow_up_cycle']  # 复诊周期
            new_p.next_appointment_day = day + follow_up_cycle  # 设置下次复诊日期
            
            self.state['all_patients'].append(new_p)  # 添加到所有患者列表
            todays_visitors.append(new_p)  # 添加到今日到店患者列表
            
            # 只有native来源的患者才计入新客户
            if new_p.source == "native":
                new_customers += 1  # 实际新客户数递增
        
        # 3. 患者就诊处理
        for p in todays_visitors:  # 遍历今日到店患者
            current_age = p.initial_age + (day - p.join_day) // 365  # 计算当前年龄
            
            week_num = (day - 1) // 7 + 1  # 计算当前周数
            
            # 获取日期信息，包括星期几
            date_info = self.get_date_info(day)
            formatted_date = date_info['date'].strftime('%Y-%m-%d')
            
            # 记录患者就诊信息
            if p.next_appointment_day == day or p.next_ortho_appointment == day:
                # 这是一个复诊患者
                self.state['patient_details'].append({
                    'PatientID': p.id,  # 患者ID
                    'Day': day,  # 模拟天数
                    'Date': formatted_date,  # 实际日期
                    'Week': week_num,  # 周数
                    'Weekday': date_info['weekday_name'],  # 星期几
                    'Age': current_age,  # 当前年龄
                    'Action': '复诊',  # 行为类型
                    'CardType': p.card_type,  # 卡类型
                    'Amount': 0,  # 金额
                    'RevenueType': '复诊',  # 收入类型
                    'CashFlow': 0,  # 现金流
                    'Costs': 0,  # 成本
                    'Profit': 0,  # 利润
                    'Description': f'患者复诊',  # 描述
                    'Source': p.source  # 患者来源
                })
                
                # 记录患者行为透视表数据
                self.state['pivot_records'].append({
                    'PatientID': f'P{p.id:03}', 
                    'Day': f'D{day:03}', 
                    'Val': f'Follow-up', 
                    'Age': current_age, 
                    'Source': p.source
                })
            
            # 随机判定是否进行治疗
            if random.random() < self.params['prob_treatment']:
                discount = 0.65 if p.card_expiry_day > 0 else 1.0  # 检查是否有治疗折扣（会员卡65折）
                treatment_cost = int(self.params['price_treatment'] * discount)  # 计算治疗费用
                cash_today += treatment_cost  # 更新今日现金流
                cash_treatment += treatment_cost  # 更新治疗现金流
                revenue_treatment += treatment_cost  # 更新治疗营收
                
                material_cost = treatment_cost * self.params['pediatric_material_ratio']  # 计算耗材成本
                profit = treatment_cost - material_cost  # 计算利润
                
                # 计算当前周数
                week_num = (day - 1) // 7 + 1
                
                # 获取日期信息，包括星期几
                date_info = self.get_date_info(day)
                formatted_date = date_info['date'].strftime('%Y-%m-%d')
                
                # 记录患者详细信息
                self.state['patient_details'].append({
                    'PatientID': p.id,  # 患者ID
                    'Day': day,  # 模拟天数
                    'Date': formatted_date,  # 实际日期
                    'Week': week_num,  # 周数
                    'Weekday': date_info['weekday_name'],  # 星期几
                    'Age': current_age,  # 当前年龄
                    'Action': '治疗',  # 行为类型
                    'CardType': p.card_type,  # 卡类型
                    'Amount': treatment_cost,  # 金额
                    'RevenueType': '治疗收入',  # 收入类型
                    'CashFlow': treatment_cost,  # 现金流
                    'Costs': material_cost,  # 成本
                    'Profit': profit,  # 利润
                    'Description': f'患者接受基础治疗，收入{treatment_cost}元，耗材成本{material_cost:.2f}元，利润{profit:.2f}元',  # 描述
                    'Source': p.source  # 患者来源
                })
                
                # 记录患者行为透视表数据
                self.state['pivot_records'].append({
                    'PatientID': f'P{p.id:03}', 
                    'Day': f'D{day:03}', 
                    'Val': f'Treatment(+{treatment_cost})', 
                    'Age': current_age, 
                    'Source': p.source
                })
            
            # 续卡判定：只有当天到店的患者，且卡有效期在正负365天内才会判定续卡
            if p.card_expiry_day > 0:  # 有有效的会员卡
                # 计算卡到期日与当前日的差值
                expiry_diff = p.card_expiry_day - day
                # 如果到期日与就诊日相差正负365天内
                if abs(expiry_diff) < 365:
                    current_age = p.initial_age + (day - p.join_day) // 365  # 计算当前年龄
                    roll = random.random()  # 生成随机数用于判定续卡类型
                    
                    week_num = (day - 1) // 7 + 1  # 计算当前周数
                    
                    # 获取日期信息，包括星期几
                    date_info = self.get_date_info(day)
                    formatted_date = date_info['date'].strftime('%Y-%m-%d')
                    
                    # 判定续1年卡
                    if roll < self.params['prob_renew_1yr']:
                        amt = p.buy_card('1yr', day, self.params['price_card_1yr'])  # 患者购买1年卡
                        cash_today += amt  # 更新今日现金流
                        cash_renew_card += amt  # 更新续卡现金流
                        self.state['card_1yr_total'] += amt  # 更新1年卡总收入
                        card_sales_today += amt  # 更新今日卡类销售总额
                        
                        # 记录患者详细信息
                        self.state['patient_details'].append({
                            'PatientID': p.id,  # 患者ID
                            'Day': day,  # 模拟天数
                            'Date': formatted_date,  # 实际日期
                            'Week': week_num,  # 周数
                            'Weekday': date_info['weekday_name'],  # 星期几
                            'Age': current_age,  # 当前年龄
                            'Action': '续卡',  # 行为类型
                            'CardType': '1年卡',  # 卡类型
                            'Amount': amt,  # 金额
                            'RevenueType': '卡类收入',  # 收入类型
                            'CashFlow': amt,  # 现金流
                            'Costs': 0,  # 续卡无直接成本
                            'Profit': amt,  # 利润
                            'Description': f'患者续1年卡，金额{amt}元',  # 描述
                            'Source': p.source  # 患者来源
                        })
                        
                        # 记录患者行为透视表数据
                        self.state['pivot_records'].append({
                            'PatientID': f'P{p.id:03}', 
                            'Day': f'D{day:03}', 
                            'Val': f'Renew 1yr card(+{amt})', 
                            'Age': current_age, 
                            'Source': p.source
                        })
                    
                    # 判定续5年卡
                    elif roll < (self.params['prob_renew_1yr'] + self.params['prob_renew_5yr']):
                        amt = p.buy_card('5yr', day, self.params['price_card_5yr'])  # 患者购买5年卡
                        cash_today += amt  # 更新今日现金流
                        cash_renew_card += amt  # 更新续卡现金流
                        self.state['card_5yr_total'] += amt  # 更新5年卡总收入
                        card_sales_today += amt  # 更新今日卡类销售总额
                        
                        # 记录患者详细信息
                        self.state['patient_details'].append({
                            'PatientID': p.id,  # 患者ID
                            'Day': day,  # 模拟天数
                            'Date': formatted_date,  # 实际日期
                            'Week': week_num,  # 周数
                            'Weekday': date_info['weekday_name'],  # 星期几
                            'Age': current_age,  # 当前年龄
                            'Action': '续卡',  # 行为类型
                            'CardType': '5年卡',  # 卡类型
                            'Amount': amt,  # 金额
                            'RevenueType': '卡类收入',  # 收入类型
                            'CashFlow': amt,  # 现金流
                            'Costs': 0,  # 续卡无直接成本
                            'Profit': amt,  # 利润
                            'Description': f'患者续5年卡，金额{amt}元',  # 描述
                            'Source': p.source  # 患者来源
                        })
                        
                        # 记录患者行为透视表数据
                        self.state['pivot_records'].append({
                            'PatientID': f'P{p.id:03}', 
                            'Day': f'D{day:03}', 
                            'Val': f'Renew 5yr card(+{amt})', 
                            'Age': current_age, 
                            'Source': p.source
                        })
            
            # 随机判定是否进行矫正 - 根据年龄调整概率
            # 只有当诊所类型是ortho时才允许矫正
            if self.params['clinic_type'] == 'ortho':
                current_age = p.initial_age + (day - p.join_day) // 365  # 计算当前年龄
                base_ortho_prob = self.params['prob_ortho']  # 基础矫正概率
                
                # 根据年龄调整矫正概率
                age_ortho_prob = base_ortho_prob
                if current_age < 6:
                    age_ortho_prob = base_ortho_prob * 0.1  # 6岁以下概率低
                elif 6 <= current_age <= 10:
                    age_ortho_prob = base_ortho_prob * 2.0  # 6-10岁概率中等
                elif 11 <= current_age <= 14:
                    age_ortho_prob = base_ortho_prob * 5.0  # 11-14岁概率高
                
                # 判定是否进行矫正
                if random.random() < age_ortho_prob:
                    ortho_cost = self.params['price_ortho']  # 基础矫正价格
                    discount = 0.65 if p.card_expiry_day > 0 else 1.0  # 检查是否有治疗折扣（会员卡65折）
                    ortho_cost = int(ortho_cost * discount)  # 计算实际矫正费用
                    
                    ortho_cash = ortho_cost  # 开始矫正时收取全额
                    cash_today += ortho_cash  # 更新今日现金流
                    cash_ortho += ortho_cash  # 记录矫正现金流
                    
                    revenue_ortho += ortho_cost * 0.55  # 开始时记入营收55%
                    
                    material_cost = ortho_cost * self.params['ortho_material_ratio']  # 计算耗材成本
                    profit = ortho_cost * 0.55 - material_cost  # 计算利润
                    
                    week_num = (day - 1) // 7 + 1  # 计算当前周数
                    
                    # 获取日期信息，包括星期几
                    date_info = self.get_date_info(day)
                    formatted_date = date_info['date'].strftime('%Y-%m-%d')
                    
                    # 记录患者详细信息
                    self.state['patient_details'].append({
                        'PatientID': p.id,  # 患者ID
                        'Day': day,  # 模拟天数
                        'Date': formatted_date,  # 实际日期
                        'Week': week_num,  # 周数
                        'Weekday': date_info['weekday_name'],  # 星期几
                        'Age': current_age,  # 当前年龄
                        'Action': '矫正开始',  # 行为类型
                        'CardType': p.card_type,  # 卡类型
                        'Amount': ortho_cost,  # 金额
                        'RevenueType': '矫正收入',  # 收入类型
                        'CashFlow': ortho_cost,  # 现金流是全额
                        'Costs': material_cost,  # 成本
                        'Profit': profit,  # 利润
                        'Description': f'患者开始矫正，现金流{ortho_cost:.2f}元（总费用{ortho_cost}元），记入营收{ortho_cost * 0.55:.2f}元（55%），耗材成本{material_cost:.2f}元，利润{profit:.2f}元',  # 描述
                        'Source': p.source  # 患者来源
                    })
                    
                    # 记录患者行为透视表数据
                    self.state['pivot_records'].append({
                        'PatientID': f'P{p.id:03}', 
                        'Day': f'D{day:03}', 
                        'Val': f'Ortho Start(+{ortho_cost:.2f}, rev:{ortho_cost * 0.55:.2f})', 
                        'Age': current_age, 
                        'Source': p.source
                    })
                    
                    # 设置矫正相关属性
                    p.has_ortho = True  # 标记已进行矫正
                    p.ortho_start_day = day  # 记录矫正开始日期
                    p.ortho_age = current_age  # 记录矫正时年龄
                    p.next_ortho_appointment = day + 45  # 设置下次矫正复诊日期（每45天一次）
                    p.ortho_total_cost = ortho_cost  # 记录总矫正费用
                    p.ortho_revenue_remaining = ortho_cost * 0.45  # 剩余45%营收待确认
            
            # 设置下次常规复诊日期
            if p.next_appointment_day is None or p.next_appointment_day <= day:
                follow_up_cycle = self.params['follow_up_cycle']  # 获取复诊周期
                p.next_appointment_day = day + follow_up_cycle  # 设置下次复诊日期
        
        # 计算医生和护士工资
        doctor_salary_today = 0  # 今日医生工资
        nurse_salary_today = 0  # 今日护士工资
        ops_salary_today = 0  # 今日运营工资
        
        # 获取真实日期信息
        date_info = self.get_date_info(day)
        current_month = date_info['month']
        current_year = date_info['year']
        
        # 检查是否是当月最后一天
        next_day_info = self.get_date_info(day + 1)  # 获取次日信息
        is_last_day_of_month = (next_day_info['month'] != current_month) or day == int(self.params['years'] * 365)
        
        # 人员配置管理：增加医生的逻辑
        # 计算平均单医生会员总数，当>阈值时增加儿牙医生
        total_doctors = self.state['current_pediatric_doctors'] + self.state['current_ortho_doctors']
        if total_doctors > 0:
            current_members = len([p for p in self.state['all_patients'] if p.is_active and p.card_type is not None])
            avg_members_per_doctor = current_members / total_doctors
            doctor_threshold = self.params['doctor_threshold']
            # 如果平均单医生会员总数>阈值，增加1个儿牙医生（最多2个儿牙医生）
            if avg_members_per_doctor > doctor_threshold and self.state['current_pediatric_doctors'] < 2:
                self.state['current_pediatric_doctors'] += 1
        
        # 只在每月最后一天计算工资
        if is_last_day_of_month:
            # 计算医生薪酬：底薪+提成+保底
            # 提成基于月度总营收（权责发生制）
            
            # 计算月度总营收
            monthly_revenue = 0  # 月度总营收
            monthly_pediatric_revenue = 0  # 月度儿牙营收
            monthly_ortho_revenue = 0  # 月度矫正营收
            
            # 获取当月的日数据
            for d in reversed(self.state['daily_history']):
                if d['Month'] == current_month:
                    monthly_revenue += d['RevenueTotal']  # 累计总营收
                    monthly_pediatric_revenue += d.get('RevenueTreatment', 0)  # 累计儿牙营收
                    monthly_ortho_revenue += d.get('RevenueOrtho', 0)  # 累计矫正营收
            
            # 医生薪酬计算
            doctor_commission_rate = self.params['doctor_commission_rate']  # 医生提成比例
            doctor_base_salary = self.params['doctor_base_salary']  # 医生底薪
            doctor_guaranteed_salary = self.params['doctor_guaranteed_salary']  # 医生保底工资
            
            # 儿牙医生薪酬
            pediatric_doctor_commission = monthly_pediatric_revenue * doctor_commission_rate  # 儿牙医生提成
            pediatric_doctor_total = doctor_base_salary + pediatric_doctor_commission  # 儿牙医生总薪酬
            if day <= 365:  # 第一年有保底
                pediatric_doctor_total = max(pediatric_doctor_total, doctor_guaranteed_salary)  # 取提成和保底的最大值
            
            # 矫正医生薪酬
            ortho_doctor_commission = monthly_ortho_revenue * doctor_commission_rate  # 矫正医生提成
            ortho_doctor_total = doctor_base_salary + ortho_doctor_commission  # 矫正医生总薪酬
            if day <= 365:  # 第一年有保底
                ortho_doctor_total = max(ortho_doctor_total, doctor_guaranteed_salary)  # 取提成和保底的最大值
            
            # 使用当前人员数量计算工资
            doctor_salary_today = (self.state['current_pediatric_doctors'] * pediatric_doctor_total) + \
                                  (self.state['current_ortho_doctors'] * ortho_doctor_total)  # 总医生工资
            
            # 护士薪酬计算
            nurse_commission_rate = self.params['nurse_commission_rate']  # 护士提成比例
            nurse_base_salary = self.params['nurse_base_salary']  # 护士底薪
            nurse_guaranteed_salary = self.params['nurse_guaranteed_salary']  # 护士保底工资
            
            nurse_commission = monthly_revenue * nurse_commission_rate  # 护士提成
            nurse_individual = nurse_base_salary + nurse_commission  # 单个护士总薪酬
            nurse_individual = max(nurse_individual, nurse_guaranteed_salary)  # 取提成和保底的最大值
            nurse_salary_today = self.state['current_nurses'] * nurse_individual  # 总护士工资
            
            # 运营薪酬计算
            ops_commission_rate = self.params['ops_commission_rate']  # 运营提成比例
            ops_base_salary = self.params['ops_base_salary']  # 运营底薪
            ops_guaranteed_salary = self.params['ops_guaranteed_salary']  # 运营保底工资
            
            ops_commission = monthly_revenue * ops_commission_rate  # 运营提成
            ops_individual = ops_base_salary + ops_commission  # 运营人员总薪酬
            # 第一年有保底
            if day <= 365:
                ops_individual = max(ops_individual, ops_guaranteed_salary)  # 取提成和保底的最大值
            ops_salary_today = self.state['current_ops'] * ops_individual  # 总运营工资
        
        # 4. 计算当日成本
        # 房租和工资统一在每月最后一天结算
        costs_today = 0  # 今日总成本
        
        # 每日计算耗材成本（治疗和矫正的耗材成本已经在各自的处理逻辑中计算）
        # 固定成本（房租、工资）只在每月最后一天结算
        
        # 检查是否是当月最后一天或模拟最后一天
        if is_last_day_of_month:
            # 计算月固定成本
            # 房租计算：月房租 = 建筑面积 × 日租金 × 当月天数
            # 使用真实日历计算当月天数
            # 找到当月的第一天
            month_days = 0
            for date_info in self.calendar:
                if date_info['year'] == current_year and date_info['month'] == current_month:
                    month_days += 1
            
            # 如果在日历范围外，计算下一个月的第一天，然后减去当前月的第一天
            if month_days == 0:
                # 计算当前月的第一天
                current_month_start = datetime(current_year, current_month, 1)
                # 计算下一个月的第一天
                if current_month == 12:
                    next_month_start = datetime(current_year + 1, 1, 1)
                else:
                    next_month_start = datetime(current_year, current_month + 1, 1)
                # 计算当月天数
                month_days = (next_month_start - current_month_start).days
            
            monthly_rent = self.params['building_area'] * self.params['rent_per_sqm_per_day'] * month_days
            
            # 添加水电、市场费用和每月其他成本
            monthly_utilities = self.params['monthly_utilities']  # 每月水电费
            monthly_marketing = self.params['monthly_marketing']  # 每月市场费用
            monthly_other_costs = self.params['monthly_other_costs']  # 每月其他成本
            
            # 使用之前计算好的医生和护士工资
            # 这些工资已经包含了提成和保底
            costs_today = monthly_rent + monthly_utilities + monthly_marketing + monthly_other_costs + doctor_salary_today + nurse_salary_today
        
        # 计算当日确认的卡类收入：办卡当日确认的部分
        card_recognition_ratio = self.params['card_revenue_recognition_ratio']  # 办卡当日确认营收比例
        revenue_card_immediate = card_sales_today * card_recognition_ratio  # 当日确认的卡类收入
        
        # 计算总卡类营收（当日确认 + 分摊）
        revenue_card = revenue_card_immediate + revenue_card_amortized  # 总卡类营收
        
        # 计算总营收
        revenue_today = revenue_treatment + revenue_ortho + revenue_card  # 今日总营收
        
        # 计算卡类现金流
        cash_card = cash_new_card + cash_renew_card  # 卡类现金流
        
        # 计算利润
        # 1. 卡类利润：与营收记入方式一致，只要记入营收的，都直接记入利润
        profit_card = revenue_card  # 卡类营收全部计入利润
        
        # 2. 治疗利润：现金流入记入营收，扣减儿牙操作成本后记入利润
        treatment_material_cost = 0  # 当日治疗耗材成本
        # 从patient_details中查找今日的治疗记录，计算耗材成本
        for record in self.state['patient_details']:
            if record['Day'] == day and record['Action'] == '治疗':
                treatment_material_cost += record['Costs']
        profit_treatment = revenue_treatment - treatment_material_cost  # 治疗利润
        
        # 3. 矫正利润：矫正开始当次扣减全部成本，结束当次记入营收的全部记入利润
        ortho_material_cost = 0  # 当日矫正耗材成本
        # 从patient_details中查找今日的矫正记录，计算耗材成本
        for record in self.state['patient_details']:
            if record['Day'] == day and record['Action'] == '矫正开始':
                ortho_material_cost += record['Costs']
        profit_ortho = revenue_ortho - ortho_material_cost  # 矫正利润
        
        # 4. 总利润：卡类利润 + 治疗利润 + 矫正利润 - 当月变动成本
        # 当月变动成本包括：医生工资、护士工资、房租、水电、市场费用等
        # 这些成本已经包含在costs_today中，只在每月最后一天计算
        profit_today = profit_card + profit_treatment + profit_ortho - costs_today  # 今日总利润
        
        # 5. 更新现金和收入
        self.state['current_cash'] += cash_today - costs_today  # 更新当前现金余额
        
        # 6. 计算各项统计指标
        # 使用真实日历信息
        date_info = self.get_date_info(day)
        formatted_date = date_info['date'].strftime('%Y-%m-%d')  # 真实日期字符串
        
        total_customers = len(self.state['all_patients'])  # 总客户数：去重的唯一客户（所有历史患者）
        total_members = len([p for p in self.state['all_patients'] if p.is_active and p.card_type is not None])  # 最终会员数：只有买了会员卡的患者才算
        # 去重患者，避免同一患者多次到店被重复统计
        unique_patients = list(set(todays_visitors))
        patients_seen = len(unique_patients)  # 就诊人次：今日到店患者数（去重）
        
        # 记录每日统计数据
        self.state['daily_history'].append({
            'Day': day,  # 模拟天数
            'Date': formatted_date,  # 真实日期
            'Week': date_info['week_num'],  # 真实周数（ISO周数）
            'Month': date_info['month'],  # 真实月份
            'Year': date_info['year'],  # 真实年份
            'Weekday': date_info['weekday_name'],  # 星期几
            'NewCustomers': new_customers,  # 当日新客户数
            'PatientsSeen': patients_seen,  # 今日就诊人次
            'RevenueTotal': revenue_today,  # 今日总营收
            'Costs': costs_today,  # 今日总成本
            'Profit': profit_today,  # 今日利润
            'CashFlowToday': cash_today - costs_today,  # 今日现金流
            'Cash': self.state['current_cash'],  # 当前现金余额
            'TotalCustomers': total_customers,  # 累计总客户数（去重）
            'TotalMembers': total_members,  # 累计会员数（仅买了会员卡的）
            
            # 分类营收
            'RevenueCard': revenue_card,  # 卡类营收
            'RevenueTreatment': revenue_treatment,  # 治疗营收
            'RevenueOrtho': revenue_ortho,  # 矫正营收
            
            # 分类利润
            'ProfitCard': profit_card,  # 卡类利润
            'ProfitTreatment': profit_treatment,  # 治疗利润
            'ProfitOrtho': profit_ortho,  # 矫正利润
            
            # 分类现金流
            'CashFlowCard': cash_card,  # 卡类现金流
            'CashFlowTreatment': cash_treatment,  # 治疗现金流
            'CashFlowOrtho': cash_ortho,  # 矫正现金流
            
            # 人员工资
            'DoctorSalary': doctor_salary_today,  # 今日医生工资
            'NurseSalary': nurse_salary_today,  # 今日护士工资
            'OpsSalary': ops_salary_today,  # 今日运营工资
            
            # 保留原始数据但调整顺序，将不重要的字段放在后面
            'Card1YrTotal': self.state['card_1yr_total'],
            'Card5YrTotal': self.state['card_5yr_total'],
            'MonthlyCardRevenue': self.state['monthly_card_revenue'],
            'CardContractLiability': self.state['card_contract_liability'],
            'OrthoContractLiability': self.state['ortho_contract_liability'],
            'CurrentPediatricDoctors': self.state['current_pediatric_doctors'],
            'CurrentOrthoDoctors': self.state['current_ortho_doctors'],
            'CurrentNurses': self.state['current_nurses'],
            'CurrentOps': self.state['current_ops']
        })
        
        # 更新患者详细记录中的月份
        for record in self.state['patient_details']:
            if record['Day'] == day and 'Month' not in record:
                record['Month'] = current_month  # 添加月份字段
    
    def _calculate_weekly_stats(self):
        """计算每周统计数据"""
        # 简单的周统计，实际逻辑需扩展
        if len(self.state['daily_history']) < 7:
            return
        
        weekly_data = self.state['daily_history'][-7:]
        weekly_stats = {
            'Week': self.state['current_week'],
            'StartDay': weekly_data[0]['Day'],
            'EndDay': weekly_data[-1]['Day'],
            'StartDate': weekly_data[0]['Date'],  # 周起始日期
            'EndDate': weekly_data[-1]['Date'],  # 周结束日期
            'NewCustomers': sum(d['NewCustomers'] for d in weekly_data),  # 周新增客户数
            'TotalCustomers': weekly_data[-1]['TotalCustomers'],  # 累计总客户数（去重）
            'TotalMembers': weekly_data[-1]['TotalMembers'],  # 累计会员数（仅买了会员卡的）
            'PatientsSeen': sum(d['PatientsSeen'] for d in weekly_data),  # 周就诊人次
            'RevenueTotal': sum(d['RevenueTotal'] for d in weekly_data),  # 周总营收
            'Costs': sum(d['Costs'] for d in weekly_data),  # 周总成本
            'Profit': sum(d['Profit'] for d in weekly_data),  # 周总利润
            'CashFlowWeekly': sum(d['CashFlowToday'] for d in weekly_data),  # 周现金流
            'Cash': weekly_data[-1]['Cash'],  # 周末现金余额
            
            # 分类营收
            'RevenueCard': sum(d['RevenueCard'] for d in weekly_data),  # 周卡类营收
            'RevenueTreatment': sum(d['RevenueTreatment'] for d in weekly_data),  # 周治疗营收
            'RevenueOrtho': sum(d['RevenueOrtho'] for d in weekly_data),  # 周矫正营收
            
            # 分类利润
            'ProfitCard': sum(d.get('ProfitCard', 0) for d in weekly_data),  # 周卡类利润
            'ProfitTreatment': sum(d.get('ProfitTreatment', 0) for d in weekly_data),  # 周治疗利润
            'ProfitOrtho': sum(d.get('ProfitOrtho', 0) for d in weekly_data),  # 周矫正利润
            
            # 分类现金流
            'CashFlowCard': sum(d['CashFlowCard'] for d in weekly_data),  # 周卡类现金流
            'CashFlowTreatment': sum(d['CashFlowTreatment'] for d in weekly_data),  # 周治疗现金流
            'CashFlowOrtho': sum(d['CashFlowOrtho'] for d in weekly_data),  # 周矫正现金流
            
            # 人员相关
            'CurrentPediatricDoctors': weekly_data[-1]['CurrentPediatricDoctors'],  # 当前儿牙医生数
            'CurrentOrthoDoctors': weekly_data[-1]['CurrentOrthoDoctors'],  # 当前矫正医生数
            'CurrentNurses': weekly_data[-1]['CurrentNurses'],  # 当前护士数
            'CurrentOps': weekly_data[-1].get('CurrentOps', 1),  # 当前运营数
            'DoctorSalary': sum(d.get('DoctorSalary', 0) for d in weekly_data),  # 周医生工资
            'NurseSalary': sum(d.get('NurseSalary', 0) for d in weekly_data),  # 周护士工资
            'OpsSalary': sum(d.get('OpsSalary', 0) for d in weekly_data)  # 周运营工资
        }
        
        self.state['weekly_history'].append(weekly_stats)
        
        # 重新计算所有月度数据，确保数据准确性
        self._recalculate_all_monthly_stats()
    
    def _recalculate_all_monthly_stats(self):
        """重新计算所有月度数据，直接从日数据聚合"""
        # 清空现有月度数据
        self.state['monthly_history'] = []
        
        # 获取所有日数据
        daily_data = self.state['daily_history']
        if not daily_data:
            return
        
        # 按月分组日数据：将每个日数据分配到它所属的月份
        monthly_groups = {}
        for day in daily_data:
            if 'Month' not in day:
                continue
            month = day['Month']
            if month not in monthly_groups:
                monthly_groups[month] = []
            monthly_groups[month].append(day)
        
        # 为每个月计算统计数据
        for month, month_days in sorted(monthly_groups.items()):
            # 确保数据按天数排序
            month_days.sort(key=lambda x: x['Day'])
            
            # 计算月总医生工资和护士工资
            total_doctor_salary = sum(d.get('DoctorSalary', 0) for d in month_days)
            total_nurse_salary = sum(d.get('NurseSalary', 0) for d in month_days)
            total_ops_salary = sum(d.get('OpsSalary', 0) for d in month_days)
            
            # 获取月末的医生和护士人数
            total_doctors = month_days[-1]['CurrentPediatricDoctors'] + month_days[-1]['CurrentOrthoDoctors']
            total_nurses = month_days[-1]['CurrentNurses']
            total_ops = month_days[-1].get('CurrentOps', 1)
            
            # 计算人均工资（避免除以0）
            avg_doctor_salary = total_doctor_salary / total_doctors if total_doctors > 0 else 0
            avg_nurse_salary = total_nurse_salary / total_nurses if total_nurses > 0 else 0
            avg_ops_salary = total_ops_salary / total_ops if total_ops > 0 else 0
            
            monthly_stats = {
                'Month': month,
                'StartDay': month_days[0]['Day'],
                'EndDay': month_days[-1]['Day'],
                'NewCustomers': sum(d['NewCustomers'] for d in month_days),  # 月新增客户数
                'TotalCustomers': month_days[-1]['TotalCustomers'],  # 累计总客户数（去重）
                'TotalMembers': month_days[-1]['TotalMembers'],  # 累计会员数（仅买了会员卡的）
                'PatientsSeen': sum(d['PatientsSeen'] for d in month_days),  # 月就诊人次
                'RevenueTotal': sum(d['RevenueTotal'] for d in month_days),  # 月总营收
                'Costs': sum(d['Costs'] for d in month_days),  # 月总成本
                'Profit': sum(d['Profit'] for d in month_days),  # 月总利润
                'CashFlowMonthly': sum(d['CashFlowToday'] for d in month_days),  # 月现金流
                'Cash': month_days[-1]['Cash'],  # 月末现金余额
                
                # 分类营收
                'RevenueCard': sum(d['RevenueCard'] for d in month_days),  # 月卡类营收
                'RevenueTreatment': sum(d['RevenueTreatment'] for d in month_days),  # 月治疗营收
                'RevenueOrtho': sum(d['RevenueOrtho'] for d in month_days),  # 月矫正营收
                
                # 分类利润
                'ProfitCard': sum(d.get('ProfitCard', 0) for d in month_days),  # 月卡类利润
                'ProfitTreatment': sum(d.get('ProfitTreatment', 0) for d in month_days),  # 月治疗利润
                'ProfitOrtho': sum(d.get('ProfitOrtho', 0) for d in month_days),  # 月矫正利润
                
                # 分类现金流
                'CashFlowCard': sum(d['CashFlowCard'] for d in month_days),  # 月卡类现金流
                'CashFlowTreatment': sum(d['CashFlowTreatment'] for d in month_days),  # 月治疗现金流
                'CashFlowOrtho': sum(d['CashFlowOrtho'] for d in month_days),  # 月矫正现金流
                
                # 人员工资（人均）
                'DoctorSalary': avg_doctor_salary,  # 月人均医生工资
                'NurseSalary': avg_nurse_salary,  # 月人均护士工资
                'OpsSalary': avg_ops_salary,  # 月人均运营工资
                
                # 人员相关
                'CurrentPediatricDoctors': month_days[-1]['CurrentPediatricDoctors'],  # 当前儿牙医生数
                'CurrentOrthoDoctors': month_days[-1]['CurrentOrthoDoctors'],  # 当前矫正医生数
                'CurrentNurses': month_days[-1]['CurrentNurses'],  # 当前护士数
                'CurrentOps': month_days[-1].get('CurrentOps', 1)  # 当前运营数
            }
            
            self.state['monthly_history'].append(monthly_stats)
        
        # 更新当前月份
        if monthly_groups:
            self.state['current_month'] = max(monthly_groups.keys())
        else:
            self.state['current_month'] = 0
    
    def get_results(self, type="daily"):
        """获取结果数据"""
        if type == "daily":
            return self.state['daily_history']
        elif type == "weekly":
            return self.state['weekly_history']
        elif type == "monthly":
            return self.state['monthly_history']
        else:
            return []
    
    def get_summary(self):
        """获取总结数据"""
        if not self.state['daily_history']:
            return {
                'total_weeks': 0,
                'total_customers': 0,
                'total_members': 0,
                'total_revenue': 0,
                'total_profit': 0,
                'final_cash': -(self.params['invest_decoration'] + self.params['invest_hardware'])
            }
        
        # 总客户数：去重的唯一客户（所有历史患者）
        total_customers = len(self.state['all_patients'])
        # 最终会员数：只有买了会员卡的患者才算
        total_members = len([p for p in self.state['all_patients'] if p.is_active and p.card_type is not None])
        # 总营收和总成本
        total_revenue = sum(d['RevenueTotal'] for d in self.state['daily_history'])
        total_costs = sum(d['Costs'] for d in self.state['daily_history'])
        
        return {
            'total_weeks': self.state['current_week'],
            'total_customers': total_customers,
            'total_members': total_members,
            'total_revenue': total_revenue,
            'total_profit': total_revenue - total_costs,
            'final_cash': self.state['current_cash']
        }
    
    def get_patient_details(self):
        """获取患者详细记录"""
        return self.state['patient_details']
    
    def get_pivot_data(self):
        """获取患者行为透视表数据"""
        df_raw = pd.DataFrame(self.state['pivot_records'])
        if df_raw.empty:
            return pd.DataFrame()
        
        # 使用 pivot 将原始记录转换为以“患者”为行、“日期”为列的矩阵
        df_pivot = df_raw.pivot(index='PatientID', columns='Day', values='Val').fillna('')
        return df_pivot

