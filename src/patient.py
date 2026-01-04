#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
患者个体代理类

用于追踪患者的完整生命周期行为，包括办卡、复诊、矫正等
"""


class Patient:
    """
    患者个体代理类，用于追踪患者的完整生命周期行为
    
    属性说明：
    - id: 患者唯一识别ID
    - join_day: 患者第一次进入诊所的日期
    - initial_age: 患者初诊时的年龄
    - source: 患者来源（固定为"native"=原生）
    - card_type: 会员卡类型（"1yr"=1年卡，"5yr"=5年卡，None=无卡）
    - card_expiry_day: 会员卡到期日期
    - next_appointment_day: 下次常规复诊预约日期
    - is_active: 患者是否活跃（未流失）
    - remaining_prevention: 剩余免费预防次数（-1表示无限次）
    - has_ortho: 是否已进行过矫正
    - ortho_start_day: 矫正开始日期
    - ortho_end_day: 矫正结束日期
    - next_ortho_appointment: 下次矫正复诊日期
    - ortho_age: 进行矫正时的年龄
    - ortho_completed: 矫正是否已完成
    """
    
    def __init__(self, patient_id, join_day, initial_age, source="native"):
        """
        初始化患者对象
        
        参数：
        - patient_id: 患者唯一ID
        - join_day: 初诊日期
        - initial_age: 初诊年龄
        - source: 患者来源（"native"=原生，"existing"=初始配置的现有会员）
        """
        self.id = patient_id           # 患者唯一识别ID
        self.join_day = join_day       # 初诊日期
        self.initial_age = initial_age # 初诊年龄
        self.source = source           # 患者来源：原生或初始配置的现有会员
        self.card_type = None          # 初始无会员卡
        self.card_expiry_day = 0       # 会员卡到期日期，初始为0（无卡）
        self.next_appointment_day = None  # 下次常规复诊日期
        self.is_active = True          # 初始为活跃状态
        self.remaining_prevention = 0  # 剩余免费预防次数，初始为0
        
        # 矫正相关属性初始化
        self.has_ortho = False         # 初始未进行矫正
        self.ortho_start_day = 0       # 矫正开始日期
        self.ortho_end_day = 0         # 矫正结束日期
        self.next_ortho_appointment = None  # 下次矫正复诊日期
        self.ortho_age = 0             # 矫正时年龄
        self.ortho_completed = False   # 矫正未完成

    def buy_card(self, card_type, current_day, price):
        """
        购买会员卡，更新会员状态
        
        参数：
        - card_type: 卡类型（"1yr"=1年卡，"5yr"=5年卡）
        - current_day: 当前日期
        - price: 卡价格
        
        返回：
        - 办卡收入金额
        """
        self.card_type = card_type     # 更新会员卡类型
        # 计算卡有效期：1年=365天，5年=365*5天
        duration = 365 if card_type == '1yr' else 365 * 5
        self.card_expiry_day = current_day + duration  # 计算到期日期
        # 设置免费预防次数：1年卡4次，5年卡无限次
        self.remaining_prevention = 4 if card_type == '1yr' else -1
        return price                   # 返回办卡收入

    def use_prevention(self):
        """
        使用一次预防服务，判断是否免费
        
        返回：
        - True: 免费使用
        - False: 收费使用
        """
        # 检查是否有有效会员卡且有免费次数
        if self.card_expiry_day > 0 and (self.remaining_prevention > 0 or self.remaining_prevention == -1):
            if self.remaining_prevention > 0:
                self.remaining_prevention -= 1  # 减少免费次数
            return True  # 免费使用
        return False  # 收费使用
