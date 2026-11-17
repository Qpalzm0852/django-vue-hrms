<template>
  <div class="biz-page dashboard-page">
    <el-breadcrumb separator-class="el-icon-arrow-right">
      <el-breadcrumb-item :to="{ path: '/admin/home' }">首页</el-breadcrumb-item>
      <el-breadcrumb-item>数据统计</el-breadcrumb-item>
      <el-breadcrumb-item>统计仪表板</el-breadcrumb-item>
    </el-breadcrumb>

    <el-card class="hero-card biz-page__hero biz-page__panel" shadow="never">
      <div class="hero-main biz-page__toolbar">
        <div class="hero-title-wrap">
          <h2>经营与人力数据驾驶舱</h2>
          <p>支持按时间范围筛选并导出图表，用于汇报与决策分析</p>
        </div>

        <div class="hero-actions">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            format="yyyy-MM-dd"
            value-format="yyyy-MM-dd"
            @change="handleDateChange"
          />
          <el-button type="primary" icon="el-icon-refresh" :loading="loading" @click="refreshData">刷新</el-button>
          <el-button type="success" icon="el-icon-download" @click="exportAllCharts">导出图表</el-button>
        </div>
      </div>

      <div class="summary-grid biz-page__hero-stats">
        <div class="summary-item" v-for="item in summaryCards" :key="item.key">
          <span class="summary-label">{{ item.label }}</span>
          <strong class="summary-value">{{ item.value }}</strong>
        </div>
      </div>
    </el-card>

    <div class="charts-grid" v-loading="loading" element-loading-text="数据加载中..." element-loading-spinner="el-icon-loading">
      <el-card class="chart-card" shadow="never">
        <div slot="header" class="card-header"><i class="el-icon-pie-chart"></i><span>员工部门分布</span></div>
        <div ref="departmentChart" class="chart-box"></div>
      </el-card>

      <el-card class="chart-card" shadow="never">
        <div slot="header" class="card-header"><i class="el-icon-s-data"></i><span>员工岗位分布</span></div>
        <div ref="positionChart" class="chart-box"></div>
      </el-card>

      <el-card class="chart-card" shadow="never">
        <div slot="header" class="card-header"><i class="el-icon-data-line"></i><span>考勤趋势</span></div>
        <div ref="attendanceChart" class="chart-box"></div>
      </el-card>

      <el-card class="chart-card" shadow="never">
        <div slot="header" class="card-header"><i class="el-icon-s-grid"></i><span>部门平均薪酬</span></div>
        <div ref="salaryChart" class="chart-box"></div>
      </el-card>

      <el-card class="chart-card" shadow="never">
        <div slot="header" class="card-header"><i class="el-icon-s-operation"></i><span>请假类型统计</span></div>
        <div ref="leaveChart" class="chart-box"></div>
      </el-card>

      <el-card class="chart-card" shadow="never">
        <div slot="header" class="card-header"><i class="el-icon-user-solid"></i><span>员工状态分布</span></div>
        <div ref="statusChart" class="chart-box"></div>
      </el-card>

      <el-card class="chart-card" shadow="never">
        <div slot="header" class="card-header"><i class="el-icon-trophy"></i><span>绩效趋势</span></div>
        <div ref="performanceChart" class="chart-box"></div>
      </el-card>

      <el-card class="chart-card" shadow="never">
        <div slot="header" class="card-header"><i class="el-icon-coin"></i><span>薪酬成本趋势</span></div>
        <div ref="salaryTrendChart" class="chart-box"></div>
      </el-card>

      <el-card class="chart-card" shadow="never">
        <div slot="header" class="card-header"><i class="el-icon-user"></i><span>入离职趋势</span></div>
        <div ref="hireLeaveChart" class="chart-box"></div>
      </el-card>

      <el-card class="chart-card" shadow="never">
        <div slot="header" class="card-header"><i class="el-icon-data-analysis"></i><span>部门绩效对比</span></div>
        <div ref="departmentPerformanceChart" class="chart-box"></div>
      </el-card>
    </div>
  </div>
</template>

<script>
import { getErrorMessage } from '@/utils/errorHandler'

export default {
  name: 'Dashboard',
  data() {
    return {
      loading: false,
      dateRange: [],
      dashboardData: {
        department_distribution: [],
        position_distribution: [],
        attendance_trend: { dates: [], counts: [] },
        salary_by_department: [],
        leave_by_type: { categories: [], series: [] },
        employee_status: [],
        performance_trend: [],
        salary_trend: [],
        hire_leave_trend: { hire: [], leave: [] },
        department_performance: [],
      },
      charts: {},
      chartExportConfig: [
        { key: 'departmentChart', label: '员工部门分布' },
        { key: 'positionChart', label: '员工岗位分布' },
        { key: 'attendanceChart', label: '考勤趋势' },
        { key: 'salaryChart', label: '部门平均薪酬' },
        { key: 'leaveChart', label: '请假类型统计' },
        { key: 'statusChart', label: '员工状态分布' },
        { key: 'performanceChart', label: '绩效趋势' },
        { key: 'salaryTrendChart', label: '薪酬成本趋势' },
        { key: 'hireLeaveChart', label: '入离职趋势' },
        { key: 'departmentPerformanceChart', label: '部门绩效对比' },
      ],
      resizeHandler: null,
      echartsLib: null,
    }
  },
  computed: {
    summaryCards() {
      const departmentCount = this.dashboardData.department_distribution.length
      const positionCount = this.dashboardData.position_distribution.length
      const totalEmployees = this.dashboardData.department_distribution.reduce((sum, item) => sum + Number(item.value || 0), 0)
      const avgAttendance = this.getAverage(this.dashboardData.attendance_trend.counts)
      const latestSalaryCost = this.dashboardData.salary_trend.length
        ? Number(this.dashboardData.salary_trend[this.dashboardData.salary_trend.length - 1].total_cost || 0)
        : 0

      return [
        { key: 'employees', label: '员工总量（统计口径）', value: totalEmployees },
        { key: 'departments', label: '部门数量', value: departmentCount },
        { key: 'positions', label: '岗位数量', value: positionCount },
        { key: 'attendance', label: '期间日均出勤', value: avgAttendance },
        { key: 'salary', label: '最新月薪酬成本', value: this.formatCurrency(latestSalaryCost) },
      ]
    },
  },
  mounted() {
    this.setDefaultRange()
    this.loadStatistics()
    this.resizeHandler = () => this.handleResize()
    window.addEventListener('resize', this.resizeHandler)
  },
  beforeDestroy() {
    window.removeEventListener('resize', this.resizeHandler)
    this.disposeCharts()
  },
  methods: {
    setDefaultRange() {
      const endDate = new Date()
      const startDate = new Date()
      startDate.setDate(endDate.getDate() - 30)
      this.dateRange = [this.formatDate(startDate), this.formatDate(endDate)]
    },
    formatDate(date) {
      const y = date.getFullYear()
      const m = String(date.getMonth() + 1).padStart(2, '0')
      const d = String(date.getDate()).padStart(2, '0')
      return `${y}-${m}-${d}`
    },
    getAverage(arr) {
      const list = Array.isArray(arr) ? arr : []
      if (list.length === 0) return 0
      const sum = list.reduce((acc, v) => acc + Number(v || 0), 0)
      return (sum / list.length).toFixed(1)
    },
    formatCurrency(value) {
      const n = Number(value || 0)
      return `¥${n.toLocaleString()}`
    },
    getRequestParams() {
      const params = {}
      if (Array.isArray(this.dateRange) && this.dateRange.length === 2) {
        params.start_date = this.dateRange[0]
        params.end_date = this.dateRange[1]
      }
      return params
    },
    async loadStatistics() {
      this.loading = true
      try {
        const { data } = await this.$http.get('/api/statistics/dashboard/', { params: this.getRequestParams() })
        if (!data || typeof data !== 'object') {
          this.$message.error('统计数据格式错误')
          return
        }

        this.dashboardData = {
          department_distribution: Array.isArray(data.department_distribution) ? data.department_distribution : [],
          position_distribution: Array.isArray(data.position_distribution) ? data.position_distribution : [],
          attendance_trend: data.attendance_trend || { dates: [], counts: [] },
          salary_by_department: Array.isArray(data.salary_by_department) ? data.salary_by_department : [],
          leave_by_type: data.leave_by_type || { categories: [], series: [] },
          employee_status: Array.isArray(data.employee_status) ? data.employee_status : [],
          performance_trend: Array.isArray(data.performance_trend) ? data.performance_trend : [],
          salary_trend: Array.isArray(data.salary_trend) ? data.salary_trend : [],
          hire_leave_trend: data.hire_leave_trend || { hire: [], leave: [] },
          department_performance: Array.isArray(data.department_performance) ? data.department_performance : [],
        }

        await this.ensureEchartsLoaded()
        this.$nextTick(() => {
          this.initAllCharts()
        })
      } catch (error) {
        console.error('获取统计数据失败:', error)
        this.$message.error(getErrorMessage(error, '获取统计数据失败'))
      } finally {
        this.loading = false
      }
    },
    refreshData() {
      this.loadStatistics()
    },
    handleDateChange() {
      this.loadStatistics()
    },
    async ensureEchartsLoaded() {
      if (this.echartsLib) return this.echartsLib
      const echartsModule = await import('echarts')
      this.echartsLib = echartsModule && echartsModule.default ? echartsModule.default : echartsModule
      return this.echartsLib
    },
    ensureChart(refKey) {
      if (!this.echartsLib) return null
      if (!this.$refs[refKey]) return null
      if (!this.charts[refKey]) {
        this.charts[refKey] = this.echartsLib.init(this.$refs[refKey])
      }
      return this.charts[refKey]
    },
    setChartOption(refKey, option) {
      const chart = this.ensureChart(refKey)
      if (!chart) return
      chart.clear()
      chart.setOption(option, true)
    },
    getEmptyOption(title) {
      return {
        title: {
          text: title,
          left: 'center',
          top: 'center',
          textStyle: {
            color: '#9aa4b2',
            fontSize: 14,
            fontWeight: 'normal',
          },
        },
        xAxis: { show: false },
        yAxis: { show: false },
        series: [],
      }
    },
    initAllCharts() {
      this.initDepartmentChart(this.dashboardData.department_distribution)
      this.initPositionChart(this.dashboardData.position_distribution)
      this.initAttendanceChart(this.dashboardData.attendance_trend)
      this.initSalaryChart(this.dashboardData.salary_by_department)
      this.initLeaveChart(this.dashboardData.leave_by_type)
      this.initStatusChart(this.dashboardData.employee_status)
      this.initPerformanceChart(this.dashboardData.performance_trend)
      this.initSalaryTrendChart(this.dashboardData.salary_trend)
      this.initHireLeaveChart(this.dashboardData.hire_leave_trend)
      this.initDepartmentPerformanceChart(this.dashboardData.department_performance)
    },
    initDepartmentChart(data) {
      if (!Array.isArray(data) || data.length === 0) {
        this.setChartOption('departmentChart', this.getEmptyOption('暂无部门分布数据'))
        return
      }

      this.setChartOption('departmentChart', {
        color: ['#2f88df', '#16a34a', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'],
        tooltip: { trigger: 'item', formatter: '{b}<br/>{c} 人 ({d}%)' },
        legend: { type: 'scroll', bottom: 0 },
        series: [
          {
            type: 'pie',
            radius: ['42%', '72%'],
            center: ['50%', '45%'],
            itemStyle: { borderColor: '#fff', borderWidth: 2 },
            label: { formatter: '{b}\n{c}人' },
            data,
          },
        ],
      })
    },
    initPositionChart(data) {
      if (!Array.isArray(data) || data.length === 0) {
        this.setChartOption('positionChart', this.getEmptyOption('暂无岗位分布数据'))
        return
      }

      const names = data.map((item) => item.name)
      const values = data.map((item) => Number(item.value || 0))

      this.setChartOption('positionChart', {
        color: ['#1d74c9'],
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, formatter: '{b}<br/>人数: {c}' },
        grid: { left: '3%', right: '3%', bottom: '8%', containLabel: true },
        xAxis: { type: 'category', data: names, axisLabel: { interval: 0, rotate: names.length > 6 ? 30 : 0 } },
        yAxis: { type: 'value', minInterval: 1 },
        series: [{ type: 'bar', data: values, barWidth: '52%', itemStyle: { borderRadius: [6, 6, 0, 0] } }],
      })
    },
    initAttendanceChart(data) {
      const dates = Array.isArray(data && data.dates) ? data.dates : []
      const counts = Array.isArray(data && data.counts) ? data.counts : []
      if (dates.length === 0) {
        this.setChartOption('attendanceChart', this.getEmptyOption('暂无考勤趋势数据'))
        return
      }

      this.setChartOption('attendanceChart', {
        color: ['#0ea5e9'],
        tooltip: { trigger: 'axis', formatter: '{b}<br/>出勤人数: {c}' },
        grid: { left: '3%', right: '3%', bottom: '8%', containLabel: true },
        xAxis: { type: 'category', boundaryGap: false, data: dates, axisLabel: { interval: Math.max(0, Math.floor(dates.length / 8)) } },
        yAxis: { type: 'value', minInterval: 1 },
        series: [
          {
            type: 'line',
            smooth: true,
            data: counts,
            symbolSize: 6,
            areaStyle: {
              color: new this.echartsLib.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: 'rgba(14,165,233,0.30)' },
                { offset: 1, color: 'rgba(14,165,233,0.05)' },
              ]),
            },
          },
        ],
      })
    },
    initSalaryChart(data) {
      if (!Array.isArray(data) || data.length === 0) {
        this.setChartOption('salaryChart', this.getEmptyOption('暂无薪酬统计数据'))
        return
      }

      const names = data.map((item) => item.name)
      const values = data.map((item) => Number(item.value || 0))

      this.setChartOption('salaryChart', {
        color: ['#16a34a'],
        tooltip: {
          trigger: 'axis',
          axisPointer: { type: 'shadow' },
          formatter(params) {
            const p = params[0]
            return `${p.name}<br/>平均薪酬: ¥${Number(p.value).toLocaleString()}`
          },
        },
        grid: { left: '3%', right: '3%', bottom: '6%', containLabel: true },
        xAxis: { type: 'value' },
        yAxis: { type: 'category', data: names },
        series: [{ type: 'bar', data: values, barWidth: 16, itemStyle: { borderRadius: [0, 8, 8, 0] } }],
      })
    },
    initLeaveChart(data) {
      const categories = Array.isArray(data && data.categories) ? data.categories : []
      const series = Array.isArray(data && data.series) ? data.series : []
      if (categories.length === 0 || series.length === 0) {
        this.setChartOption('leaveChart', this.getEmptyOption('暂无请假统计数据'))
        return
      }

      const colorMap = {
        待审批: '#f59e0b',
        已通过: '#16a34a',
        已拒绝: '#ef4444',
      }

      this.setChartOption('leaveChart', {
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
        legend: { top: 0 },
        grid: { left: '3%', right: '3%', bottom: '6%', top: '16%', containLabel: true },
        xAxis: { type: 'category', data: categories },
        yAxis: { type: 'value', minInterval: 1 },
        series: series.map((item) => ({
          ...item,
          itemStyle: { color: colorMap[item.name] || undefined },
        })),
      })
    },
    initStatusChart(data) {
      if (!Array.isArray(data) || data.length === 0) {
        this.setChartOption('statusChart', this.getEmptyOption('暂无员工状态数据'))
        return
      }

      this.setChartOption('statusChart', {
        color: ['#22c55e', '#f59e0b', '#ef4444', '#64748b', '#6366f1'],
        tooltip: { trigger: 'item', formatter: '{b}<br/>{c} 人 ({d}%)' },
        legend: { bottom: 0 },
        series: [
          {
            type: 'pie',
            roseType: 'radius',
            radius: ['22%', '72%'],
            center: ['50%', '44%'],
            itemStyle: { borderColor: '#fff', borderWidth: 1 },
            data,
          },
        ],
      })
    },
    initPerformanceChart(data) {
      if (!Array.isArray(data) || data.length === 0) {
        this.setChartOption('performanceChart', this.getEmptyOption('暂无绩效趋势数据'))
        return
      }

      const periods = data.map((item) => item.period)
      const scores = data.map((item) => Number(item.avg_score || 0))

      this.setChartOption('performanceChart', {
        color: ['#8b5cf6'],
        tooltip: { trigger: 'axis', formatter: '{b}<br/>平均绩效: {c} 分' },
        grid: { left: '3%', right: '3%', bottom: '8%', containLabel: true },
        xAxis: { type: 'category', boundaryGap: false, data: periods, axisLabel: { rotate: 30 } },
        yAxis: { type: 'value', min: 0, max: 100 },
        series: [{ type: 'line', smooth: true, data: scores, symbolSize: 6 }],
      })
    },
    initSalaryTrendChart(data) {
      if (!Array.isArray(data) || data.length === 0) {
        this.setChartOption('salaryTrendChart', this.getEmptyOption('暂无薪酬成本趋势数据'))
        return
      }

      const periods = data.map((item) => item.period)
      const costs = data.map((item) => Number(item.total_cost || 0))

      this.setChartOption('salaryTrendChart', {
        color: ['#e67e22'],
        tooltip: {
          trigger: 'axis',
          formatter(params) {
            const p = params[0]
            return `${p.name}<br/>薪酬成本: ¥${Number(p.value).toLocaleString()}`
          },
        },
        grid: { left: '3%', right: '3%', bottom: '8%', containLabel: true },
        xAxis: { type: 'category', boundaryGap: false, data: periods, axisLabel: { rotate: 30 } },
        yAxis: { type: 'value' },
        series: [{ type: 'line', smooth: true, data: costs, symbolSize: 6 }],
      })
    },
    initHireLeaveChart(data) {
      const hire = Array.isArray(data && data.hire) ? data.hire : []
      const leave = Array.isArray(data && data.leave) ? data.leave : []
      if (hire.length === 0 && leave.length === 0) {
        this.setChartOption('hireLeaveChart', this.getEmptyOption('暂无入离职趋势数据'))
        return
      }

      const periods = hire.length ? hire.map((item) => item.period) : leave.map((item) => item.period)
      const hireCounts = hire.map((item) => Number(item.count || 0))
      const leaveCounts = leave.map((item) => Number(item.count || 0))

      this.setChartOption('hireLeaveChart', {
        tooltip: { trigger: 'axis' },
        legend: { data: ['入职', '离职'], top: 0 },
        grid: { left: '3%', right: '3%', bottom: '8%', top: '16%', containLabel: true },
        xAxis: { type: 'category', boundaryGap: false, data: periods, axisLabel: { rotate: 30 } },
        yAxis: { type: 'value', minInterval: 1 },
        series: [
          { name: '入职', type: 'line', smooth: true, data: hireCounts, itemStyle: { color: '#16a34a' } },
          { name: '离职', type: 'line', smooth: true, data: leaveCounts, itemStyle: { color: '#ef4444' } },
        ],
      })
    },
    initDepartmentPerformanceChart(data) {
      if (!Array.isArray(data) || data.length === 0) {
        this.setChartOption('departmentPerformanceChart', this.getEmptyOption('暂无部门绩效数据'))
        return
      }

      const names = data.map((item) => item.name)
      const scores = data.map((item) => Number(item.avg_score || 0))
      const counts = data.map((item) => Number(item.count || 0))

      this.setChartOption('departmentPerformanceChart', {
        color: ['#7c3aed'],
        tooltip: {
          trigger: 'axis',
          axisPointer: { type: 'shadow' },
          formatter(params) {
            const p = params[0]
            const idx = p.dataIndex
            return `${p.name}<br/>平均绩效: ${p.value} 分<br/>人数: ${counts[idx]}`
          },
        },
        grid: { left: '3%', right: '3%', bottom: '8%', containLabel: true },
        xAxis: { type: 'category', data: names, axisLabel: { rotate: names.length > 6 ? 30 : 0 } },
        yAxis: { type: 'value', min: 0, max: 100 },
        series: [{ type: 'bar', data: scores, barWidth: '56%', itemStyle: { borderRadius: [6, 6, 0, 0] } }],
      })
    },
    handleResize() {
      Object.keys(this.charts).forEach((key) => {
        if (this.charts[key]) this.charts[key].resize()
      })
    },
    disposeCharts() {
      Object.keys(this.charts).forEach((key) => {
        if (this.charts[key]) {
          this.charts[key].dispose()
          this.charts[key] = null
        }
      })
    },
    exportAllCharts() {
      this.chartExportConfig.forEach((item, index) => {
        const instance = this.charts[item.key]
        if (!instance) return

        setTimeout(() => {
          const url = instance.getDataURL({ type: 'png', pixelRatio: 2, backgroundColor: '#ffffff' })
          const link = document.createElement('a')
          link.download = `${item.label}.png`
          link.href = url
          document.body.appendChild(link)
          link.click()
          document.body.removeChild(link)
        }, index * 220)
      })

      this.$message.success('图表导出任务已开始')
    },
  },
}
</script>

<style lang="less" scoped>
.dashboard-page {
  --line: rgba(20, 72, 142, 0.12);
  --soft-bg: linear-gradient(180deg, rgba(247, 251, 255, 0.98), rgba(242, 248, 255, 0.92));
}

/deep/ .el-breadcrumb {
  margin: 4px 0 12px;
}

/deep/ .el-breadcrumb__inner {
  color: #355d92;
}

.hero-card {
  border-radius: 18px;
  border: 1px solid var(--line);
  background:
    radial-gradient(900px circle at 0% 0%, rgba(47, 136, 223, 0.12), transparent 56%),
    radial-gradient(1000px circle at 100% 100%, rgba(22, 163, 74, 0.09), transparent 60%),
    #ffffff;
  box-shadow: 0 14px 30px rgba(16, 66, 135, 0.08);
}

/deep/ .hero-card .el-card__body {
  padding: 18px;
}

.hero-main {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 14px;
}

.hero-title-wrap {
  h2 {
    margin: 0;
    font-size: 22px;
    color: #0f3363;
    letter-spacing: 0.3px;
  }

  p {
    margin: 8px 0 0;
    color: #4f6f99;
    font-size: 13px;
  }
}

.hero-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.summary-grid {
  margin-top: 16px;
  display: grid;
  gap: 10px;
  grid-template-columns: repeat(5, minmax(130px, 1fr));
}

.summary-item {
  border: 1px solid rgba(20, 72, 142, 0.1);
  background: var(--soft-bg);
  border-radius: 12px;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.summary-label {
  color: #5c7ea8;
  font-size: 12px;
}

.summary-value {
  color: #134f95;
  font-size: 20px;
  line-height: 1;
}

.charts-grid {
  margin-top: 12px;
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(2, minmax(320px, 1fr));
}

.chart-card {
  border-radius: 16px;
  border: 1px solid var(--line);
  box-shadow: 0 12px 24px rgba(16, 66, 135, 0.07);
  overflow: hidden;
}

/deep/ .chart-card .el-card__body {
  padding: 12px 14px 14px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #154a88;
  font-weight: 700;
  font-size: 14px;

  i {
    color: #2f88df;
    font-size: 16px;
  }
}

.chart-box {
  width: 100%;
  height: 320px;
}

@media (max-width: 1400px) {
  .summary-grid {
    grid-template-columns: repeat(3, minmax(120px, 1fr));
  }
}

@media (max-width: 1100px) {
  .charts-grid {
    grid-template-columns: 1fr;
  }

  .hero-main {
    flex-direction: column;
  }
}

@media (max-width: 768px) {
  /deep/ .hero-card .el-card__body {
    padding: 12px;
  }

  .hero-title-wrap h2 {
    font-size: 18px;
  }

  .summary-grid {
    grid-template-columns: repeat(2, minmax(120px, 1fr));
  }

  .chart-box {
    height: 280px;
  }
}
</style>
