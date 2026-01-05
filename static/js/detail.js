// 明细页JavaScript

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 初始化页面
    initDetailPage();
});

// 初始化明细页
function initDetailPage() {
    // 获取DOM元素
    const tabBtns = document.querySelectorAll('.tab-btn');
    const refreshBtn = document.getElementById('refresh-btn');
    const resultTable = document.getElementById('result-table');
    const resultTableBody = document.getElementById('result-table-body');
    const filterMonth = document.getElementById('filter-month');
    const filterWeek = document.getElementById('filter-week');
    const filterDay = document.getElementById('filter-day');
    
    // 当前显示的数据类型
    let currentDataType = 'patient';
    
    // 当前数据
    let currentData = [];
    
    // 分页配置
    let currentPage = 1;
    const itemsPerPage = 100;
    
    // 绑定标签页切换事件
    tabBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            // 更新活跃标签
            tabBtns.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            
            // 切换数据类型
            currentDataType = this.dataset.type;
            currentPage = 1;
            
            // 更新过滤选项
            updateFilterOptions();
            
            // 加载数据
            loadData();
        });
    });
    
    // 刷新按钮点击事件
    refreshBtn.addEventListener('click', function() {
        loadData();
    });
    
    // 过滤事件
    filterMonth.addEventListener('change', function() {
        currentPage = 1;
        loadData();
    });
    
    filterWeek.addEventListener('change', function() {
        currentPage = 1;
        loadData();
    });
    
    filterDay.addEventListener('change', function() {
        currentPage = 1;
        loadData();
    });
    
    // 初始加载数据
    loadData();
    
    // 定期更新数据（每3秒）
    setInterval(loadData, 3000);
    
    // 加载数据
            function loadData() {
        let endpoint;
        
        // 根据数据类型选择不同的API端点
        if (currentDataType === 'daily') {
            endpoint = '/api/results/daily';
        } else if (currentDataType === 'weekly') {
            endpoint = '/api/results/weekly';
        } else if (currentDataType === 'monthly') {
            endpoint = '/api/results/monthly';
        } else if (currentDataType === 'patient') {
            endpoint = '/api/results/patient_details';
        }
        
        fetch(endpoint)
            .then(response => response.json())
            .then(data => {
                currentData = data;
                
                // 应用过滤
                let filteredData = applyFilters(data);
                
                // 对于患者明细，合并同一天同一个患者的记录
                if (currentDataType === 'patient') {
                    filteredData = mergePatientRecords(filteredData);
                }
                
                // 渲染表格
                renderTable(filteredData);
                
                // 渲染分页
                renderPagination(filteredData.length);
            })
            .catch(error => {
                console.error('Error loading data:', error);
            });
    }
    
    // 应用过滤
    function applyFilters(data) {
        const monthFilter = filterMonth.value;
        const weekFilter = filterWeek.value;
        const dayFilter = filterDay.value;
        
        return data.filter(item => {
            // 月数过滤
            if (monthFilter !== 'all') {
                const targetMonth = parseInt(monthFilter);
                if (currentDataType === 'monthly') {
                    // 月数据直接比较Month字段
                    if (item.Month !== targetMonth) {
                        return false;
                    }
                } else if (currentDataType === 'daily' || currentDataType === 'patient' || currentDataType === 'weekly') {
                    // 其他数据类型根据Day计算Month
                    if ('Month' in item) {
                        // 如果数据中已有Month字段，直接使用
                        if (item.Month !== targetMonth) {
                            return false;
                        }
                    } else {
                        // 否则根据Day计算Month，使用与后端相同的逻辑：(Day - 1) // 31 + 1
                        const itemMonth = Math.floor((item.Day - 1) / 31) + 1;
                        if (itemMonth !== targetMonth) {
                            return false;
                        }
                    }
                }
            }
            
            // 周数过滤
            if (weekFilter !== 'all') {
                const targetWeek = parseInt(weekFilter);
                if (currentDataType === 'weekly') {
                    // 周数据直接比较Week字段
                    if (item.Week !== targetWeek) {
                        return false;
                    }
                } else if (currentDataType === 'daily' || currentDataType === 'patient') {
                    // 日数据和患者明细根据Day计算Week
                    const itemWeek = Math.ceil(item.Day / 7);
                    if (itemWeek !== targetWeek) {
                        return false;
                    }
                }
            }
            
            // 天数过滤（适用于日数据和患者明细）
            if ((currentDataType === 'daily' || currentDataType === 'patient') && dayFilter !== 'all') {
                const targetDay = parseInt(dayFilter);
                
                // 直接使用后端计算好的Month字段，避免前后端计算方式不一致
                const itemMonth = item.Month;
                
                // 只有当月份匹配时，才进行天数过滤
                if (monthFilter !== 'all') {
                    const targetMonth = parseInt(monthFilter);
                    
                    // 如果月份不匹配，跳过
                    if (itemMonth !== targetMonth) {
                        return false;
                    }
                }
                
                // 计算项目在当月的日期：使用后端一致的计算方式（每月31天）
                const dayInMonth = item.Day - (itemMonth - 1) * 31;
                
                if (dayInMonth !== targetDay) {
                    return false;
                }
            }
            
            return true;
        });
    }
    
    // 更新过滤选项
    function updateFilterOptions() {
        // 清除现有选项
        filterMonth.innerHTML = '<option value="all">全部</option>';
        filterWeek.innerHTML = '<option value="all">全部</option>';
        filterDay.innerHTML = '<option value="all">全部</option>';
        
        // 计算当前月份
        fetch('/api/simulation/state')
            .then(response => response.json())
            .then(state => {
                const currentMonth = Math.ceil(state.current_day / 30);
                
                // 加载月数选项
                for (let i = 1; i <= currentMonth; i++) {
                    const option = document.createElement('option');
                    option.value = i;
                    option.textContent = `第 ${i} 月`;
                    filterMonth.appendChild(option);
                }
                
                // 根据数据类型显示/隐藏不同的过滤选项
                if (currentDataType === 'monthly') {
                    // 对于月数据，只显示月数过滤
                    filterWeek.style.display = 'none';
                    filterDay.style.display = 'none';
                } else if (currentDataType === 'weekly') {
                    // 对于周数据，显示月数和周数过滤
                    filterWeek.style.display = 'inline-block';
                    filterDay.style.display = 'none';
                    
                    // 加载周数选项
                    for (let i = 1; i <= state.current_week; i++) {
                        const option = document.createElement('option');
                        option.value = i;
                        option.textContent = `第 ${i} 周`;
                        filterWeek.appendChild(option);
                    }
                } else {
                    // 对于日数据和患者明细，显示月数、周数和天数过滤
                    filterWeek.style.display = 'inline-block';
                    filterDay.style.display = 'inline-block';
                    
                    // 加载周数选项
                    for (let i = 1; i <= state.current_week; i++) {
                        const option = document.createElement('option');
                        option.value = i;
                        option.textContent = `第 ${i} 周`;
                        filterWeek.appendChild(option);
                    }
                    
                    // 加载天数选项，最多到31天
                    const maxDays = Math.min(state.current_day, 31);
                    for (let i = 1; i <= maxDays; i++) {
                        const option = document.createElement('option');
                        option.value = i;
                        option.textContent = `第 ${i} 日`;
                        filterDay.appendChild(option);
                    }
                }
            });
    }
    
    // 渲染表格
    function renderTable(data) {
        if (data.length === 0) {
            resultTableBody.innerHTML = '<tr><td colspan="100%" style="text-align: center;">暂无数据</td></tr>';
            return;
        }
        
        // 计算分页数据
        const startIndex = (currentPage - 1) * itemsPerPage;
        const endIndex = startIndex + itemsPerPage;
        const paginatedData = data.slice(startIndex, endIndex);
        
        // 根据数据类型调整字段顺序
        let headers;
        // 定义需要合计的字段
        let sumFields = [];
        if (currentDataType === 'daily') {
            // 每日数据：日期，天，周，月，新客户数，接诊量，总营收，成本，利润，今日现金流，现金余额，分类营收，分类现金流，人员工资
            headers = ['Date', 'Day', 'Week', 'Month', 'NewCustomers', 'PatientsSeen', 'RevenueTotal', 'Costs', 'Profit', 'CashFlowToday', 'Cash', 
                      'RevenueCard', 'RevenueTreatment', 'RevenueOrtho', 
                      'CashFlowCard', 'CashFlowTreatment', 'CashFlowOrtho', 
                      'DoctorSalary', 'NurseSalary', 'OpsSalary',
                      'TotalCustomers', 'TotalMembers'];
            // 每日数据需要合计的字段
            sumFields = ['NewCustomers', 'PatientsSeen', 'RevenueTotal', 'Costs', 'Profit', 'CashFlowToday', 
                       'RevenueCard', 'RevenueTreatment', 'RevenueOrtho', 
                       'CashFlowCard', 'CashFlowTreatment', 'CashFlowOrtho', 
                       'DoctorSalary', 'NurseSalary', 'OpsSalary'];
        } else if (currentDataType === 'weekly') {
            // 每周数据：周数，周起始日期，周结束日期，接诊量，新客户数，总客户数，总营收，成本，利润，周现金流，现金余额，分类营收，分类现金流，人员工资
            headers = ['Week', 'StartDate', 'EndDate', 'PatientsSeen', 'NewCustomers', 'TotalCustomers', 'RevenueTotal', 'Costs', 'Profit', 'CashFlowWeekly', 'Cash', 
                      'RevenueCard', 'RevenueTreatment', 'RevenueOrtho', 
                      'CashFlowCard', 'CashFlowTreatment', 'CashFlowOrtho', 
                      'DoctorSalary', 'NurseSalary', 'OpsSalary',
                      'TotalMembers'];
            // 每周数据需要合计的字段
            sumFields = ['PatientsSeen', 'NewCustomers', 'RevenueTotal', 'Costs', 'Profit', 'CashFlowWeekly', 
                       'RevenueCard', 'RevenueTreatment', 'RevenueOrtho', 
                       'CashFlowCard', 'CashFlowTreatment', 'CashFlowOrtho', 
                       'DoctorSalary', 'NurseSalary', 'OpsSalary'];
        } else if (currentDataType === 'monthly') {
            // 月度数据：月数，接诊量，新客户数，总客户数，总营收，成本，利润，月现金流，现金余额，分类营收，分类现金流，人员工资
            // 与周数据保持相同的字段顺序，只是时间粒度不同
            headers = ['Month', 'PatientsSeen', 'NewCustomers', 'TotalCustomers', 'RevenueTotal', 'Costs', 'Profit', 'CashFlowMonthly', 'Cash', 
                      'RevenueCard', 'RevenueTreatment', 'RevenueOrtho', 
                      'CashFlowCard', 'CashFlowTreatment', 'CashFlowOrtho', 
                      'DoctorSalary', 'NurseSalary', 'OpsSalary',
                      'TotalMembers'];
            // 月度数据需要合计的字段
            sumFields = ['PatientsSeen', 'NewCustomers', 'RevenueTotal', 'Costs', 'Profit', 'CashFlowMonthly', 
                       'RevenueCard', 'RevenueTreatment', 'RevenueOrtho', 
                       'CashFlowCard', 'CashFlowTreatment', 'CashFlowOrtho', 
                       'DoctorSalary', 'NurseSalary', 'OpsSalary'];
        } else {
            // 患者明细：患者ID，日期，天，周，月，星期几，年龄，客户类型，行为，会员卡类型，金额，收入类型，现金流，成本，利润，描述
            headers = ['PatientID', 'Date', 'Day', 'Week', 'Month', 'Weekday', 'Age', 'Source', 'Action', 'CardType', 'Amount', 'RevenueType', 'CashFlow', 'Costs', 'Profit', 'Description'];
            // 患者明细不需要合计
            sumFields = [];
        }
        
        // 渲染表头
        renderTableHeader(headers);
        
        // 渲染数据行
        let html = '';
        paginatedData.forEach(item => {
            html += '<tr>';
            headers.forEach(header => {
                let value = item[header];
                
                // 格式化数值
                if (typeof value === 'number') {
                    // 金额数据最多保留2位小数
                    const amountFields = ['RevenueTotal', 'Costs', 'CashFlowToday', 'Cash', 'Amount', 'CashFlow', 'Profit', 'MonthlyCardRevenue', 'ContractLiability', 'OrthoContractLiability', 'CardContractLiability', 'RevenueTotal', 'CashFlowWeekly', 'CashFlowMonthly'];
                    if (amountFields.includes(header)) {
                        value = value.toFixed(2);
                    } else {
                        // 人数等数据保留整数
                        value = Math.round(value);
                    }
                }
                
                // 将客户类型从英文转换为中文
                if (header === 'Source') {
                    const sourceMap = {
                        'existing': '老店',
                        'native': '新店'
                    };
                    value = sourceMap[value] || value;
                }
                
                html += `<td>${value}</td>`;
            });
            html += '</tr>';
        });
        
        // 渲染合计行（如果需要合计的字段不为空）
        if (sumFields.length > 0) {
            // 计算合计值
            const sums = {};
            // 初始化合计值为0
            sumFields.forEach(field => sums[field] = 0);
            
            // 计算所有数据的合计（包括分页外的数据）
            data.forEach(item => {
                sumFields.forEach(field => {
                    if (item[field] !== undefined && item[field] !== null) {
                        sums[field] += item[field];
                    }
                });
            });
            
            // 添加合计行
            html += '<tr class="total-row">';
            headers.forEach(header => {
                if (sumFields.includes(header)) {
                    let value = sums[header];
                    // 格式化合计值
                    const amountFields = ['RevenueTotal', 'Costs', 'CashFlowToday', 'Cash', 'Amount', 'CashFlow', 'Profit', 'MonthlyCardRevenue', 'ContractLiability', 'OrthoContractLiability', 'CardContractLiability', 'RevenueTotal', 'CashFlowWeekly', 'CashFlowMonthly'];
                    if (amountFields.includes(header)) {
                        value = value.toFixed(2);
                    } else {
                        value = Math.round(value);
                    }
                    html += `<td><strong>${value}</strong></td>`;
                } else if (header === 'Date') {
                    // 每日数据的第一列显示"合计"
                    html += '<td><strong>合计</strong></td>';
                } else if (header === 'Week' || header === 'Month') {
                    // 周/月数据的第一列显示"合计"
                    html += '<td><strong>合计</strong></td>';
                } else {
                    // 其他字段留空
                    html += '<td></td>';
                }
            });
            html += '</tr>';
        }
        
        resultTableBody.innerHTML = html;
    }
    
    // 渲染表头
    function renderTableHeader(headers) {
        const tableHead = resultTable.querySelector('thead');
        let html = '<tr>';
        
        headers.forEach(header => {
            // 中文表头映射
            const headerMap = {
                // 通用字段
                'Day': '天数',
                'Date': '日期',
                'Week': '周数',
                'Month': '月数',
                'Weekday': '星期几',
                'StartDate': '周起始日期',
                'EndDate': '周结束日期',
                'StartDay': '开始天数',
                'EndDay': '结束天数',
                
                // 核心业务字段
                'NewCustomers': '新客户数',
                'TotalCustomers': '总客户数',
                'TotalMembers': '总会员数',
                'PatientsSeen': '接诊量',
                'RevenueTotal': '总营收',
                'Costs': '成本',
                'Cash': '现金余额',
                
                // 分类营收字段
                'RevenueCard': '卡类营收',
                'RevenueTreatment': '治疗营收',
                'RevenueOrtho': '矫正营收',
                
                // 分类现金流字段
                'CashFlowToday': '今日现金流',
                'CashFlowWeekly': '每周现金流',
                'CashFlowMonthly': '每月现金流',
                'CashFlowCard': '卡类现金流',
                'CashFlowTreatment': '治疗现金流',
                'CashFlowOrtho': '矫正现金流',
                
                // 人员相关字段
                'CurrentPediatricDoctors': '当前儿牙医生数',
                'CurrentOrthoDoctors': '当前矫正医生数',
                'CurrentNurses': '当前护士数',
                'CurrentOps': '当前运营数',
                'DoctorSalary': '医生工资',
                'NurseSalary': '护士工资',
                'OpsSalary': '运营工资',
                
                // 会员卡相关字段
                'Card1YrTotal': '1年卡总收入',
                'Card5YrTotal': '5年卡总收入',
                'MonthlyCardRevenue': '月度卡类分摊收入',
                
                // 合同负债相关字段
                'ContractLiability': '合同负债',
                'OrthoContractLiability': '矫正合同负债',
                'CardContractLiability': '卡类合同负债',
                
                // 患者明细字段
                'PatientID': '患者ID',
                'Age': '年龄',
                'Source': '客户类型',
                'Action': '行为',
                'CardType': '会员卡类型',
                'Amount': '金额',
                'RevenueType': '收入类型',
                'CashFlow': '现金流',
                'Profit': '利润',
                'Description': '描述'
            };
            
            // 获取中文表头，确保所有表头都是中文
            const headerText = headerMap[header] || header;
            html += `<th>${headerText}</th>`;
        });
        
        html += '</tr>';
        tableHead.innerHTML = html;
    }
    
    // 渲染分页
    function renderPagination(totalItems) {
        const totalPages = Math.ceil(totalItems / itemsPerPage);
        
        // 移除旧的分页控件
        const oldPagination = document.querySelector('.pagination-controls');
        if (oldPagination) {
            oldPagination.remove();
        }
        
        // 创建分页控件
        const pagination = document.createElement('div');
        pagination.className = 'pagination-controls';
        
        // 上一页按钮
        const prevBtn = document.createElement('button');
        prevBtn.className = 'btn btn-secondary';
        prevBtn.textContent = '上一页';
        prevBtn.disabled = currentPage === 1;
        prevBtn.addEventListener('click', function() {
            if (currentPage > 1) {
                currentPage--;
                loadData();
            }
        });
        pagination.appendChild(prevBtn);
        
        // 页码显示
        const pageInfo = document.createElement('span');
        pageInfo.className = 'page-info';
        pageInfo.textContent = `第 ${currentPage} 页 / 共 ${totalPages} 页`;
        pagination.appendChild(pageInfo);
        
        // 下一页按钮
        const nextBtn = document.createElement('button');
        nextBtn.className = 'btn btn-secondary';
        nextBtn.textContent = '下一页';
        nextBtn.disabled = currentPage === totalPages;
        nextBtn.addEventListener('click', function() {
            if (currentPage < totalPages) {
                currentPage++;
                loadData();
            }
        });
        pagination.appendChild(nextBtn);
        
        // 添加到过滤条件旁边
        const filterSection = document.querySelector('.filter-section');
        filterSection.appendChild(pagination);
    }
    
    // 合并同一天同一个患者的记录
    function mergePatientRecords(data) {
        // 按PatientID和Day分组
        const recordGroups = {};
        
        data.forEach(record => {
            const key = `${record.PatientID}-${record.Day}`;
            if (!recordGroups[key]) {
                recordGroups[key] = [];
            }
            recordGroups[key].push(record);
        });
        
        // 合并每组记录
        const mergedData = [];
        
        for (const key in recordGroups) {
            const group = recordGroups[key];
            if (group.length === 1) {
                // 只有一条记录，直接添加
                mergedData.push(group[0]);
            } else {
                // 合并多条记录
                const mergedRecord = {
                    ...group[0], // 基础信息从第一条记录获取
                    // 数值字段求和
                    Amount: group.reduce((sum, r) => sum + (r.Amount || 0), 0),
                    CashFlow: group.reduce((sum, r) => sum + (r.CashFlow || 0), 0),
                    Costs: group.reduce((sum, r) => sum + (r.Costs || 0), 0),
                    Profit: group.reduce((sum, r) => sum + (r.Profit || 0), 0),
                    // 合并文本字段
                Action: mergeTextFields(group, 'Action'),
                Source: mergeTextFields(group, 'Source'),
                CardType: mergeTextFields(group, 'CardType'),
                RevenueType: mergeTextFields(group, 'RevenueType'),
                Description: mergeDescriptions(group)
                };
                mergedData.push(mergedRecord);
            }
        }
        
        return mergedData;
    }
    
    // 合并文本字段，去重并以逗号分隔
    function mergeTextFields(records, fieldName) {
        const values = new Set();
        records.forEach(record => {
            if (record[fieldName] && record[fieldName] !== 'None' && record[fieldName] !== null && record[fieldName] !== undefined && record[fieldName] !== '') {
                values.add(record[fieldName]);
            }
        });
        return Array.from(values).join(', ');
    }
    
    // 合并描述字段，保留所有描述
    function mergeDescriptions(records) {
        return records.map(record => record.Description).join('; ');
    }
    
    // 导出loadData函数，供外部调用
    window.loadData = loadData;
}
