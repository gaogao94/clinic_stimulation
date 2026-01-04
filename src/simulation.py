#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊所运营模拟核心逻辑

包含诊所日常运营的主要模拟逻辑，包括患者流、医生接诊、财务计算等
"""

import random
import numpy as np
import pandas as pd
from .patient import Patient


def run_simulation(
    years=10,                          # 模拟时长（年） 
    invest_decoration=280000,         # 装修投资成本
    invest_hardware=300000,           # 硬件设备投资成本 
    num_chairs=4,                     # 诊疗椅数量
    num_pediatric_doctors=1,          # 初始儿牙专职医生人数
    num_ortho_doctors=0,              # 初始三级儿牙正畸医生人数
    num_nurses=4,                     # 初始护士人数（含1个管理者）
    daily_new_leads_base=3,          # 每日基础新客流入量 
    prob_card_1yr=0.2,                # 新客办1年卡的概率 
    prob_card_5yr=0.4,               # 新客办5年卡的概率 
    price_card_1yr=1000,              # 1年卡价格 
    price_card_5yr=5000,              # 5年卡价格 
    prob_treatment=0.10,               # 每次就诊的治疗概率
    price_treatment=800,             # 基础治疗平均单价 
    prob_ortho=0.0001,                  # 非会员非初诊每次就诊转矫正项目的概率 
    price_ortho=25000,                # 高值项目平均单价 
    follow_up_cycle=90,               # 建议复诊周期（天） 
    prob_follow_up=0.95,              # 老客户收到复诊通知后赴约的概率 
    prob_renew_1yr=0.15,               # 1年卡到期后续约概率 
    prob_renew_5yr=0.3,               # 5年卡到期后续约概率 
    monthly_rent=63000,               # 每月房租固定支出
    doctor_base_salary=10000,         # 医生底薪
    doctor_guaranteed_salary=15000,   # 医生第一年保底工资
    doctor_commission_rate=0.1,       # 医生提成比例
    nurse_base_salary=5000,           # 护士底薪
    nurse_guaranteed_salary=7000,     # 护士保底工资
    nurse_commission_rate=0.03,       # 护士提成比例
    pediatric_material_ratio=0.05,    # 儿牙耗材比例
    ortho_material_ratio=0.30,        # 矫正耗材比例
    card_revenue_recognition_ratio=0.2,  # 会员卡办卡当日确认营收比例，默认20%
):
    """
    诊所运营模拟核心函数
    
    模拟牙科诊所的日常运营，包括：
    1. 患者流管理（新患者获取、老患者复诊）
    2. 会员卡销售和续卡
    3. 医疗服务提供（预防、基础治疗、矫正）
    4. 人员管理（医生、护士）
    5. 财务管理（现金流、权责发生制收入）
    6. 合同负债计算
    
    参数：
    见函数定义中的注释
    
    返回：
    - df_pivot: 患者行为透视表
    - daily_stats: 每日统计数据
    - df_age_dist: 年龄分布数据
    """
    
    # 1. 定义新客年龄分布数据（17000新客的情况下）
    age_distribution = {
        1: 1000,
        2: 2700,
        3: 2600,
        4: 1800,
        5: 1800,
        6: 1700,
        7: 1200,
        8: 1100,
        9: 800,
        10: 600,
        11: 600,
        12: 300,
        13: 200,
        14: 100
    }
    
    # 计算总人数和每个年龄的概率
    total_patients = sum(age_distribution.values())
    age_list = list(age_distribution.keys())
    age_probs = [count / total_patients for count in age_distribution.values()]
    
    # ========== 初始化模拟参数 ==========
    days = int(years * 365)                # 将模拟年限转换为总天数（整数） 
    all_patients = []                 # 存储所有产生的患者对象实例 
    pivot_records = []                # 用于存储透视表所需的原始记录: {'PatientID', 'Day', 'Val', 'Age', 'Source'}
    daily_history = []                # 存储每日总计财务数据 
    patient_counter = 0               # 全局患者ID计数器 
    current_cash = -(invest_decoration + invest_hardware)  # 初始现金流（负值，代表初始投入）
    
    # ========== 收入分摊相关变量 ==========
    # 卡类收入分摊相关变量
    card_1yr_monthly_revenue = 0      # 1年卡月均分摊收入
    card_5yr_monthly_revenue = 0      # 5年卡月均分摊收入
    card_1yr_total = 0                 # 累计1年卡总收入
    card_5yr_total = 0                 # 累计5年卡总收入
    monthly_card_revenue = 0           # 当月卡类分摊收入
    
    # 矫正收入分摊相关变量
    ortho_started_revenue = 0          # 本月开始矫正的收入（55%）
    ortho_completed_revenue = 0        # 本月结束矫正的收入（45%）
    
    # ========== 月度累计变量 ==========
    monthly_cash_flow = 0              # 当月现金流
    monthly_revenue = 0                # 当月营收
    monthly_pediatric_revenue = 0      # 当月儿牙营收
    monthly_ortho_revenue = 0          # 当月矫正营收
    monthly_card_sales = 0             # 当月卖卡现金收入
    
    # ========== 合同负债相关变量 ==========
    contract_liability = 0             # 合同负债总额
    ortho_contract_liability = 0       # 矫正未确认收入
    card_contract_liability = 0        # 卡类合同负债
    
    # 初始人员配置 - 固定医生数量为2个，护士数量根据需要调整但不超过6个
    current_pediatric_doctors = 1  # 固定1个儿牙医生
    current_ortho_doctors = 1  # 固定1个矫正医生，总共2个医生
    current_nurses = num_nurses
    
    # ========== 开始逐日模拟 ==========
    for day in range(1, days + 1):  
        # ---------- 人员配置管理 ----------
        # 人员爬坡逻辑 - 医生数量保持2个，护士数量根据需要调整但不超过6个
        if day > 180:  # 6个月后
            current_ortho_doctors = 1  # 保持1个矫正医生，医生总数不变
        if day > 365:  # 1年后
            current_pediatric_doctors = 1  # 保持1个儿牙医生，医生总数不变
            current_nurses = 6  # 增加到6个护士（最多6个）
        if day > 730:  # 2年后
            current_ortho_doctors = 1  # 保持1个矫正医生，医生总数不变
            current_nurses = 6  # 保持最多6个护士
        
        # ---------- 今日财务数据初始化 ----------
        cash_today = 0                # 今日现金流（实际收到的现金）
        revenue_today = 0             # 今日营收（不含卡类分摊）
        revenue_prevention = 0        # 今日预防服务收入（权责发生制）
        revenue_treatment = 0         # 今日基础治疗收入（权责发生制）
        revenue_ortho = 0             # 今日矫正收入（权责发生制：开始55% + 结束45%）
        revenue_card_immediate = 0    # 今日办卡确认的收入（20%）
        cash_new_card = 0             # 今日新办卡现金收入
        cash_renew_card = 0           # 今日续卡现金收入
        todays_visitors = []          # 今日到店患者名单 
        new_customers = 0             # 今日新客数量
        card_sales_today = 0          # 今日新办卡和续卡的总金额
        
        # ---------- 患者分类准备 ----------
        pediatric_patients = []       # 今日儿牙患者
        ortho_patients = []           # 今日矫正患者
        
        # 计算当日卡类分摊收入（权责发生制）
        daily_card_revenue = 0
        if day % 30 == 1 or day == 1:
            # 1年卡分摊到12个月，5年卡分摊到60个月
            # 只分摊(1 - card_revenue_recognition_ratio)的部分，因为其余部分已在办卡当日确认
            monthly_card_revenue = (card_1yr_total * (1 - card_revenue_recognition_ratio) / 12) + (card_5yr_total * (1 - card_revenue_recognition_ratio) / 60)
            card_1yr_monthly_revenue = card_1yr_total * (1 - card_revenue_recognition_ratio) / 12
            card_5yr_monthly_revenue = card_5yr_total * (1 - card_revenue_recognition_ratio) / 60
        daily_card_revenue = monthly_card_revenue / 30  # 日均卡类分摊收入
        
        # 更新合同负债：卡类收入的未确认部分
        # 已确认的卡类收入 = 办卡当日确认的20% + 已摊销的部分
        months_passed = day // 30
        recognized_immediate = (card_1yr_total + card_5yr_total) * card_revenue_recognition_ratio
        recognized_amortized = (card_1yr_total * (1 - card_revenue_recognition_ratio) / 12 * min(months_passed, 12)) + (card_5yr_total * (1 - card_revenue_recognition_ratio) / 60 * min(months_passed, 60))
        recognized_card_revenue = recognized_immediate + recognized_amortized
        card_contract_liability = (card_1yr_total + card_5yr_total) - recognized_card_revenue
        
        # 1. 老患者复诊与续卡判定 
        for p in all_patients: 
            if not p.is_active: continue  # 如果患者已流失则跳过 
            
            # 续卡判定：如果今天刚好是会员卡到期日 
            if p.card_expiry_day == day: 
                # 计算当前年龄：初诊年龄 + 距离初诊的年数（按365天/年计算）
                current_age = p.initial_age + (day - p.join_day) // 365
                roll = random.random()    # 掷随机数决定是否续费 
                if roll < prob_renew_1yr: # 续1年 
                    amt = p.buy_card('1yr', day, price_card_1yr) 
                    cash_today += amt 
                    cash_renew_card += amt 
                    card_1yr_total += amt
                    card_sales_today += amt
                    pivot_records.append({'PatientID': f'P{p.id:03}', 'Day': f'D{day:03}', 'Val': f'续1年卡(+{amt})', 'Age': current_age, 'Source': p.source}) 
                elif roll < (prob_renew_1yr + prob_renew_5yr): # 续5年 
                    amt = p.buy_card('5yr', day, price_card_5yr) 
                    cash_today += amt 
                    cash_renew_card += amt 
                    card_5yr_total += amt
                    card_sales_today += amt
                    pivot_records.append({'PatientID': f'P{p.id:03}', 'Day': f'D{day:03}', 'Val': f'续5年卡(+{amt})', 'Age': current_age, 'Source': p.source}) 
            
            # 复诊判定：如果今天有常规预约或矫正复诊 
            if p.next_appointment_day == day or p.next_ortho_appointment == day: 
                if random.random() < prob_follow_up: # 如果患者准时赴约 
                    todays_visitors.append(p)        # 加入今日到店名单 
                else: 
                    # 未赴约，推迟30天再联系 
                    if p.next_appointment_day == day: 
                        p.next_appointment_day = day + 30 
                    if p.next_ortho_appointment == day: 
                        p.next_ortho_appointment = day + 30 
        
        # 2. 获取新初诊客户 
        # 计算增长因子：模拟诊所开业初期客流较少，随时间增加逐渐趋于稳定（180天达到最高峰） 
        growth_factor = min(1.0, 0.4 + (day / 180) * 0.6) 
        # 根据高斯分布生成今日新客数 
        num_new_leads = max(0, int(random.gauss(daily_new_leads_base, 1) * growth_factor)) 
        new_customers = num_new_leads  # 记录今日新客数量 
        
        for _ in range(num_new_leads): 
            patient_counter += 1               # 增加ID计数 
            # 根据年龄分布生成初诊年龄 
            initial_age = random.choices(age_list, weights=age_probs, k=1)[0] 
            new_p = Patient(patient_counter, day, initial_age) # 创建新患者对象 
            
            roll = random.random()             # 判定新客是否在首诊时办卡 
            action_desc = "初诊" 
            card_rev = 0 
            if roll < prob_card_1yr: 
                card_rev = new_p.buy_card('1yr', day, price_card_1yr) 
                action_desc += f"+办1年卡(+{card_rev})" 
                card_1yr_total += card_rev
                card_sales_today += card_rev
            elif roll < (prob_card_1yr + prob_card_5yr): 
                card_rev = new_p.buy_card('5yr', day, price_card_5yr) 
                action_desc += f"+办5年卡(+{card_rev})" 
                card_5yr_total += card_rev
                card_sales_today += card_rev
            
            if card_rev > 0:
                cash_today += card_rev             # 办卡收入计入现金流
                cash_new_card += card_rev           # 记录今日新办卡现金收入
            
            pivot_records.append({'PatientID': f'P{new_p.id:03}', 'Day': f'D{day:03}', 'Val': action_desc, 'Age': initial_age, 'Source': new_p.source}) 
            todays_visitors.append(new_p)      # 新客首日必然到店 
            all_patients.append(new_p)         # 加入总患者库 

        # 3. 资源瓶颈与诊疗逻辑 
        # 诊所接诊上限：受限于牙椅数量（1椅配20人）或医生精力（1医配30人） 
        total_doctors = current_pediatric_doctors + current_ortho_doctors
        capacity = min(num_chairs * 20, total_doctors * 30) 
        actual_seen = todays_visitors[:capacity] # 超出负荷的患者今日无法就诊 
        
        # 患者分类：区分儿牙和矫正患者
        for p in actual_seen: 
            treatment_rev = 0 
            prevention_rev = 0 
            ortho_rev = 0 
            actions = [] 
            current_age = p.initial_age + (day - p.join_day) // 365
            
            # 预防服务判定 
            # if random.random() < prob_prevention: 
            #     if p.use_prevention(): 
            #         actions.append(f"免费预防") 
            #     else: 
            #         prevention_rev += price_prevention 
            #         revenue_today += prevention_rev 
            #         revenue_prevention += prevention_rev 
            #         cash_today += prevention_rev
            #         actions.append(f"预防(+{prevention_rev})") 
            
            # 治疗判定 
            if random.random() < prob_treatment: # 判定是否产生普通治疗 
                # 检查是否有治疗折扣（会员卡65折） 
                discount = 0.65 if p.card_expiry_day > 0 else 1.0 
                treatment_amt = int(price_treatment * discount) 
                treatment_rev += treatment_amt 
                
                # 治疗收入：权责发生制下直接计入营收
                revenue_today += treatment_amt
                revenue_treatment += treatment_amt
                cash_today += treatment_amt  # 治疗收入直接计入现金流
                
                actions.append(f"治疗(+{treatment_amt})") 
            
            # 高值项目判定：矫正 
            # 如果之前未进行过矫正，根据会员状态和年龄计算概率 
            if not p.has_ortho and not p.ortho_completed: 
                # 计算当前年龄
                current_age = p.initial_age + (day - p.join_day) // 365
                
                # 1. 确定矫正概率 
                ortho_prob = 0.0 
                
                # 检查是否为初诊（join_day == day）
                is_first_visit = (p.join_day == day) 
                
                if is_first_visit: 
                    # 初诊患者矫正概率 
                    if current_age <= 6: 
                        ortho_prob = 0.00  # 6岁及以下 0%
                    elif current_age == 7: 
                        ortho_prob = 0.04  # 7岁 4%
                    elif 8 <= current_age <= 10: 
                        ortho_prob = 0.10  # 8岁至10岁 10%
                    elif current_age >= 11: 
                        ortho_prob = 0.20  # 11至13岁以上 20%
                else: 
                    # 非初诊患者（会员或非会员）
                    # 会员状态：card_expiry_day > 0表示会员
                    is_member = (p.card_expiry_day > 0)
                    
                    if is_member: 
                        # 会员患者矫正概率 
                        if current_age <= 6: 
                            ortho_prob = 0.0025  # 6岁及以下 0.25%
                        elif current_age == 7: 
                            ortho_prob = 0.02     # 7岁 2%
                        elif 8 <= current_age <= 13: 
                            ortho_prob = 0.03     # 8岁至13岁 3%
                        elif current_age > 13: 
                            ortho_prob = 0.01     # 13岁以上 1%
                    else: 
                        # 非会员非初诊患者，使用默认概率
                        ortho_prob = prob_ortho
                
                # 2. 确定矫正金额
                ortho_amt = 0
                if current_age <= 6: 
                    ortho_amt = 8000   # 6岁及以下 8000元
                elif current_age == 7: 
                    ortho_amt = 14000  # 7岁 14000元
                else: 
                    ortho_amt = 30000  # 8岁以上 30000元
                
                # 3. 检查是否有治疗折扣（会员卡65折）
                discount = 0.65 if p.card_expiry_day > 0 else 1.0
                ortho_amt = int(ortho_amt * discount)
                
                # 4. 随机判定是否进行矫正 - 只有矫正医生在时才能进行
                if current_ortho_doctors > 0 and random.random() < ortho_prob: 
                    # 记录矫正信息
                    p.has_ortho = True
                    p.ortho_start_day = day
                    p.ortho_age = current_age
                    
                    # 确定矫正时长和结束日期
                    # 6岁以下矫正1年结束，6岁以上矫正2年结束
                    if current_age < 6: 
                        ortho_duration = 365  # 1年
                    else: 
                        ortho_duration = 730  # 2年
                    p.ortho_end_day = day + ortho_duration
                    
                    # 安排下次矫正复诊（30天后）
                    p.next_ortho_appointment = day + 30
                    
                    # 计算收入 - 矫正开始时计入55%的营收和全部现金流
                    ortho_start_amount = int(ortho_amt * 0.55)
                    ortho_end_amount = int(ortho_amt * 0.45)
                    
                    # 记录开始矫正的收入
                    revenue_today += ortho_start_amount
                    revenue_ortho += ortho_start_amount
                    cash_today += ortho_amt  # 全部现金流立即计入
                    
                    # 合同负债：剩余45%计入
                    ortho_contract_liability += ortho_end_amount
                    
                    actions.append(f"矫正(+{ortho_amt})") 
            
            # 检查是否为矫正复诊
            is_ortho_appointment = (p.next_ortho_appointment == day)
            
            # 处理矫正复诊
            if is_ortho_appointment: 
                # 计算当前年龄
                current_age = p.initial_age + (day - p.join_day) // 365
                
                # 检查矫正是否已结束
                if day > p.ortho_end_day: 
                    # 矫正结束，标记完成
                    p.ortho_completed = True
                    p.next_ortho_appointment = None
                    
                    # 计算结束矫正的收入 - 计入剩余45%
                    # 重新计算矫正金额以获取正确的45%部分
                    if p.ortho_age <= 6: 
                        ortho_amt_end = 8000
                    elif p.ortho_age == 7: 
                        ortho_amt_end = 14000
                    else: 
                        ortho_amt_end = 30000
                    
                    discount_end = 0.65 if p.card_expiry_day > 0 else 1.0
                    ortho_amt_end = int(ortho_amt_end * discount_end)
                    ortho_end_amount = int(ortho_amt_end * 0.45)
                    
                    # 记录结束矫正的收入
                    revenue_today += ortho_end_amount
                    revenue_ortho += ortho_end_amount
                    
                    # 从合同负债中减去已确认的45%收入
                    ortho_contract_liability -= ortho_end_amount
                    
                    actions.append("矫正结束")
                else: 
                    # 矫正未结束，安排下一次复诊（30天后）
                    p.next_ortho_appointment = day + 30
                    actions.append("矫正复诊")
            
            # 记录所有动作（包括矫正复诊）
            if any([prevention_rev, treatment_rev, ortho_rev]) or len(actions) > 0: 
                # 更新透视表记录：如果该患者今天已有动作（如办卡），则合并文字描述 
                existing = [r for r in pivot_records if r['PatientID'] == f'P{p.id:03}' and r['Day'] == f'D{day:03}'] 
                current_age = p.initial_age + (day - p.join_day) // 365
                if existing: 
                    existing[0]['Val'] += f"+{'+'.join(actions)}" 
                    existing[0]['Age'] = current_age  # 更新年龄信息
                else: 
                    pivot_records.append({'PatientID': f'P{p.id:03}', 'Day': f'D{day:03}', 'Val': f"{'+'.join(actions)}", 'Age': current_age, 'Source': p.source}) 
            
            # 为就诊过的患者预约下一次常规复诊时间（设定周期加上正负5天的随机波动）
            # 只有在不是矫正复诊时才更新常规复诊时间
            if not is_ortho_appointment:
                p.next_appointment_day = day + follow_up_cycle + random.randint(-5, 5)

        # 4. 财务统计与支出记录 
        
        # 计算当日确认的卡类收入：办卡当日确认的20%
        revenue_card_immediate = card_sales_today * card_revenue_recognition_ratio
        
        # 计算总营收：权责发生制（治疗+矫正+卡类分摊+办卡当日确认收入）
        total_revenue_today = revenue_today + daily_card_revenue + revenue_card_immediate
        
        # 计算耗材成本：区分儿牙和矫正
        pediatric_revenue = revenue_treatment + revenue_prevention
        ortho_revenue = revenue_ortho
        costs_today = (pediatric_revenue * pediatric_material_ratio) + (ortho_revenue * ortho_material_ratio)
        
        # 计算今日现金流
        cash_flow_today = cash_today - costs_today
        
        # 月度累计
        monthly_cash_flow += cash_flow_today
        monthly_revenue += total_revenue_today
        monthly_pediatric_revenue += pediatric_revenue
        monthly_ortho_revenue += ortho_revenue
        monthly_card_sales += (cash_new_card + cash_renew_card)
        
        # 每隔30天结算一次固定成本（工资和房租）
        doctor_salary = 0
        nurse_salary = 0
        # 计算当前月和下月的第一天，在每月最后一天结算工资
        current_month = (day - 1) // 31 + 1
        next_month_first_day = current_month * 31 + 1
        if day == next_month_first_day - 1: 
            # 计算医生薪酬：底薪+提成+保底
            # 提成基于月度总营收（权责发生制）
            
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
            doctor_salary = (current_pediatric_doctors * pediatric_doctor_total) + (current_ortho_doctors * ortho_doctor_total)
            
            # 计算护士薪酬：底薪+提成+保底
            nurse_commission = monthly_revenue * nurse_commission_rate
            nurse_individual = nurse_base_salary + nurse_commission
            nurse_individual = max(nurse_individual, nurse_guaranteed_salary)
            nurse_salary = current_nurses * nurse_individual
            
            total_salary = doctor_salary + nurse_salary
            costs_today += (monthly_rent + total_salary)
            
            # 重新计算包含固定成本的现金流
            cash_flow_today = cash_today - costs_today
            monthly_cash_flow = cash_flow_today  # 重置月度现金流为包含固定成本的当日值
            
            # 重置月度累计
            monthly_revenue = 0
            monthly_pediatric_revenue = 0
            monthly_ortho_revenue = 0
            monthly_card_sales = 0
            ortho_started_revenue = 0
            ortho_completed_revenue = 0
        
        # 更新当前现金总额
        current_cash += cash_flow_today
        
        # 计算合同负债总额：卡类未确认收入 + 矫正未确认收入
        contract_liability = card_contract_liability + ortho_contract_liability
        
        # 计算截止到当日的会员数：active且卡未过期的患者
        current_members = sum(1 for p in all_patients if p.is_active and p.card_expiry_day > day)
        
        # 当日就诊总人数：实际接诊的患者数
        today_patients_seen = len(actual_seen)
        
        daily_history.append({                # 记录每日财务快照 
            'Day': day, 
            'Month': (day - 1) // 30 + 1,  # 计算当前月份
            'NewCustomers': new_customers, 
            'TotalMembers': current_members, 
            'PatientsSeen': today_patients_seen, 
            'CurrentPediatricDoctors': current_pediatric_doctors,  # 当前儿牙医生数
            'CurrentOrthoDoctors': current_ortho_doctors,  # 当前矫正医生数
            'CurrentNurses': current_nurses,  # 当前护士数
            'RevenuePrevention': revenue_prevention, 
            'RevenueTreatment': revenue_treatment, 
            'RevenueOrtho': revenue_ortho, 
            'RevenueCardDaily': daily_card_revenue,  # 当日卡类分摊收入（权责发生制）
            'RevenueTotal': total_revenue_today,  # 当日总营收（权责发生制）
            'CashNewCard': cash_new_card,  # 当日新办卡现金收入
            'CashRenewCard': cash_renew_card,  # 当日续卡现金收入
            'CashTreatment': cash_today - cash_new_card - cash_renew_card,  # 当日治疗和矫正的现金收入
            'CashFlowToday': cash_flow_today,  # 当日现金流
            'Cash': current_cash,  # 当前现金总额
            'Costs': costs_today,  # 当日总成本
            'DoctorSalary': doctor_salary,  # 当日医生工资（仅在月结日有值）
            'NurseSalary': nurse_salary,  # 当日护士工资（仅在月结日有值）
            'MonthlyCardRevenue': monthly_card_revenue,  # 当月卡类分摊收入
            'ContractLiability': contract_liability,  # 合同负债总额（借客户的钱）
            'CardContractLiability': card_contract_liability,  # 卡类合同负债
            'OrthoContractLiability': ortho_contract_liability,  # 矫正合同负债
            'PediatricMaterialRatio': pediatric_material_ratio, 
            'OrthoMaterialRatio': ortho_material_ratio
        }) 

    # 数据收尾：创建患者行为透视表 
    df_raw = pd.DataFrame(pivot_records) 
    
    # 确保result目录存在 - 提前创建以避免保存时出错
    import os
    # 使用脚本所在目录的父目录作为基础路径，确保结果文件写入到正确位置
    script_dir = os.path.dirname(os.path.abspath(__file__))
    result_dir = os.path.join(os.path.dirname(script_dir), "result")
    if not os.path.exists(result_dir):
        os.makedirs(result_dir, exist_ok=True)
    
    # 保存包含年龄信息的原始记录到CSV文件
    df_raw.to_csv(f"{result_dir}/纯新患者模拟_with_age.csv", encoding="gbk", index=False)
    # 使用 pivot 将原始记录转换为以“患者”为行、“日期”为列的矩阵 
    df_pivot = df_raw.pivot(index='PatientID', columns='Day', values='Val').fillna('') 
    
    # 创建年龄分布数据框（仅用于返回，不保存到文件）
    df_age_dist = pd.DataFrame({
        'Age': age_list,
        'Count': [age_distribution[age] for age in age_list],
        'Probability': age_probs
    })
    
    return df_pivot, pd.DataFrame(daily_history), df_age_dist  # 返回透视表和每日统计 
