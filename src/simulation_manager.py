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
from .patient import Patient


class SimulationManager:
    """
    模拟管理器类，负责管理模拟状态、参数和执行逻辑
    """
    
    def __init__(self):
        """初始化模拟管理器"""
        # 模拟参数默认值
        self.default_params = {
            'years': 10,
            'invest_decoration': 280000,
            'invest_hardware': 300000,
            'pre_opening_investment': 0,  # 开业前期投入：0元（一次性投入）
            'num_chairs': 4,
            'num_pediatric_doctors': 0,
            'num_ortho_doctors': 1,
            'num_nurses': 4,
            'daily_new_leads_base': 3,
            'initial_members': 400,  # 初始会员数量，默认400人
            'prob_card_1yr': 0.2,
            'prob_card_5yr': 0.4,
            'price_card_1yr': 1000,
            'price_card_5yr': 5000,
            'prob_treatment': 0.10,
            'price_treatment': 800,
            'prob_ortho': 0.01,
            'price_ortho': 25000,
            'follow_up_cycle': 90,
            'prob_follow_up': 0.95,
            'prob_renew_1yr': 0.15,
            'prob_renew_5yr': 0.3,
            'rent_per_sqm_per_day': 6,  # 租金：元每平米每天（按照建筑面积计算）
            'building_area': 150,  # 建筑面积：143平米（不可调整）
            'occupancy_rate': 0.7,  # 得房率：70%（不可调整，仅展示使用面积）
            'monthly_utilities': 2000,  # 每月水电费：2000元（固定）
            'monthly_marketing': 10000,  # 每月市场费用：10000元（固定）
            'monthly_other_costs': 0,  # 每月其他成本：0元（固定）
            'doctor_base_salary': 15000,
            'doctor_guaranteed_salary': 15000,
            'doctor_commission_rate': 0.15,
            'nurse_base_salary': 7000,
            'nurse_guaranteed_salary': 7000,
            'nurse_commission_rate': 0.03,
            'pediatric_material_ratio': 0.05,
            'ortho_material_ratio': 0.30,
            'card_revenue_recognition_ratio': 0.2,  # 会员卡办卡当日确认营收比例，默认20%
            'clinic_type': 'ortho'  # 诊所类型：'ortho'做矫正，'pediatric'纯儿牙
        }
        
        # 初始化params为默认值
        self.params = self.default_params.copy()
        
        # 初始化状态
        self.reset_simulation()
    
    def reset_simulation(self):
        """重置模拟状态"""
        # 重置模拟状态，但保留当前参数
        self.state = {
            'current_day': 0,
            'current_week': 0,
            'current_month': 0,
            'all_patients': [],
            'pivot_records': [],
            'patient_details': [],  # 患者详细记录，包括每个患者的行为和财务数据
            'daily_history': [],
            'weekly_history': [],
            'monthly_history': [],
            'patient_counter': 0,
            'current_cash': -(self.params['invest_decoration'] + self.params['invest_hardware'] + self.params['pre_opening_investment']),  # 包含开业前期投入
            'current_pediatric_doctors': self.params['num_pediatric_doctors'],
            'current_ortho_doctors': self.params['num_ortho_doctors'],
            'current_nurses': self.params['num_nurses'],
            'card_1yr_total': 0,
            'card_5yr_total': 0,
            'monthly_card_revenue': 0,
            'ortho_started_revenue': 0,
            'ortho_completed_revenue': 0,
            'monthly_cash_flow': 0,
            'monthly_revenue': 0,
            'monthly_pediatric_revenue': 0,
            'monthly_ortho_revenue': 0,
            'monthly_card_sales': 0,
            'contract_liability': 0,
            'ortho_contract_liability': 0,
            'card_contract_liability': 0,
            # 确保耗材比例被正确应用
        }
        
        # 初始化现有会员
        initial_members_count = self.params['initial_members']
        if initial_members_count > 0:
            for i in range(initial_members_count):
                self.state['patient_counter'] += 1
                # 生成平均9岁，标准差2岁的年龄
                age = max(0.1, np.random.normal(9, 2))
                
                # 创建现有会员，join_day设为0表示初始就存在
                p = Patient(self.state['patient_counter'], 0, age, source="existing")
                
                # 所有现有会员都有5年卡，剩余到期天数随机
                total_5yr_days = 365 * 5
                remaining_days = random.randint(1, total_5yr_days)
                p.card_type = '5yr'
                p.card_expiry_day = remaining_days
                p.remaining_prevention = -1  # 5年卡无限次免费预防
                
                # 安排在3个月内（90天）随机到店
                first_visit_day = random.randint(1, 90)
                p.next_appointment_day = first_visit_day
                
                # 添加到患者列表
                self.state['all_patients'].append(p)
        
        # 年龄分布数据
        self.age_distribution = {
            1: 1000, 2: 2700, 3: 2600, 4: 1800, 5: 1800, 6: 1700,
            7: 1200, 8: 1100, 9: 800, 10: 600, 11: 600, 12: 300,
            13: 200, 14: 100
        }
        self.total_patients = sum(self.age_distribution.values())
        self.age_list = list(self.age_distribution.keys())
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
        if self.state['current_day'] >= self.params['years'] * 365:
            return {'status': 'error', 'message': 'Simulation has completed'}
        
        # 运行7天模拟
        for _ in range(7):
            if self.state['current_day'] >= self.params['years'] * 365:
                break
            self._run_single_day()
        
        # 更新周数
        self.state['current_week'] += 1
        
        # 计算每周统计数据
        self._calculate_weekly_stats()
        
        return {
            'status': 'success',
            'message': f'Week {self.state["current_week"]} simulated',
            'current_week': self.state['current_week'],
            'current_day': self.state['current_day']
        }
    
    def _run_single_day(self):
        """运行单日模拟"""
        day = self.state['current_day'] + 1
        self.state['current_day'] = day
        
        # 今日财务数据初始化
        cash_today = 0
        revenue_today = 0
        
        # 分类收入和现金流
        revenue_treatment = 0
        revenue_ortho = 0
        revenue_card_immediate = 0  # 卡类收入的当日确认部分
        revenue_card_amortized = 0  # 卡类收入的分摊部分
        
        cash_new_card = 0
        cash_renew_card = 0
        cash_treatment = 0
        cash_ortho = 0
        
        todays_visitors = []
        new_customers = 0
        
        # 今日新办卡和续卡的总金额
        card_sales_today = 0
        
        # 患者分类处理
        pediatric_patients = []
        ortho_patients = []
        
        # 计算当日卡类分摊收入（权责发生制）
        daily_card_revenue = 0
        if day % 30 == 1 or day == 1:
            # 获取办卡当日确认营收比例
            card_recognition_ratio = self.params['card_revenue_recognition_ratio']
            
            # 计算需要摊销的卡类收入：总卡类收入 - 办卡当日已确认的20%
            card_1yr_amortize = self.state['card_1yr_total'] * (1 - card_recognition_ratio)
            card_5yr_amortize = self.state['card_5yr_total'] * (1 - card_recognition_ratio)
            
            # 1年卡分摊到12个月，5年卡分摊到60个月
            self.state['monthly_card_revenue'] = (card_1yr_amortize / 12) + (card_5yr_amortize / 60)
        daily_card_revenue = self.state['monthly_card_revenue'] / 30
        
        # 记录卡类分摊收入
        revenue_card_amortized = daily_card_revenue
        
        # 更新合同负债：卡类收入的未确认部分
        card_recognition_ratio = self.params['card_revenue_recognition_ratio']
        months_passed = day // 30
        
        # 已确认的卡类收入 = 办卡当日确认的20% + 已摊销的部分
        recognized_immediate = (self.state['card_1yr_total'] + self.state['card_5yr_total']) * card_recognition_ratio
        recognized_amortized = (self.state['card_1yr_total'] * (1 - card_recognition_ratio) / 12 * min(months_passed, 12)) + \
                               (self.state['card_5yr_total'] * (1 - card_recognition_ratio) / 60 * min(months_passed, 60))
        recognized_card_revenue = recognized_immediate + recognized_amortized
        
        self.state['card_contract_liability'] = (self.state['card_1yr_total'] + self.state['card_5yr_total']) - recognized_card_revenue
        
        # 1. 老患者复诊与续卡判定
        for p in self.state['all_patients']:
            if not p.is_active: continue
            
            # 续卡判定：如果今天刚好是会员卡到期日
            if p.card_expiry_day == day:
                current_age = p.initial_age + (day - p.join_day) // 365
                roll = random.random()
                if roll < self.params['prob_renew_1yr']:
                    amt = p.buy_card('1yr', day, self.params['price_card_1yr'])
                    cash_today += amt
                    cash_renew_card += amt
                    self.state['card_1yr_total'] += amt
                    card_sales_today += amt
                    
                    # 计算当前周数
                    week_num = (day - 1) // 7 + 1
                    
                    # 计算实际日期，以2026年1月1日作为第一天
                    from datetime import datetime, timedelta
                    start_date = datetime(2026, 1, 1)
                    current_date = start_date + timedelta(days=day-1)
                    formatted_date = current_date.strftime('%Y-%m-%d')
                    
                    # 记录患者详细信息
                    self.state['patient_details'].append({
                        'PatientID': p.id,
                        'Day': day,
                        'Date': formatted_date,  # 添加实际日期
                        'Week': week_num,
                        'Age': current_age,
                        'Action': '续卡',
                        'CardType': '1年卡',
                        'Amount': amt,
                        'RevenueType': '卡类收入',
                        'CashFlow': amt,
                        'Costs': 0,  # 续卡无直接成本
                        'Profit': amt,
                        'Description': f'患者续1年卡，金额{amt}元',
                        'Source': p.source  # 添加来源信息
                    })
                    
                    self.state['pivot_records'].append({
                        'PatientID': f'P{p.id:03}', 
                        'Day': f'D{day:03}', 
                        'Val': f'Renew 1yr card(+{amt})', 
                        'Age': current_age, 
                        'Source': p.source
                    })
                elif roll < (self.params['prob_renew_1yr'] + self.params['prob_renew_5yr']):
                    amt = p.buy_card('5yr', day, self.params['price_card_5yr'])
                    cash_today += amt
                    cash_renew_card += amt
                    self.state['card_5yr_total'] += amt
                    card_sales_today += amt
                    
                    # 计算当前周数
                    week_num = (day - 1) // 7 + 1
                    
                    # 计算实际日期，以2026年1月1日作为第一天
                    from datetime import datetime, timedelta
                    start_date = datetime(2026, 1, 1)
                    current_date = start_date + timedelta(days=day-1)
                    formatted_date = current_date.strftime('%Y-%m-%d')
                    
                    # 记录患者详细信息
                    self.state['patient_details'].append({
                        'PatientID': p.id,
                        'Day': day,
                        'Date': formatted_date,  # 添加实际日期
                        'Week': week_num,
                        'Age': current_age,
                        'Action': '续卡',
                        'CardType': '5年卡',
                        'Amount': amt,
                        'RevenueType': '卡类收入',
                        'CashFlow': amt,
                        'Costs': 0,  # 续卡无直接成本
                        'Profit': amt,
                        'Description': f'患者续5年卡，金额{amt}元',
                        'Source': p.source  # 添加来源信息
                    })
                    
                    self.state['pivot_records'].append({
                        'PatientID': f'P{p.id:03}', 
                        'Day': f'D{day:03}', 
                        'Val': f'Renew 5yr card(+{amt})', 
                        'Age': current_age, 
                        'Source': p.source
                    })
            
            # 复诊判定：如果今天有常规预约或矫正复诊
            is_ortho_appointment = False
            # 只有当诊所类型是ortho时才处理矫正复诊
            if p.next_appointment_day == day or (self.params['clinic_type'] == 'ortho' and p.next_ortho_appointment == day):
                if self.params['clinic_type'] == 'ortho' and p.next_ortho_appointment == day:
                    is_ortho_appointment = True
                    
                    # 检查是否是最后一次矫正复诊（矫正完成）
                    # 假设总共24次复诊，每次间隔45天，总时长约3年
                    total_ortho_days = 45 * 24
                    if day - p.ortho_start_day >= total_ortho_days and not getattr(p, 'ortho_completed', False):
                        # 矫正完成，不产生耗材费用，营收记入剩余的45%
                        if hasattr(p, 'ortho_revenue_remaining') and p.ortho_revenue_remaining > 0:
                            # 记录矫正完成的营收
                            revenue_ortho += p.ortho_revenue_remaining
                            
                            # 计算当前周数
                            week_num = (day - 1) // 7 + 1
                            
                            # 计算实际日期，以2026年1月1日作为第一天
                            from datetime import datetime, timedelta
                            start_date = datetime(2026, 1, 1)
                            current_date = start_date + timedelta(days=day-1)
                            formatted_date = current_date.strftime('%Y-%m-%d')
                            
                            # 记录患者详细信息
                            self.state['patient_details'].append({
                                'PatientID': p.id,
                                'Day': day,
                                'Date': formatted_date,  # 添加实际日期
                                'Week': week_num,
                                'Age': p.initial_age + (day - p.join_day) // 365,
                                'Action': '矫正结束',
                                'CardType': p.card_type,
                                'Amount': p.ortho_total_cost,
                                'RevenueType': '矫正收入',
                                'CashFlow': 0,  # 矫正结束不产生现金流
                                'Costs': 0,  # 矫正结束不产生耗材费用
                                'Profit': p.ortho_revenue_remaining,  # 利润为剩余营收
                                'Description': f'患者矫正完成，记入剩余营收{p.ortho_revenue_remaining:.2f}元（45%），无额外耗材费用'
                            })
                            
                            self.state['pivot_records'].append({
                                'PatientID': f'P{p.id:03}', 
                                'Day': f'D{day:03}', 
                                'Val': f'Ortho End(rev:+{p.ortho_revenue_remaining:.2f})', 
                                'Age': p.initial_age + (day - p.join_day) // 365, 
                                'Source': p.source
                            })
                            
                            # 标记矫正已完成
                            p.ortho_completed = True
                            p.ortho_end_day = day
                            p.ortho_revenue_remaining = 0
                        
                        # 矫正完成后不再有矫正复诊
                        p.next_ortho_appointment = None
                    else:
                        # 不是最后一次复诊，继续预约下一次
                        p.next_ortho_appointment = day + 45
                    
                    todays_visitors.append(p)
                
                # 常规复诊处理
                if p.next_appointment_day == day:
                    if random.random() < self.params['prob_follow_up']:
                        todays_visitors.append(p)
                    else:
                        # 未赴约，推迟30天再联系
                        p.next_appointment_day = day + 30
        
        # 2. 获取新初诊客户
        growth_factor = min(1.0, 0.4 + (day / 180) * 0.6)
        num_new_leads = max(0, int(random.gauss(self.params['daily_new_leads_base'], 1) * growth_factor))
        new_customers = 0  # 初始化为0，实际新客户数
        
        for _ in range(num_new_leads):
            self.state['patient_counter'] += 1
            initial_age = random.choices(self.age_list, weights=self.age_probs, k=1)[0]
            new_p = Patient(self.state['patient_counter'], day, initial_age)
            
            roll = random.random()
            action_desc = "Initial visit"
            card_rev = 0
            card_type = None
            
            if roll < self.params['prob_card_1yr']:
                card_rev = new_p.buy_card('1yr', day, self.params['price_card_1yr'])
                action_desc += f"+Buy 1yr card(+{card_rev})"
                cash_today += card_rev
                cash_new_card += card_rev
                self.state['card_1yr_total'] += card_rev
                card_sales_today += card_rev
                card_type = '1年卡'
            elif roll < (self.params['prob_card_1yr'] + self.params['prob_card_5yr']):
                card_rev = new_p.buy_card('5yr', day, self.params['price_card_5yr'])
                action_desc += f"+Buy 5yr card(+{card_rev})"
                cash_today += card_rev
                cash_new_card += card_rev
                self.state['card_5yr_total'] += card_rev
                card_sales_today += card_rev
                card_type = '5年卡'
            
            # 计算当前周数
            week_num = (day - 1) // 7 + 1
            
            # 计算实际日期，以2026年1月1日作为第一天
            from datetime import datetime, timedelta
            start_date = datetime(2026, 1, 1)
            current_date = start_date + timedelta(days=day-1)
            formatted_date = current_date.strftime('%Y-%m-%d')
            
            # 记录患者详细信息
            self.state['patient_details'].append({
                'PatientID': new_p.id,
                'Day': day,
                'Date': formatted_date,  # 添加实际日期
                'Week': week_num,
                'Age': initial_age,
                'Action': '初诊',
                'CardType': card_type,
                'Amount': card_rev,
                'RevenueType': '卡类收入' if card_rev > 0 else '初诊',
                'CashFlow': card_rev,
                'Costs': 0,  # 初诊成本已包含在固定成本中
                'Profit': card_rev,
                'Description': f'患者初诊，{f"购买{card_type}，" if card_type else ""}金额{card_rev}元',
                'Source': new_p.source  # 添加来源信息
            })
            
            # 记录患者行为
            self.state['pivot_records'].append({
                'PatientID': f'P{new_p.id:03}', 
                'Day': f'D{day:03}', 
                'Val': action_desc, 
                'Age': initial_age, 
                'Source': new_p.source
            })
            
            # 设置新患者的初始复诊日期
            # 确保使用的是当前设置的follow_up_cycle参数
            follow_up_cycle = self.params['follow_up_cycle']
            new_p.next_appointment_day = day + follow_up_cycle
            self.state['all_patients'].append(new_p)
            todays_visitors.append(new_p)
            # 只有native来源的患者才计入新客户
            if new_p.source == "native":
                new_customers += 1  # 实际新客户数递增
        
        # 3. 患者就诊处理
        for p in todays_visitors:
            # 简单的就诊处理
            current_age = p.initial_age + (day - p.join_day) // 365
            
            # 计算当前周数
            week_num = (day - 1) // 7 + 1
            
            # 计算实际日期，以2026年1月1日作为第一天
            from datetime import datetime, timedelta
            start_date = datetime(2026, 1, 1)
            current_date = start_date + timedelta(days=day-1)
            formatted_date = current_date.strftime('%Y-%m-%d')
            
            # 记录患者就诊信息
            if p.next_appointment_day == day or p.next_ortho_appointment == day:
                # 这是一个复诊患者
                self.state['patient_details'].append({
                    'PatientID': p.id,
                    'Day': day,
                    'Date': formatted_date,
                    'Week': week_num,
                    'Age': current_age,
                    'Action': '复诊',
                    'CardType': p.card_type,
                    'Amount': 0,
                    'RevenueType': '复诊',
                    'CashFlow': 0,
                    'Costs': 0,
                    'Profit': 0,
                    'Description': f'患者复诊',
                    'Source': p.source  # 添加来源信息
                })
                
                self.state['pivot_records'].append({
                    'PatientID': f'P{p.id:03}', 
                    'Day': f'D{day:03}', 
                    'Val': f'Follow-up', 
                    'Age': current_age, 
                    'Source': p.source
                })
            
            # 随机判定是否进行治疗
            if random.random() < self.params['prob_treatment']:
                # 检查是否有治疗折扣（会员卡65折）
                discount = 0.65 if p.card_expiry_day > 0 else 1.0
                treatment_cost = int(self.params['price_treatment'] * discount)
                cash_today += treatment_cost
                cash_treatment += treatment_cost  # 记录治疗现金流
                revenue_treatment += treatment_cost
                
                # 计算耗材成本
                material_cost = treatment_cost * self.params['pediatric_material_ratio']
                profit = treatment_cost - material_cost
                
                # 计算当前周数
                week_num = (day - 1) // 7 + 1
                
                # 计算实际日期，以2026年1月1日作为第一天
                from datetime import datetime, timedelta
                start_date = datetime(2026, 1, 1)
                current_date = start_date + timedelta(days=day-1)
                formatted_date = current_date.strftime('%Y-%m-%d')
                
                # 记录患者详细信息
                self.state['patient_details'].append({
                    'PatientID': p.id,
                    'Day': day,
                    'Date': formatted_date,  # 添加实际日期
                    'Week': week_num,
                    'Age': current_age,
                    'Action': '治疗',
                    'CardType': p.card_type,
                    'Amount': treatment_cost,
                    'RevenueType': '治疗收入',
                    'CashFlow': treatment_cost,
                    'Costs': material_cost,
                    'Profit': profit,
                    'Description': f'患者接受基础治疗，收入{treatment_cost}元，耗材成本{material_cost:.2f}元，利润{profit:.2f}元',
                    'Source': p.source  # 添加来源信息
                })
                
                self.state['pivot_records'].append({
                    'PatientID': f'P{p.id:03}', 
                    'Day': f'D{day:03}', 
                    'Val': f'Treatment(+{treatment_cost})', 
                    'Age': current_age, 
                    'Source': p.source
                })
            
            # 随机判定是否进行矫正 - 根据年龄调整概率
            # 只有当诊所类型是ortho时才允许矫正
            if self.params['clinic_type'] == 'ortho':
                current_age = p.initial_age + (day - p.join_day) // 365
                base_ortho_prob = self.params['prob_ortho']
                
                # 根据年龄调整矫正概率
                age_ortho_prob = base_ortho_prob
                if current_age < 6:
                    age_ortho_prob = base_ortho_prob * 0.1  # 6岁以下概率低
                elif 6 <= current_age <= 10:
                    age_ortho_prob = base_ortho_prob * 2.0  # 6-10岁概率中等
                elif 11 <= current_age <= 14:
                    age_ortho_prob = base_ortho_prob * 5.0  # 11-14岁概率高
                
                if random.random() < age_ortho_prob:
                    ortho_cost = self.params['price_ortho']
                    # 检查是否有治疗折扣（会员卡65折）
                    discount = 0.65 if p.card_expiry_day > 0 else 1.0
                    ortho_cost = int(ortho_cost * discount)
                    
                    # 矫正开始当天现金流收入应该是完整的25000
                    ortho_cash = ortho_cost  # 开始矫正时收取全额
                    cash_today += ortho_cash
                    cash_ortho += ortho_cash  # 记录矫正现金流
                    
                    # 开始时是记入营收55%
                    revenue_ortho += ortho_cost * 0.55
                    
                    # 当天产生耗材费用7500
                    material_cost = ortho_cost * self.params['ortho_material_ratio']
                    profit = ortho_cost * 0.55 - material_cost
                    
                    # 计算当前周数
                    week_num = (day - 1) // 7 + 1
                    
                    # 计算实际日期，以2026年1月1日作为第一天
                    from datetime import datetime, timedelta
                    start_date = datetime(2026, 1, 1)
                    current_date = start_date + timedelta(days=day-1)
                    formatted_date = current_date.strftime('%Y-%m-%d')
                    
                    # 记录患者详细信息
                    self.state['patient_details'].append({
                        'PatientID': p.id,
                        'Day': day,
                        'Date': formatted_date,  # 添加实际日期
                        'Week': week_num,
                        'Age': current_age,
                        'Action': '矫正开始',
                        'CardType': p.card_type,
                        'Amount': ortho_cost,
                        'RevenueType': '矫正收入',
                        'CashFlow': ortho_cost,  # 现金流是全额
                        'Costs': material_cost,
                        'Profit': profit,
                        'Description': f'患者开始矫正，现金流{ortho_cost:.2f}元（总费用{ortho_cost}元），记入营收{ortho_cost * 0.55:.2f}元（55%），耗材成本{material_cost:.2f}元，利润{profit:.2f}元',
                        'Source': p.source  # 添加来源信息
                    })
                    
                    self.state['pivot_records'].append({
                        'PatientID': f'P{p.id:03}', 
                        'Day': f'D{day:03}', 
                        'Val': f'Ortho Start(+{ortho_cost:.2f}, rev:{ortho_cost * 0.55:.2f})', 
                        'Age': current_age, 
                        'Source': p.source
                    })
                    
                    # 设置矫正复诊日期：每45天一次，总共24次
                    p.has_ortho = True
                    p.ortho_start_day = day
                    p.ortho_age = current_age
                    p.next_ortho_appointment = day + 45
                    p.ortho_total_cost = ortho_cost  # 记录总矫正费用
                    p.ortho_revenue_remaining = ortho_cost * 0.45  # 剩余45%营收待确认
            
            # 设置下次常规复诊日期
            if p.next_appointment_day is None or p.next_appointment_day <= day:
                # 根据患者类型设置不同的复诊周期
                follow_up_cycle = self.params['follow_up_cycle']
                p.next_appointment_day = day + follow_up_cycle
        
        # 计算医生和护士工资
        doctor_salary_today = 0
        nurse_salary_today = 0
        
        # 只在每月最后一天计算工资
        # 计算当前月和下月的第一天
        current_month = (day - 1) // 31 + 1
        next_month_first_day = current_month * 31 + 1
        
        if day == next_month_first_day - 1 or day == self.params['years'] * 365:
            # 计算医生薪酬：底薪+提成+保底
            # 提成基于月度总营收（权责发生制）
            
            # 计算月度总营收
            # 从最近31天的日数据中计算当月营收
            monthly_revenue = 0
            monthly_pediatric_revenue = 0
            monthly_ortho_revenue = 0
            
            # 获取当月的日数据
            for d in reversed(self.state['daily_history']):
                if d['Month'] == current_month:
                    monthly_revenue += d['RevenueTotal']
                    monthly_pediatric_revenue += d.get('RevenueTreatment', 0)
                    monthly_ortho_revenue += d.get('RevenueOrtho', 0)
            
            # 医生薪酬计算
            doctor_commission_rate = self.params['doctor_commission_rate']
            doctor_base_salary = self.params['doctor_base_salary']
            doctor_guaranteed_salary = self.params['doctor_guaranteed_salary']
            
            # 儿牙医生薪酬
            pediatric_doctor_commission = monthly_pediatric_revenue * doctor_commission_rate
            pediatric_doctor_total = doctor_base_salary + pediatric_doctor_commission
            # 第一年有保底
            if day <= 365:  # 第一年
                pediatric_doctor_total = max(pediatric_doctor_total, doctor_guaranteed_salary)
            
            # 矫正医生薪酬
            ortho_doctor_commission = monthly_ortho_revenue * doctor_commission_rate
            ortho_doctor_total = doctor_base_salary + ortho_doctor_commission
            # 第一年有保底
            if day <= 365:  # 第一年
                ortho_doctor_total = max(ortho_doctor_total, doctor_guaranteed_salary)
            
            # 使用当前人员数量（考虑爬坡）计算工资
            doctor_salary_today = (self.state['current_pediatric_doctors'] * pediatric_doctor_total) + \
                                  (self.state['current_ortho_doctors'] * ortho_doctor_total)
            
            # 护士薪酬计算
            nurse_commission_rate = self.params['nurse_commission_rate']
            nurse_base_salary = self.params['nurse_base_salary']
            nurse_guaranteed_salary = self.params['nurse_guaranteed_salary']
            
            nurse_commission = monthly_revenue * nurse_commission_rate
            nurse_individual = nurse_base_salary + nurse_commission
            nurse_individual = max(nurse_individual, nurse_guaranteed_salary)
            nurse_salary_today = self.state['current_nurses'] * nurse_individual
        
        # 4. 计算当日成本
        # 房租和工资统一在每月最后一天结算
        costs_today = 0
        
        # 每日计算耗材成本（治疗和矫正的耗材成本已经在各自的处理逻辑中计算）
        # 固定成本（房租、工资）只在每月最后一天结算
        
        # 检查是否是当月最后一天或模拟最后一天
        if day == next_month_first_day - 1 or day == self.params['years'] * 365:
            # 计算月固定成本
            # 房租计算：月房租 = 建筑面积 × 日租金 × 当月天数
            # 计算当月实际天数
            # 计算当前月的第一天
            current_month_first_day = (current_month - 1) * 31 + 1
            # 计算当月天数
            if current_month < 12:
                # 非12月，当月天数 = 下月第一天 - 当月第一天
                monthly_days = current_month * 31 + 1 - current_month_first_day
            else:
                # 12月，当月天数 = 31天
                monthly_days = 31
            # 使用建筑面积直接计算租金，不考虑使用面积
            monthly_rent = self.params['building_area'] * self.params['rent_per_sqm_per_day'] * monthly_days
            
            # 添加水电、市场费用和每月其他成本
            monthly_utilities = self.params['monthly_utilities']
            monthly_marketing = self.params['monthly_marketing']
            monthly_other_costs = self.params['monthly_other_costs']
            
            # 使用之前计算好的医生和护士工资
            # 这些工资已经包含了提成和保底
            costs_today = monthly_rent + monthly_utilities + monthly_marketing + monthly_other_costs + doctor_salary_today + nurse_salary_today
        
        # 计算当日确认的卡类收入：办卡当日确认的20%
        card_recognition_ratio = self.params['card_revenue_recognition_ratio']
        revenue_card_immediate = card_sales_today * card_recognition_ratio
        
        # 计算总卡类营收（当日确认 + 分摊）
        revenue_card = revenue_card_immediate + revenue_card_amortized
        
        # 计算总营收
        revenue_today = revenue_treatment + revenue_ortho + revenue_card
        
        # 计算卡类现金流
        cash_card = cash_new_card + cash_renew_card
        
        # 计算利润
        # 1. 卡类利润：与营收记入方式一致，只要记入营收的，都直接记入利润
        # 卡类营收已经包含了当日确认的20%和分摊的部分，所以利润直接等于营收
        profit_card = revenue_card  # 卡类营收全部计入利润，与营收记入方式一致
        
        # 2. 治疗利润：现金流入记入营收，扣减儿牙操作成本后记入利润
        # 统计当日治疗的耗材成本
        treatment_material_cost = 0
        # 从patient_details中查找今日的治疗记录，计算耗材成本
        for record in self.state['patient_details']:
            if record['Day'] == day and record['Action'] == '治疗':
                treatment_material_cost += record['Costs']
        profit_treatment = revenue_treatment - treatment_material_cost
        
        # 3. 矫正利润：矫正开始当次扣减全部成本，结束当次记入营收的全部记入利润
        ortho_material_cost = 0
        # 从patient_details中查找今日的矫正记录，计算耗材成本
        for record in self.state['patient_details']:
            if record['Day'] == day and record['Action'] == '矫正开始':
                ortho_material_cost += record['Costs']
        profit_ortho = revenue_ortho - ortho_material_cost  # 矫正开始当次：营收55% - 全部耗材成本；矫正结束当次：营收45% - 0成本
        
        # 4. 总利润：卡类利润 + 治疗利润 + 矫正利润 - 当月变动成本
        # 当月变动成本包括：医生工资、护士工资、房租、水电、市场费用等
        # 这些成本已经包含在costs_today中，只在每月最后一天计算
        profit_today = profit_card + profit_treatment + profit_ortho - costs_today
        
        # 5. 更新现金和收入
        self.state['current_cash'] += cash_today - costs_today
        
        # 6. 计算各项统计指标
        # 计算实际日期，以2026年1月1日作为第一天
        from datetime import datetime, timedelta
        start_date = datetime(2026, 1, 1)
        current_date = start_date + timedelta(days=day-1)
        formatted_date = current_date.strftime('%Y-%m-%d')
        
        # 总客户数：去重的唯一客户（所有历史患者）
        total_customers = len(self.state['all_patients'])
        # 最终会员数：只有买了会员卡的患者才算
        total_members = len([p for p in self.state['all_patients'] if p.is_active and p.card_type is not None])
        # 就诊人次：今日到店患者数（来一次算一次）
        patients_seen = len(todays_visitors)
        
        # 计算月份（从1开始，更准确的月份计算）
        # 1-31日为第1个月，32-61日为第2个月，依此类推
        month = current_month
        
        # 记录每日统计数据
        self.state['daily_history'].append({
            'Day': day,
            'Date': formatted_date,  # 添加实际日期
            'Week': (day - 1) // 7 + 1,  # 计算周数
            'Month': month,  # 添加月份
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
            
            # 保留原始数据但调整顺序，将不重要的字段放在后面
            'Card1YrTotal': self.state['card_1yr_total'],
            'Card5YrTotal': self.state['card_5yr_total'],
            'MonthlyCardRevenue': self.state['monthly_card_revenue'],
            'CardContractLiability': self.state['card_contract_liability'],
            'OrthoContractLiability': self.state['ortho_contract_liability'],
            'CurrentPediatricDoctors': self.state['current_pediatric_doctors'],
            'CurrentOrthoDoctors': self.state['current_ortho_doctors'],
            'CurrentNurses': self.state['current_nurses']
        })
        
        # 更新患者详细记录中的月份
        for record in self.state['patient_details']:
            if record['Day'] == day and 'Month' not in record:
                record['Month'] = month
    
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
            'DoctorSalary': sum(d.get('DoctorSalary', 0) for d in weekly_data),  # 周医生工资
            'NurseSalary': sum(d.get('NurseSalary', 0) for d in weekly_data)  # 周护士工资
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
            
            # 获取月末的医生和护士人数
            total_doctors = month_days[-1]['CurrentPediatricDoctors'] + month_days[-1]['CurrentOrthoDoctors']
            total_nurses = month_days[-1]['CurrentNurses']
            
            # 计算人均工资（避免除以0）
            avg_doctor_salary = total_doctor_salary / total_doctors if total_doctors > 0 else 0
            avg_nurse_salary = total_nurse_salary / total_nurses if total_nurses > 0 else 0
            
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
                
                # 人员相关
                'CurrentPediatricDoctors': month_days[-1]['CurrentPediatricDoctors'],  # 当前儿牙医生数
                'CurrentOrthoDoctors': month_days[-1]['CurrentOrthoDoctors'],  # 当前矫正医生数
                'CurrentNurses': month_days[-1]['CurrentNurses']  # 当前护士数
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

