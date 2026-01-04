// 总结页JavaScript

// 检查Chart.js是否已加载
function checkChartJsLoaded() {
    if (typeof Chart === 'undefined') {
        console.error('Chart.js 未加载，尝试重新加载...');
        // 动态加载Chart.js
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/chart.js';
        script.onload = function() {
            console.log('Chart.js 重新加载成功');
            // 重新初始化页面
            initSummaryPage();
        };
        script.onerror = function() {
            console.error('Chart.js 重新加载失败');
        };
        document.head.appendChild(script);
        return false;
    }
    return true;
}

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 检查Chart.js是否已加载
    if (checkChartJsLoaded()) {
        // 初始化页面
        initSummaryPage();
    }
});

// 初始化总结页
function initSummaryPage() {
    // 获取DOM元素
    const chartBtns = document.querySelectorAll('.chart-btn');
    const refreshChartBtn = document.getElementById('refresh-chart');
    
    // 当前图表类型
    let currentChartType = 'revenue';
    
    // 图表实例
    let chart = null;
    
    // 保存上一次的数据状态
    let lastSummaryData = null;
    let lastWeeklyData = null;
    
    // 绑定图表切换事件
    chartBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            // 更新活跃按钮
            chartBtns.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            
            // 切换图表类型
            currentChartType = this.dataset.chart;
            
            // 刷新图表（仅切换类型，不需要重新获取数据）
            if (lastWeeklyData) {
                renderTrendChart(lastWeeklyData);
            }
        });
    });
    
    // 刷新图表按钮点击事件
    refreshChartBtn.addEventListener('click', function() {
        // 强制刷新数据和图表
        lastSummaryData = null;
        lastWeeklyData = null;
        loadSummaryData();
        refreshCharts();
    });
    
    // 初始加载数据
    loadSummaryData();
    refreshCharts();
    
    // 定期更新数据（每5秒）
    setInterval(() => {
        loadSummaryData();
        refreshCharts();
    }, 5000);
    
    // 比较两个数据对象是否相等
    function isDataEqual(data1, data2) {
        if (!data1 || !data2) return false;
        return JSON.stringify(data1) === JSON.stringify(data2);
    }
    
    // 加载总结数据
    function loadSummaryData() {
        fetch('/api/results/summary')
            .then(response => response.json())
            .then(summary => {
                // 检查数据是否变化
                if (isDataEqual(summary, lastSummaryData)) {
                    return; // 数据未变化，不更新
                }
                
                // 更新统计卡片
                document.getElementById('stat-weeks').textContent = summary.total_weeks;
                document.getElementById('stat-customers').textContent = summary.total_customers;
                document.getElementById('stat-members').textContent = summary.total_members;
                document.getElementById('stat-revenue').textContent = summary.total_revenue.toFixed(2);
                document.getElementById('stat-profit').textContent = summary.total_profit.toFixed(2);
                document.getElementById('stat-cash').textContent = summary.final_cash.toFixed(2);
                
                // 更新分析
                updateAnalysis(summary);
                
                // 保存当前数据作为下次比较的基准
                lastSummaryData = JSON.parse(JSON.stringify(summary));
            })
            .catch(error => {
                console.error('Error loading summary:', error);
            });
    }
    
    // 刷新图表
    function refreshCharts() {
        // 加载月数据用于图表
        fetch('/api/results/monthly')
            .then(response => response.json())
            .then(monthlyData => {
                console.log('月度数据:', monthlyData);
                let dataToUse = monthlyData;
                let isWeekly = false;
                
                if (monthlyData.length === 0) {
                    // 如果没有月度数据，回退到周数据
                    return fetch('/api/results/weekly')
                        .then(response => response.json())
                        .then(weeklyData => {
                            console.log('周数据:', weeklyData);
                            if (weeklyData.length === 0) {
                                console.log('没有周数据，不渲染图表');
                                return;
                            }
                            
                            dataToUse = weeklyData;
                            isWeekly = true;
                            
                            // 检查数据是否变化
                            if (isDataEqual(dataToUse, lastWeeklyData)) {
                                console.log('数据未变化，不更新图表');
                                return; // 数据未变化，不更新图表
                            }
                            
                            try {
                                // 渲染趋势图表
                                console.log('渲染趋势图表');
                                renderTrendChart(dataToUse, isWeekly);
                                
                                // 渲染新增的图表
                                console.log('渲染现金流成本对比图');
                                renderCashflowCostChart(dataToUse, isWeekly);
                                console.log('渲染投资回报对比图');
                                renderInvestmentRevenueChart(dataToUse, isWeekly);
                                
                                // 保存当前数据作为下次比较的基准
                                lastWeeklyData = JSON.parse(JSON.stringify(dataToUse));
                                console.log('图表更新成功');
                            } catch (error) {
                                console.error('渲染图表时出错:', error);
                            }
                        });
                }
                
                // 检查数据是否变化
                if (isDataEqual(dataToUse, lastWeeklyData)) {
                    console.log('数据未变化，不更新图表');
                    return; // 数据未变化，不更新图表
                }
                
                try {
                    // 渲染趋势图表
                    console.log('渲染趋势图表');
                    renderTrendChart(dataToUse, isWeekly);
                    
                    // 渲染新增的图表
            console.log('渲染现金流成本对比图');
            renderCashflowCostChart(dataToUse, isWeekly);
            console.log('渲染投资回报对比图');
            renderInvestmentRevenueChart(dataToUse, isWeekly);
            console.log('渲染老店与纯新现金流对比图');
            renderOldNewCashflowChart(dataToUse, isWeekly);
            
            // 保存当前数据作为下次比较的基准
            lastWeeklyData = JSON.parse(JSON.stringify(dataToUse));
            console.log('图表更新成功');
                } catch (error) {
                    console.error('渲染图表时出错:', error);
                }
            })
            .catch(error => {
                console.error('Error loading monthly data:', error);
            });
    }
    
    // 渲染趋势图表
    function renderTrendChart(data, isWeekly = false) {
        console.log('=== 开始渲染趋势图表 ===');
        console.log('数据长度:', data.length, 'isWeekly:', isWeekly);
        
        // 检查Chart.js是否已加载
        if (typeof Chart === 'undefined') {
            console.error('Chart.js 未加载，无法渲染图表');
            return;
        }
        
        // 检查数据是否为空
        if (!data || data.length === 0) {
            console.error('数据为空，无法渲染趋势图表');
            // 显示提示信息
            const chartContainer = document.querySelector('#trend-chart').parentElement;
            chartContainer.innerHTML += '<div style="text-align: center; color: #666; padding: 20px;">暂无数据</div>';
            return;
        }
        
        // 检查Canvas元素
        const canvas = document.getElementById('trend-chart');
        if (!canvas) {
            console.error('未找到trend-chart Canvas元素');
            return;
        }
        console.log('Canvas元素:', canvas);
        console.log('Canvas宽高:', canvas.width, canvas.height);
        
        // 检查Canvas容器样式
        const container = canvas.parentElement;
        console.log('Canvas容器:', container);
        console.log('容器宽高:', container.clientWidth, container.clientHeight);
        
        // 确保容器有高度
        if (container.clientHeight === 0) {
            container.style.height = '400px';
            console.log('已设置容器高度为400px');
        }
        
        const ctx = canvas.getContext('2d');
        if (!ctx) {
            console.error('无法获取Canvas上下文');
            return;
        }
        console.log('Canvas上下文获取成功');
        
        try {
            // 准备数据
            const isMonthly = !isWeekly;
            console.log('数据项示例:', data[0]);
            
            // 确保Month/Week字段存在
            data.forEach((item, index) => {
                if (isMonthly && !item.Month) {
                    console.warn(`第${index}项数据缺少Month字段`);
                    item.Month = index + 1;
                }
                if (!isMonthly && !item.Week) {
                    console.warn(`第${index}项数据缺少Week字段`);
                    item.Week = index + 1;
                }
            });
            
            const labels = data.map(item => isMonthly ? `Month ${item.Month}` : `Week ${item.Week}`);
            let dataSeries = [];
            let title = '';
            let yLabel = '';
            let color = '#4a90e2';
            let xLabel = isMonthly ? '月数' : '周数';
            
            console.log('当前图表类型:', currentChartType);
            
            switch (currentChartType) {
                case 'revenue':
                    dataSeries = data.map(item => item.RevenueTotal || 0);
                    title = isMonthly ? '每月营收趋势' : '每周营收趋势';
                    yLabel = '营收（元）';
                    color = '#4caf50';
                    break;
                case 'cash':
                    dataSeries = data.map(item => item.Cash || 0);
                    title = isMonthly ? '每月现金余额趋势' : '每周现金余额趋势';
                    yLabel = '现金余额（元）';
                    color = '#2196f3';
                    break;
                case 'cashflow':
                    dataSeries = data.map(item => isMonthly ? item.CashFlowMonthly || 0 : item.CashFlowWeekly || 0);
                    title = isMonthly ? '现金流含成本支出趋势' : '每周现金流含成本支出趋势';
                    yLabel = '现金流（元）';
                    color = '#9c27b0';
                    break;
                case 'cashinflow':
                    // 计算现金流入：只考虑收入，不考虑支出
                    dataSeries = data.map((item, index) => {
                        // 现金流入 = 卡类现金流 + 治疗现金流 + 矫正现金流
                        const cashFlowCard = item.CashFlowCard || 0;
                        const cashFlowTreatment = item.CashFlowTreatment || 0;
                        const cashFlowOrtho = item.CashFlowOrtho || 0;
                        const result = cashFlowCard + cashFlowTreatment + cashFlowOrtho;
                        console.log(`第${index}项现金流入:`, { cashFlowCard, cashFlowTreatment, cashFlowOrtho, result });
                        return result;
                    });
                    title = isMonthly ? '每月现金流入趋势' : '每周现金流入趋势';
                    yLabel = '现金流入（元）';
                    color = '#4caf50';
                    break;
                case 'members':
                    dataSeries = data.map(item => item.TotalMembers || 0);
                    title = isMonthly ? '每月会员趋势' : '每周会员趋势';
                    yLabel = '会员数';
                    color = '#ff9800';
                    break;
            }
            
            console.log('图表数据:', {
                labelsCount: labels.length,
                dataSeriesMin: Math.min(...dataSeries),
                dataSeriesMax: Math.max(...dataSeries),
                title: title,
                yLabel: yLabel
            });
            
            // 移除之前可能添加的提示信息
            const existingHint = container.querySelector('div');
            if (existingHint) {
                existingHint.remove();
            }
            
            // 销毁旧图表
            let existingChart = Chart.getChart(ctx);
            if (existingChart) {
                console.log('销毁现有图表实例');
                existingChart.destroy();
            }
            
            console.log('创建新图表实例');
            
            // 创建新图表
            chart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: yLabel,
                        data: dataSeries,
                        backgroundColor: `${color}20`, // 半透明背景
                        borderColor: color,
                        borderWidth: 2,
                        tension: 0.3,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {
                            display: true,
                            text: title,
                            font: {
                                size: 16
                            }
                        },
                        legend: {
                            display: true,
                            position: 'top'
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: false,
                            title: {
                                display: true,
                                text: yLabel
                            },
                            ticks: {
                                callback: function(value) {
                                    if (value >= 1000) {
                                        return value.toFixed(0);
                                    }
                                    return value;
                                }
                            }
                        },
                        x: {
                            title: {
                                display: true,
                                text: xLabel
                            }
                        }
                    }
                }
            });
            
            console.log('=== 趋势图表渲染成功 ===');
        } catch (error) {
            console.error('=== 渲染趋势图表出错 ===');
            console.error('错误信息:', error.message);
            console.error('错误堆栈:', error.stack);
            // 显示错误信息
            const chartContainer = canvas.parentElement;
            chartContainer.innerHTML += `<div style="text-align: center; color: #ff6b6b; padding: 20px;">图表渲染失败: ${error.message}</div>`;
        }
    }
    

    
    // 渲染当月现金流与总成本对比图
    function renderCashflowCostChart(data, isWeekly = false) {
        console.log('=== 开始渲染现金流成本对比图 ===');
        console.log('数据长度:', data.length, 'isWeekly:', isWeekly);
        
        // 检查数据是否为空
        if (!data || data.length === 0) {
            console.error('数据为空，无法渲染现金流成本对比图');
            // 显示提示信息
            const chartContainer = document.querySelector('#cashflow-cost-chart').parentElement;
            chartContainer.innerHTML += '<div style="text-align: center; color: #666; padding: 20px;">暂无数据</div>';
            return;
        }
        
        // 检查Canvas元素
        const canvas = document.getElementById('cashflow-cost-chart');
        if (!canvas) {
            console.error('未找到cashflow-cost-chart Canvas元素');
            return;
        }
        console.log('Canvas元素:', canvas);
        console.log('Canvas宽高:', canvas.width, canvas.height);
        
        // 检查Canvas容器样式
        const container = canvas.parentElement;
        console.log('Canvas容器:', container);
        console.log('容器宽高:', container.clientWidth, container.clientHeight);
        
        // 确保容器有高度
        if (container.clientHeight === 0) {
            container.style.height = '400px';
            console.log('已设置容器高度为400px');
        }
        
        const ctx = canvas.getContext('2d');
        if (!ctx) {
            console.error('无法获取Canvas上下文');
            return;
        }
        console.log('Canvas上下文获取成功');
        
        try {
            // 准备数据
            const isMonthly = !isWeekly;
            console.log('数据项示例:', data[0]);
            
            // 确保Month/Week字段存在
            data.forEach((item, index) => {
                if (isMonthly && !item.Month) {
                    console.warn(`第${index}项数据缺少Month字段`);
                    item.Month = index + 1;
                }
                if (!isMonthly && !item.Week) {
                    console.warn(`第${index}项数据缺少Week字段`);
                    item.Week = index + 1;
                }
            });
            
            const labels = data.map(item => isMonthly ? `Month ${item.Month}` : `Week ${item.Week}`);
            console.log('生成的标签:', labels);
            
            // 使用现金流入值，即不考虑支出项
            const cashflowData = data.map((item, index) => {
                // 现金流入 = 卡类现金流 + 治疗现金流 + 矫正现金流
                const cashFlowCard = item.CashFlowCard || 0;
                const cashFlowTreatment = item.CashFlowTreatment || 0;
                const cashFlowOrtho = item.CashFlowOrtho || 0;
                const result = cashFlowCard + cashFlowTreatment + cashFlowOrtho;
                console.log(`第${index}项现金流入:`, { cashFlowCard, cashFlowTreatment, cashFlowOrtho, result });
                return result;
            });
            
            const costData = data.map((item, index) => {
                const result = item.Costs || 0;
                console.log(`第${index}项成本:`, result);
                return result;
            });
            
            const title = isMonthly ? '当月现金流入与总成本对比' : '当周现金流入与总成本对比';
            const xLabel = isMonthly ? '月数' : '周数';
            
            console.log('最终图表数据:', {
                labelsCount: labels.length,
                cashflowDataMin: Math.min(...cashflowData),
                cashflowDataMax: Math.max(...cashflowData),
                costDataMin: Math.min(...costData),
                costDataMax: Math.max(...costData)
            });
            
            // 移除之前可能添加的提示信息
            const existingHint = container.querySelector('div');
            if (existingHint) {
                existingHint.remove();
            }
            
            // 获取或创建图表实例
            let cashflowCostChart = Chart.getChart(ctx);
            
            if (cashflowCostChart) {
                console.log('销毁现有图表实例');
                cashflowCostChart.destroy();
            }
            
            console.log('创建新图表实例');
            
            // 创建新图表
            cashflowCostChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: isMonthly ? '当月现金流入' : '当周现金流入',
                            data: cashflowData,
                            backgroundColor: 'rgba(33, 150, 243, 0.2)',
                            borderColor: '#2196f3',
                            borderWidth: 2,
                            tension: 0.3,
                            fill: true
                        },
                        {
                            label: isMonthly ? '当月总成本' : '当周总成本',
                            data: costData,
                            backgroundColor: 'rgba(244, 67, 54, 0.2)',
                            borderColor: '#f44336',
                            borderWidth: 2,
                            tension: 0.3,
                            fill: true
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {
                            display: true,
                            text: title,
                            font: {
                                size: 16
                            }
                        },
                        legend: {
                            display: true,
                            position: 'top'
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: false,
                            title: {
                                display: true,
                                text: '金额（元）'
                            }
                        },
                        x: {
                            title: {
                                display: true,
                                text: xLabel
                            }
                        }
                    }
                }
            });
            
            console.log('=== 现金流成本对比图渲染成功 ===');
            
        } catch (error) {
            console.error('=== 渲染现金流成本对比图出错 ===');
            console.error('错误信息:', error.message);
            console.error('错误堆栈:', error.stack);
            // 显示错误信息
            const chartContainer = canvas.parentElement;
            chartContainer.innerHTML += `<div style="text-align: center; color: #ff6b6b; padding: 20px;">图表渲染失败: ${error.message}</div>`;
        }
    }
    
    // 渲染现金投入与总营收累计对比图
    function renderInvestmentRevenueChart(data, isWeekly = false) {
        console.log('=== 开始渲染投资回报对比图 ===');
        console.log('数据长度:', data.length, 'isWeekly:', isWeekly);
        
        // 检查数据是否为空
        if (!data || data.length === 0) {
            console.error('数据为空，无法渲染投资回报对比图');
            // 显示提示信息
            const chartContainer = document.querySelector('#investment-revenue-chart').parentElement;
            chartContainer.innerHTML += '<div style="text-align: center; color: #666; padding: 20px;">暂无数据</div>';
            return;
        }
        
        // 检查Canvas元素
        const canvas = document.getElementById('investment-revenue-chart');
        if (!canvas) {
            console.error('未找到investment-revenue-chart Canvas元素');
            return;
        }
        console.log('Canvas元素:', canvas);
        console.log('Canvas宽高:', canvas.width, canvas.height);
        
        // 检查Canvas容器样式
        const container = canvas.parentElement;
        console.log('Canvas容器:', container);
        console.log('容器宽高:', container.clientWidth, container.clientHeight);
        
        // 确保容器有高度
        if (container.clientHeight === 0) {
            container.style.height = '400px';
            console.log('已设置容器高度为400px');
        }
        
        const ctx = canvas.getContext('2d');
        if (!ctx) {
            console.error('无法获取Canvas上下文');
            return;
        }
        console.log('Canvas上下文获取成功');
        
        try {
            // 准备数据 - 需要计算累计值
            let cumulativeInvestment = [];
            let cumulativeRevenue = [];
            // 初始投资（装修投资280000 + 硬件设备投资300000）
            const initialInvestment = 580000;
            let totalInvestment = initialInvestment;
            let totalRevenue = 0;
            
            console.log('初始投资:', initialInvestment);
            
            data.forEach((item, index) => {
                // 计算总成本投入（初始投资 + 累计成本）
                const costs = item.Costs || 0;
                const revenue = item.RevenueTotal || 0;
                totalInvestment += costs;
                totalRevenue += revenue;
                
                cumulativeInvestment.push(totalInvestment);
                cumulativeRevenue.push(totalRevenue);
                
                console.log(`第${index}项累计投资/营收:`, totalInvestment, totalRevenue);
            });
            
            // 准备图表数据
            const isMonthly = !isWeekly;
            
            // 确保Month/Week字段存在
            data.forEach((item, index) => {
                if (isMonthly && !item.Month) {
                    console.warn(`第${index}项数据缺少Month字段`);
                    item.Month = index + 1;
                }
                if (!isMonthly && !item.Week) {
                    console.warn(`第${index}项数据缺少Week字段`);
                    item.Week = index + 1;
                }
            });
            
            const labels = data.map(item => isMonthly ? `Month ${item.Month}` : `Week ${item.Week}`);
            const xLabel = isMonthly ? '月数' : '周数';
            
            console.log('投资回报对比图数据:', {
                labelsCount: labels.length,
                cumulativeInvestment: cumulativeInvestment,
                cumulativeRevenue: cumulativeRevenue
            });
            
            // 移除之前可能添加的提示信息
            const existingHint = container.querySelector('div');
            if (existingHint) {
                existingHint.remove();
            }
            
            // 获取或创建图表实例
            let investmentRevenueChart = Chart.getChart(ctx);
            
            if (investmentRevenueChart) {
                console.log('销毁现有图表实例');
                investmentRevenueChart.destroy();
            }
            
            console.log('创建新图表实例');
            
            // 创建新图表
            investmentRevenueChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: '总成本投入',
                            data: cumulativeInvestment,
                            backgroundColor: 'rgba(255, 152, 0, 0.2)',
                            borderColor: '#ff9800',
                            borderWidth: 2,
                            tension: 0.3,
                            fill: true
                        },
                        {
                            label: '截止当前总营收',
                            data: cumulativeRevenue,
                            backgroundColor: 'rgba(76, 175, 80, 0.2)',
                            borderColor: '#4caf50',
                            borderWidth: 2,
                            tension: 0.3,
                            fill: true
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {
                            display: true,
                            text: '总成本投入与总营收累计对比',
                            font: {
                                size: 16
                            }
                        },
                        legend: {
                            display: true,
                            position: 'top'
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: false,
                            title: {
                                display: true,
                                text: '金额（元）'
                            }
                        },
                        x: {
                            title: {
                                display: true,
                                text: xLabel
                            }
                        }
                    }
                }
            });
            
            console.log('=== 投资回报对比图渲染成功 ===');
        } catch (error) {
            console.error('=== 渲染投资回报对比图出错 ===');
            console.error('错误信息:', error.message);
            console.error('错误堆栈:', error.stack);
            // 显示错误信息
            const chartContainer = canvas.parentElement;
            chartContainer.innerHTML += `<div style="text-align: center; color: #ff6b6b; padding: 20px;">图表渲染失败: ${error.message}</div>`;
        }
    }
    
    // 渲染老店与纯新现金流对比图
    function renderOldNewCashflowChart(data, isWeekly = false) {
        console.log('=== 开始渲染老店与纯新现金流对比图 ===');
        console.log('数据长度:', data.length, 'isWeekly:', isWeekly);
        
        // 检查数据是否为空
        if (!data || data.length === 0) {
            console.error('数据为空，无法渲染老店与纯新现金流对比图');
            // 显示提示信息
            const chartContainer = document.querySelector('#old-new-cashflow-chart').parentElement;
            chartContainer.innerHTML += '<div style="text-align: center; color: #666; padding: 20px;">暂无数据</div>';
            return;
        }
        
        // 检查Canvas元素
        const canvas = document.getElementById('old-new-cashflow-chart');
        if (!canvas) {
            console.error('未找到old-new-cashflow-chart Canvas元素');
            return;
        }
        console.log('Canvas元素:', canvas);
        console.log('Canvas宽高:', canvas.width, canvas.height);
        
        // 检查Canvas容器样式
        const container = canvas.parentElement;
        console.log('Canvas容器:', container);
        console.log('容器宽高:', container.clientWidth, container.clientHeight);
        
        // 确保容器有高度
        if (container.clientHeight === 0) {
            container.style.height = '400px';
            console.log('已设置容器高度为400px');
        }
        
        const ctx = canvas.getContext('2d');
        if (!ctx) {
            console.error('无法获取Canvas上下文');
            return;
        }
        console.log('Canvas上下文获取成功');
        
        try {
            // 获取患者详细记录以计算老店和新店的现金流
            fetch('/api/results/patient_details')
                .then(response => response.json())
                .then(patientDetails => {
                    console.log('患者详细记录:', patientDetails.length);
                    
                    // 准备图表数据
                    const isMonthly = !isWeekly;
                    
                    // 按月份或周数分组，计算老店和新店的现金流
                    const groupedData = {};
                    
                    // 遍历患者详细记录
                    patientDetails.forEach(record => {
                        // 确保Month字段存在
                        if (!record.Month) {
                            record.Month = Math.floor((record.Day - 1) / 31) + 1;
                        }
                        
                        const key = isMonthly ? record.Month : Math.ceil(record.Day / 7);
                        if (!groupedData[key]) {
                            groupedData[key] = {
                                oldCashFlow: 0,
                                newCashFlow: 0
                            };
                        }
                        
                        const cashFlow = record.CashFlow || 0;
                        const source = record.Source || 'unknown';
                        console.log('患者记录:', record.PatientID, record.Day, record.Action, source, cashFlow);
                        
                        if (source === 'existing' || source === 'all') {
                            // 老店带来的现金流（包括初始会员）
                            groupedData[key].oldCashFlow += cashFlow;
                        } else if (source === 'native') {
                            // 纯新带来的现金流
                            groupedData[key].newCashFlow += cashFlow;
                        }
                    });
                    
                    // 准备图表的标签和数据
                    const labels = [];
                    const oldCashFlowData = [];
                    const newCashFlowData = [];
                    
                    // 确保所有月份/周数都有数据
                    // 找出最大的月份/周数
                    const maxKey = Math.max(...Object.keys(groupedData).map(k => parseInt(k)));
                    
                    // 从1到maxKey遍历，确保每个月份/周数都有数据
                    for (let key = 1; key <= maxKey; key++) {
                        const label = isMonthly ? `Month ${key}` : `Week ${key}`;
                        labels.push(label);
                        oldCashFlowData.push(groupedData[key] ? groupedData[key].oldCashFlow : 0);
                        newCashFlowData.push(groupedData[key] ? groupedData[key].newCashFlow : 0);
                    }
                    
                    const title = isMonthly ? '老店与纯新患者月度现金流对比' : '老店与纯新患者周度现金流对比';
                    const xLabel = isMonthly ? '月数' : '周数';
                    
                    console.log('最终图表数据:', {
                        labels: labels,
                        oldCashFlowData: oldCashFlowData,
                        newCashFlowData: newCashFlowData
                    });
                    
                    // 移除之前可能添加的提示信息
                    const existingHint = container.querySelector('div');
                    if (existingHint) {
                        existingHint.remove();
                    }
                    
                    // 获取或创建图表实例
                    let oldNewCashflowChart = Chart.getChart(ctx);
                    
                    if (oldNewCashflowChart) {
                        console.log('销毁现有图表实例');
                        oldNewCashflowChart.destroy();
                    }
                    
                    console.log('创建新图表实例');
                    
                    // 创建新图表 - 使用折线图替代柱状图
                    oldNewCashflowChart = new Chart(ctx, {
                        type: 'line',
                        data: {
                            labels: labels,
                            datasets: [
                                {
                                    label: '老店带来的现金流',
                                    data: oldCashFlowData,
                                    backgroundColor: 'rgba(76, 175, 80, 0.2)',
                                    borderColor: '#4caf50',
                                    borderWidth: 2,
                                    tension: 0.3,
                                    fill: true
                                },
                                {
                                    label: '纯新患者带来的现金流',
                                    data: newCashFlowData,
                                    backgroundColor: 'rgba(255, 152, 0, 0.2)',
                                    borderColor: '#ff9800',
                                    borderWidth: 2,
                                    tension: 0.3,
                                    fill: true
                                }
                            ]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                                title: {
                                    display: true,
                                    text: title,
                                    font: {
                                        size: 16
                                    }
                                },
                                legend: {
                                    display: true,
                                    position: 'top'
                                }
                            },
                            scales: {
                                y: {
                                    beginAtZero: false,
                                    title: {
                                        display: true,
                                        text: '现金流入（元）'
                                    }
                                },
                                x: {
                                    title: {
                                        display: true,
                                        text: xLabel
                                    }
                                }
                            }
                        }
                    });
                    
                    console.log('=== 老店与纯新现金流对比图渲染成功 ===');
                })
                .catch(error => {
                    console.error('获取患者详细记录失败:', error);
                    // 显示错误信息
                    const chartContainer = canvas.parentElement;
                    chartContainer.innerHTML += `<div style="text-align: center; color: #ff6b6b; padding: 20px;">获取数据失败: ${error.message}</div>`;
                });
        } catch (error) {
            console.error('=== 渲染老店与纯新现金流对比图出错 ===');
            console.error('错误信息:', error.message);
            console.error('错误堆栈:', error.stack);
            // 显示错误信息
            const chartContainer = canvas.parentElement;
            chartContainer.innerHTML += `<div style="text-align: center; color: #ff6b6b; padding: 20px;">图表渲染失败: ${error.message}</div>`;
        }
    }
    
    // 更新分析
    function updateAnalysis(summary) {
        const analysisStatus = document.getElementById('analysis-status');
        const analysisFindings = document.getElementById('analysis-findings');
        const analysisRecommendations = document.getElementById('analysis-recommendations');
        const avgAnnualReturnElement = document.getElementById('avg-annual-return');
        
        if (summary.total_weeks === 0) {
            // 模拟未开始
            analysisStatus.textContent = '模拟尚未开始';
            analysisFindings.innerHTML = '<li>请开始模拟以查看分析结果</li>';
            analysisRecommendations.innerHTML = '<li>通过参数控制页调整模拟参数</li><li>按周运行模拟，观察结果变化</li>';
            avgAnnualReturnElement.textContent = '0.00%';
            return;
        }
        
        // 基本状态分析
        let status = '正常运营';
        if (summary.final_cash < 0) {
            status = '现金流紧张';
        }
        if (summary.total_profit < 0) {
            status = '经营亏损';
        }
        
        analysisStatus.textContent = status;
        
        // 计算平均年回报率
        const totalDays = summary.total_weeks * 7;
        const yearsElapsed = totalDays / 365;
        
        // 总营收做分子，总投入做分母
        // 总投入 = 初始投资 + 累计成本
        const initialInvestment = 580000; // 装修投资280000 + 硬件设备投资300000
        const totalCosts = summary.total_revenue - summary.total_profit;
        const totalInvestment = initialInvestment + totalCosts;
        
        let avgAnnualReturn = 0;
        if (totalInvestment > 0 && yearsElapsed > 0) {
            // 平均年回报率 = (总营收 / 总投入 - 1) / yearsElapsed * 100%
            avgAnnualReturn = ((summary.total_revenue / totalInvestment - 1) / yearsElapsed) * 100;
        }
        
        // 更新平均年回报率显示，包括计算用到的数字
        avgAnnualReturnElement.innerHTML = `${avgAnnualReturn.toFixed(2)}%<br>
            <small style="font-size: 0.8em; color: #666;">
            计算：(总营收 ${summary.total_revenue.toFixed(2)} / 总投入 ${totalInvestment.toFixed(2)} - 1) / ${yearsElapsed.toFixed(2)} 年 × 100%
            </small>`;
        
        // 关键发现
        const findings = [];
        if (summary.total_profit > 0) {
            findings.push(`累计盈利 ${summary.total_profit.toFixed(2)} 元`);
        } else {
            findings.push(`累计亏损 ${Math.abs(summary.total_profit).toFixed(2)} 元`);
        }
        
        findings.push(`累计服务客户 ${summary.total_customers} 人`);
        findings.push(`最终会员数 ${summary.total_members} 人`);
        findings.push(`平均年回报率 ${avgAnnualReturn.toFixed(2)}%`);
        findings.push(`总投入 ${totalInvestment.toFixed(2)} 元（初始投资 ${initialInvestment} 元 + 累计成本 ${totalCosts.toFixed(2)} 元）`);
        
        // 生成HTML
        const findingsHtml = findings.map(f => `<li>${f}</li>`).join('');
        analysisFindings.innerHTML = findingsHtml;
        
        // 建议
        const recommendations = [];
        if (summary.final_cash < 0) {
            recommendations.push('建议关注现金流，考虑调整成本结构');
        }
        if (summary.total_profit < 0) {
            recommendations.push('建议分析成本构成，寻找降低成本的空间');
        }
        if (summary.total_members < summary.total_customers * 0.3) {
            recommendations.push('建议提高会员转化率，增强客户粘性');
        }
        recommendations.push('继续按周运行模拟，观察长期趋势');
        
        // 生成HTML
        const recommendationsHtml = recommendations.map(r => `<li>${r}</li>`).join('');
        analysisRecommendations.innerHTML = recommendationsHtml;
    }
}
