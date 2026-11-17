<template>
  <div class="biz-page logs-page">
    <el-breadcrumb separator-class="el-icon-arrow-right">
      <el-breadcrumb-item :to="{ path: '/admin/home' }">首页</el-breadcrumb-item>
      <el-breadcrumb-item>系统管理</el-breadcrumb-item>
      <el-breadcrumb-item>操作日志</el-breadcrumb-item>
    </el-breadcrumb>

    <el-card class="hero-card biz-page__hero biz-page__panel" shadow="never">
      <div class="hero-main biz-page__toolbar">
        <div>
          <h2>操作日志中心</h2>
          <p>统一追踪系统关键操作，支持按用户、模块、操作类型和时间区间筛选。</p>
        </div>
        <el-button type="primary" icon="el-icon-refresh" @click="getLogList">刷新日志</el-button>
      </div>

      <div class="summary-grid biz-page__hero-stats">
        <div class="summary-item" v-for="item in summaryCards" :key="item.key">
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
        </div>
      </div>
    </el-card>

    <el-card class="box-card biz-page__panel" shadow="never">
      <el-row :gutter="16" class="toolbar-row">
        <el-col :xs="24" :sm="12" :md="6">
          <el-input v-model="searchQuery.user_id" placeholder="请输入用户ID" clearable />
        </el-col>

        <el-col :xs="24" :sm="12" :md="6">
          <el-select v-model="searchQuery.action_type" placeholder="请选择操作类型" clearable style="width: 100%">
            <el-option v-for="item in actionTypeOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-col>

        <el-col :xs="24" :sm="12" :md="6">
          <el-input v-model="searchQuery.module" placeholder="请输入模块名称" clearable />
        </el-col>

        <el-col :xs="24" :sm="12" :md="6">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="yyyy-MM-dd"
            style="width: 100%"
          />
        </el-col>
      </el-row>

      <el-row class="toolbar-actions">
        <el-button type="primary" icon="el-icon-search" @click="getLogList">查询</el-button>
        <el-button type="info" icon="el-icon-refresh-right" @click="resetSearch">重置</el-button>
        <el-button type="success" icon="el-icon-download" @click="handleExport">导出Excel</el-button>
      </el-row>

      <el-table v-loading="loading" :data="logListShow" border stripe class="data-table">
        <el-table-column type="index" label="序号" width="64" align="center" />

        <el-table-column prop="user_name" label="用户" min-width="140" align="center">
          <template slot-scope="scope">
            <div class="user-col">
              <div class="user-name">{{ scope.row.user_name || '-' }}</div>
              <div class="user-code">{{ scope.row.user_code || '-' }}</div>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="action_type" label="操作类型" width="120" align="center">
          <template slot-scope="scope">
            <el-tag :type="getActionTypeTagType(scope.row.action_type)" size="small">
              {{ getActionTypeLabel(scope.row.action_type, scope.row.action_type_display) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="module" label="模块" width="120" align="center">
          <template slot-scope="scope">{{ scope.row.module || '-' }}</template>
        </el-table-column>

        <el-table-column prop="resource_type" label="资源类型" width="130" align="center">
          <template slot-scope="scope">{{ scope.row.resource_type || '-' }}</template>
        </el-table-column>

        <el-table-column prop="description" label="操作描述" min-width="260" show-overflow-tooltip />

        <el-table-column prop="ip_address" label="IP地址" width="140" align="center">
          <template slot-scope="scope">{{ scope.row.ip_address || '-' }}</template>
        </el-table-column>

        <el-table-column prop="created_at" label="操作时间" width="178" align="center">
          <template slot-scope="scope">{{ formatDateTime(scope.row.created_at) }}</template>
        </el-table-column>
      </el-table>

      <el-pagination
        class="pagination"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
        :current-page="currentPage"
        :page-sizes="[20, 30, 50, 100]"
        :page-size="pageSize"
        layout="total, sizes, prev, pager, next, jumper"
        :total="total"
      />
    </el-card>
  </div>
</template>

<script>
import { exportToExcel } from '@/utils/excelExport'
import { getErrorMessage } from '@/utils/errorHandler'

export default {
  name: 'OperationLogs',
  data() {
    return {
      searchQuery: {
        user_id: '',
        action_type: '',
        module: '',
      },
      dateRange: null,
      logList: [],
      logListShow: [],
      loading: false,
      currentPage: 1,
      pageSize: 20,
      total: 0,
      actionTypeOptions: [
        { label: '创建', value: 'CREATE' },
        { label: '更新', value: 'UPDATE' },
        { label: '删除', value: 'DELETE' },
        { label: '登录', value: 'LOGIN' },
        { label: '登出', value: 'LOGOUT' },
        { label: '通过', value: 'APPROVE' },
        { label: '拒绝', value: 'REJECT' },
        { label: '导出', value: 'EXPORT' },
      ],
    }
  },
  computed: {
    summaryCards() {
      const today = this.getTodayString()
      const todayCount = this.logList.filter(item => String(item.created_at || '').slice(0, 10) === today).length
      const riskCount = this.logList.filter(item => ['DELETE', 'REJECT'].includes(item.action_type)).length
      const exportCount = this.logList.filter(item => item.action_type === 'EXPORT').length
      return [
        { key: 'total', label: '日志总量', value: this.total },
        { key: 'today', label: '今日新增', value: todayCount },
        { key: 'risk', label: '高风险操作', value: riskCount },
        { key: 'export', label: '导出次数', value: exportCount },
      ]
    },
  },
  created() {
    this.getLogList()
  },
  methods: {
    getTodayString() {
      const now = new Date()
      const y = now.getFullYear()
      const m = String(now.getMonth() + 1).padStart(2, '0')
      const d = String(now.getDate()).padStart(2, '0')
      return `${y}-${m}-${d}`
    },
    getActionTypeLabel(actionType, actionTypeDisplay) {
      if (actionTypeDisplay) return actionTypeDisplay
      const map = {
        CREATE: '创建',
        UPDATE: '更新',
        DELETE: '删除',
        LOGIN: '登录',
        LOGOUT: '登出',
        APPROVE: '通过',
        REJECT: '拒绝',
        EXPORT: '导出',
      }
      return map[actionType] || actionType || '-'
    },
    getActionTypeTagType(actionType) {
      const tagTypeMap = {
        CREATE: 'success',
        UPDATE: 'warning',
        DELETE: 'danger',
        LOGIN: 'info',
        LOGOUT: '',
        APPROVE: 'success',
        REJECT: 'danger',
        EXPORT: 'info',
      }
      return tagTypeMap[actionType] || ''
    },
    formatDateTime(dateTime) {
      if (!dateTime) return '-'
      const date = new Date(dateTime)
      if (Number.isNaN(date.getTime())) return '-'
      const year = date.getFullYear()
      const month = String(date.getMonth() + 1).padStart(2, '0')
      const day = String(date.getDate()).padStart(2, '0')
      const hours = String(date.getHours()).padStart(2, '0')
      const minutes = String(date.getMinutes()).padStart(2, '0')
      const seconds = String(date.getSeconds()).padStart(2, '0')
      return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
    },
    buildQueryParams() {
      const params = {}
      if (this.searchQuery.user_id) params.user_id = this.searchQuery.user_id
      if (this.searchQuery.action_type) params.action_type = this.searchQuery.action_type
      if (this.searchQuery.module) params.module = this.searchQuery.module
      if (this.dateRange && this.dateRange.length === 2) {
        params.start_date = `${this.dateRange[0]} 00:00:00`
        params.end_date = `${this.dateRange[1]} 23:59:59`
      }
      return params
    },
    async getLogList() {
      this.loading = true
      try {
        const { data: res } = await this.$http.get('/api/operation-logs/', { params: this.buildQueryParams() })
        const list = Array.isArray(res) ? res : Array.isArray(res.results) ? res.results : []
        this.logList = list
        this.total = Array.isArray(res) ? list.length : Number(res.count || list.length)
        this.currentPage = 1
        this.updateLogListShow()
      } catch (error) {
        console.error('获取操作日志失败:', error)
        this.$message.error(getErrorMessage(error, '获取操作日志失败'))
        this.logList = []
        this.logListShow = []
        this.total = 0
      } finally {
        this.loading = false
      }
    },
    resetSearch() {
      this.searchQuery = { user_id: '', action_type: '', module: '' }
      this.dateRange = null
      this.currentPage = 1
      this.getLogList()
    },
    handleExport() {
      if (!this.logList || this.logList.length === 0) {
        this.$message.warning('没有数据可导出')
        return
      }

      const exportData = this.logList.map((item, index) => ({
        序号: index + 1,
        用户: item.user_name || item.user_code || '-',
        用户ID: item.user_code || '-',
        操作类型: this.getActionTypeLabel(item.action_type, item.action_type_display),
        模块: item.module || '-',
        资源类型: item.resource_type || '-',
        操作描述: item.description || '-',
        IP地址: item.ip_address || '-',
        操作时间: this.formatDateTime(item.created_at),
      }))

      exportToExcel(exportData, '操作日志')
      this.$message.success('导出成功')
    },
    updateLogListShow() {
      const start = (this.currentPage - 1) * this.pageSize
      const end = start + this.pageSize
      this.logListShow = this.logList.slice(start, end)
    },
    handleSizeChange(pageSize) {
      this.pageSize = pageSize
      this.currentPage = 1
      this.updateLogListShow()
    },
    handleCurrentChange(currentPage) {
      this.currentPage = currentPage
      this.updateLogListShow()
    },
  },
}
</script>

<style lang="less" scoped>
.logs-page {
  .hero-card {
    margin-bottom: 16px;
    border-radius: 14px;
    background: radial-gradient(circle at 95% 20%, rgba(47, 136, 223, 0.12), rgba(47, 136, 223, 0)), #ffffff;
  }

  .hero-main {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;

    h2 {
      margin: 0;
      font-size: 24px;
      color: #11365f;
    }

    p {
      margin: 8px 0 0;
      color: #4f6d8f;
      font-size: 14px;
    }
  }

  .summary-grid {
    margin-top: 16px;
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 12px;
  }

  .summary-item {
    background: #f7faff;
    border: 1px solid #dbe9fb;
    border-radius: 12px;
    padding: 12px 14px;
    display: flex;
    flex-direction: column;
    gap: 6px;

    span {
      font-size: 12px;
      color: #5d7695;
    }

    strong {
      font-size: 22px;
      color: #12365f;
      line-height: 1;
    }
  }

  .box-card {
    margin-top: 0;
  }

  .toolbar-row {
    margin-bottom: 12px;
  }

  .toolbar-actions {
    display: flex;
    justify-content: flex-end;
    gap: 10px;
    margin-bottom: 10px;
  }

  .data-table {
    margin-top: 0;
  }

  .user-col {
    line-height: 1.35;
  }

  .user-name {
    font-weight: 600;
    color: #1f3f67;
  }

  .user-code {
    font-size: 12px;
    color: #7a8ea6;
  }

  .pagination {
    margin-top: 16px;
    text-align: right;
  }
}

@media (max-width: 992px) {
  .logs-page {
    .summary-grid {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }

    .toolbar-actions {
      justify-content: flex-start;
      flex-wrap: wrap;
    }
  }
}

@media (max-width: 640px) {
  .logs-page {
    .hero-main {
      flex-direction: column;
      align-items: flex-start;
    }

    .summary-grid {
      grid-template-columns: 1fr;
    }
  }
}
</style>
