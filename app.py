#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
牙科诊所模拟系统Web应用主文件

使用Flask框架构建，支持参数控制、按周模拟和结果查看
"""

from flask import Flask, render_template, request, jsonify
import os
import sys

# 添加src目录到路径，以便导入现有模块
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# 初始化Flask应用
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'

# 全局模拟管理器实例
from src.simulation_manager import SimulationManager
sim_manager = SimulationManager()


@app.route('/')
def index():
    """参数控制页"""
    return render_template('control.html')


@app.route('/detail')
def detail():
    """结果明细页"""
    return render_template('detail.html')


@app.route('/summary')
def summary():
    """结果总结页"""
    return render_template('summary.html')


@app.route('/api/params', methods=['GET', 'POST'])
def api_params():
    """获取或设置模拟参数"""
    if request.method == 'GET':
        return jsonify(sim_manager.get_params())
    else:
        params = request.get_json()
        result = sim_manager.set_params(params)
        return jsonify(result)


@app.route('/api/simulation/reset', methods=['POST'])
def api_reset():
    """重置模拟"""
    result = sim_manager.reset_simulation()
    return jsonify(result)


@app.route('/api/simulation/next', methods=['POST'])
def api_next():
    """运行下一周模拟"""
    result = sim_manager.run_next_week()
    return jsonify(result)


@app.route('/api/simulation/state', methods=['GET'])
def api_state():
    """获取当前模拟状态"""
    state = sim_manager.get_state()
    return jsonify(state)


@app.route('/api/results/daily', methods=['GET'])
def api_results_daily():
    """获取每日结果"""
    results = sim_manager.get_results(type="daily")
    return jsonify(results)


@app.route('/api/results/weekly', methods=['GET'])
def api_results_weekly():
    """获取每周结果"""
    results = sim_manager.get_results(type="weekly")
    return jsonify(results)


@app.route('/api/results/monthly', methods=['GET'])
def api_results_monthly():
    """获取月度结果"""
    results = sim_manager.get_results(type="monthly")
    return jsonify(results)


@app.route('/api/results/summary', methods=['GET'])
def api_results_summary():
    """获取总结数据"""
    summary = sim_manager.get_summary()
    return jsonify(summary)


@app.route('/api/results/patient_details', methods=['GET'])
def api_results_patient_details():
    """获取患者详细记录"""
    patient_details = sim_manager.get_patient_details()
    return jsonify(patient_details)


if __name__ == '__main__':
    # 创建templates和static目录（如果不存在）
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    # 启动开发服务器
    app.run(debug=True, port=5000)
