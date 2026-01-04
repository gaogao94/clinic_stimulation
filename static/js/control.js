// 控制页JavaScript

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 初始化页面
    initControlPage();
});

// 初始化控制页
function initControlPage() {
    // 获取DOM元素
    const paramsForm = document.getElementById('params-form');
    const resetBtn = document.getElementById('reset-btn');
    const nextBtn = document.getElementById('next-btn');
    const alertDiv = document.getElementById('alert');
    
    // 加载当前参数
    loadCurrentParams();
    
    // 加载当前状态
    loadCurrentState();
    
    // 添加房租计算功能
    addRentCalculation();
    
    // 表单提交事件 - 参数更新
    paramsForm.addEventListener('change', function(e) {
        // 显示参数已更改的警告
        showAlert('参数已更改，建议重置模拟以应用新参数', 'warning');
    });
    
    // 重置模拟按钮点击事件
    resetBtn.addEventListener('click', function() {
        if (confirm('确定要重置模拟吗？当前进度将丢失。')) {
            resetSimulation();
        }
    });
    
    // 运行下一周按钮点击事件
    nextBtn.addEventListener('click', function() {
        runNextWeek();
    });
    
    // 定期更新状态（每秒）
    setInterval(loadCurrentState, 1000);
}

// 定义全局变量存储DOM元素
let buildingArea, rentPerSqmPerDay, calculatedRent;

// 计算房租的函数（全局作用域）
function calculateRent() {
    const area = parseFloat(buildingArea.value);
    const rent = parseFloat(rentPerSqmPerDay.value);
    
    // 计算每月房租：建筑面积 × 日租金 × 31天
    // 前端简化计算，使用31天作为每月天数
    const monthlyRent = area * rent * 31;
    calculatedRent.value = Math.round(monthlyRent);
}

// 添加房租计算功能
function addRentCalculation() {
    // 获取相关DOM元素并存储到全局变量
    buildingArea = document.getElementById('building_area');
    rentPerSqmPerDay = document.getElementById('rent_per_sqm_per_day');
    calculatedRent = document.getElementById('calculated_rent');
    
    // 当租金输入变化时重新计算
    rentPerSqmPerDay.addEventListener('input', calculateRent);
    
    // 初始计算
    calculateRent();
}

// 加载当前参数
function loadCurrentParams() {
    fetch('/api/params')
        .then(response => response.json())
        .then(params => {
            // 更新表单字段
            for (const [key, value] of Object.entries(params)) {
                // 处理radio按钮组
                if (key === 'clinic_type') {
                    // 查找radio按钮组
                    const radioButtons = document.querySelectorAll(`input[name="${key}"]`);
                    radioButtons.forEach(radio => {
                        radio.checked = (radio.value === value);
                    });
                } else {
                    // 处理普通字段
                    const element = document.getElementById(key);
                    if (element) {
                        element.value = value;
                    }
                }
            }
            
            // 加载参数后重新计算房租
            calculateRent();
        })
        .catch(error => {
            console.error('Error loading params:', error);
        });
}

// 加载当前状态
function loadCurrentState() {
    fetch('/api/simulation/state')
        .then(response => response.json())
        .then(state => {
            // 更新状态显示 - 在参数控制页面不需要显示这些信息
            // document.getElementById('current-week').textContent = state.current_week;
            // document.getElementById('current-day').textContent = state.current_day;
            // document.getElementById('total-days').textContent = state.total_days;
            // document.getElementById('current-cash').textContent = state.current_cash.toFixed(2);
        })
        .catch(error => {
            console.error('Error loading state:', error);
        });
}

// 重置模拟
function resetSimulation() {
    // 获取当前表单参数
    const params = {};
    const formData = new FormData(document.getElementById('params-form'));
    
    // 转换表单数据为对象，排除计算字段
    for (const [key, value] of formData.entries()) {
        // 跳过计算字段
        if (key === 'calculated_rent') {
            continue;
        }
        // 转换数值类型
        params[key] = isNaN(value) ? value : parseFloat(value);
    }
    
    // 发送重置请求
    fetch('/api/params', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(params)
    })
    .then(response => response.json())
    .then(result => {
        if (result.status === 'success') {
            showAlert('模拟已重置，新参数已应用', 'success');
            loadCurrentState();
        } else {
            showAlert(result.message, 'error');
        }
    })
    .catch(error => {
        console.error('Error resetting simulation:', error);
        showAlert('重置模拟失败：' + error.message, 'error');
    });
}

// 运行下一周
function runNextWeek() {
    fetch('/api/simulation/next', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(result => {
        if (result.status === 'success') {
            showAlert(result.message, 'success');
            loadCurrentState();
        } else {
            showAlert(result.message, 'error');
        }
    })
    .catch(error => {
        console.error('Error running next week:', error);
        showAlert('运行下一周失败：' + error.message, 'error');
    });
}

// 显示警告信息
function showAlert(message, type = 'success') {
    const alertDiv = document.getElementById('alert');
    alertDiv.textContent = message;
    alertDiv.className = `alert ${type}`;
    
    // 3秒后自动隐藏
    setTimeout(() => {
        alertDiv.style.display = 'none';
    }, 3000);
}
