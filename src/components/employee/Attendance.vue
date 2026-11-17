<template>
  <div class="biz-page">
    <section class="biz-page__hero">
      <div class="biz-page__hero-copy">
        <p class="biz-page__eyebrow">Attendance Record</p>
        <h1 class="biz-page__title">我的考勤</h1>
        <p class="biz-page__description">
          查看每日打卡、工时和异常说明。筛选某一天后，可以快速核对上班、下班和加班记录是否完整。
        </p>
        <div class="biz-page__meta">
          <span class="biz-page__badge">总记录 {{ total }} 条</span>
          <span class="biz-page__badge">异常 {{ abnormalCount }} 条</span>
        </div>
      </div>
      <div class="biz-page__hero-side">
        <div class="biz-page__stat">
          <p class="biz-page__stat-label">本页工时</p>
          <p class="biz-page__stat-value">{{ totalWorkHours }}</p>
        </div>
      </div>
    </section>

    <el-card class="biz-page__panel">
      <div class="biz-page__toolbar">
        <div class="biz-page__toolbar-main">
          <h2 class="biz-page__toolbar-title">考勤明细</h2>
          <p class="biz-page__toolbar-desc">按日期筛选个人打卡记录，异常项会在表格内高亮显示。</p>
        </div>
      </div>

      <el-form :inline="true" class="biz-page__filters">
        <el-form-item label="日期">
          <el-date-picker
            v-model="searchQuery.work_date"
            type="date"
            placeholder="请选择日期"
            style="width: 200px"
            value-format="yyyy-MM-dd"
            clearable
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" icon="el-icon-search" @click="getAttendanceList">查询</el-button>
          <el-button type="default" icon="el-icon-refresh-right" @click="resetSearch">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table
        :data="attendanceListShow"
        border
        stripe
        v-loading="loading"
        element-loading-text="加载中..."
      >
        <el-table-column type="index" label="#" width="60" align="center" />
        <el-table-column prop="work_date" label="日期" width="120" align="center" />
        <el-table-column prop="check_in" label="上班打卡" width="180" align="center" />
        <el-table-column prop="check_out" label="下班打卡" width="180" align="center" />
        <el-table-column prop="work_hours" label="工时(小时)" width="120" align="center">
          <template slot-scope="scope">
            {{ scope.row.work_hours || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="overtime_hours" label="加班时长(小时)" width="140" align="center">
          <template slot-scope="scope">
            {{ scope.row.overtime_hours || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="abnormal" label="异常说明" min-width="180" show-overflow-tooltip>
          <template slot-scope="scope">
            <span v-if="scope.row.abnormal" class="status-danger">{{ scope.row.abnormal }}</span>
            <span v-else class="status-muted">-</span>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="!loading && !attendanceListShow.length" class="biz-page__table-empty">
        <p class="biz-page__table-empty-title">当前没有考勤记录</p>
        <p class="biz-page__table-empty-desc">可以更换筛选日期，或等待新的考勤数据同步后再查看。</p>
      </div>

      <el-pagination
        class="biz-page__pagination"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
        :current-page="currentPage"
        :page-sizes="[10, 20, 50, 100]"
        :page-size="pageSize"
        layout="total, sizes, prev, pager, next, jumper"
        :total="total"
      />
    </el-card>
  </div>
</template>

<script>
export default {
  data() {
    return {
      searchQuery: {
        work_date: '',
      },
      attendanceList: [],
      attendanceListShow: [],
      loading: false,
      currentPage: 1,
      pageSize: 10,
      total: 0,
      currentUserId: '',
    }
  },
  computed: {
    abnormalCount() {
      return this.attendanceList.filter((item) => item && item.abnormal).length
    },
    totalWorkHours() {
      const sum = this.attendanceListShow.reduce((total, item) => total + Number(item.work_hours || 0), 0)
      return sum ? sum.toFixed(1) : '0.0'
    },
  },
  created() {
    this.currentUserId = window.sessionStorage.getItem('user') || ''
    this.getAttendanceList()
  },
  methods: {
    async getAttendanceList() {
      this.loading = true
      try {
        const params = {
          employee_id: this.currentUserId,
        }
        if (this.searchQuery.work_date) {
          params.work_date = this.searchQuery.work_date
        }
        const { data } = await this.$http.get('/api/attendance/', { params })
        const list = Array.isArray(data) ? data : []
        list.sort((a, b) => new Date(b.work_date) - new Date(a.work_date))

        this.attendanceList = list
        this.total = list.length
        this.currentPage = 1
        this.updateAttendanceListShow()
      } catch (error) {
        console.error('获取考勤列表失败:', error)
        this.$message.error(this.getErrorMessage(error, '获取考勤列表失败'))
        this.attendanceList = []
        this.attendanceListShow = []
        this.total = 0
      } finally {
        this.loading = false
      }
    },
    updateAttendanceListShow() {
      const start = (this.currentPage - 1) * this.pageSize
      const end = start + this.pageSize
      this.attendanceListShow = this.attendanceList.slice(start, end)
    },
    resetSearch() {
      this.searchQuery.work_date = ''
      this.getAttendanceList()
    },
    handleSizeChange(val) {
      this.pageSize = val
      this.currentPage = 1
      this.updateAttendanceListShow()
    },
    handleCurrentChange(val) {
      this.currentPage = val
      this.updateAttendanceListShow()
    },
    getErrorMessage(error, defaultMsg) {
      const data = error && error.response && error.response.data
      if (!data) {
        return defaultMsg + '，请检查网络连接'
      }
      if (typeof data === 'string') {
        return data
      }
      if (data.detail) {
        if (Array.isArray(data.detail)) {
          return data.detail[0]
        }
        return String(data.detail)
      }
      const firstKey = Object.keys(data)[0]
      if (firstKey && Array.isArray(data[firstKey]) && data[firstKey].length) {
        return data[firstKey][0]
      }
      return defaultMsg
    },
  },
}
</script>

<style lang="less" scoped>
.status-danger {
  color: #d9534f;
}

.status-muted {
  color: #909399;
}
</style>
