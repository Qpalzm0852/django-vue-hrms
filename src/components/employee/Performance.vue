<template>
  <div class="biz-page">
    <section class="biz-page__hero">
      <div class="biz-page__hero-copy">
        <p class="biz-page__eyebrow">Performance Review</p>
        <h1 class="biz-page__title">我的绩效</h1>
        <p class="biz-page__description">
          统一查看绩效评分、评价内容和评估人信息。支持按考核期间检索，便于快速回看某个阶段的绩效反馈。
        </p>
        <div class="biz-page__meta">
          <span class="biz-page__badge">绩效记录 {{ total }} 条</span>
          <span class="biz-page__badge">本页 {{ performanceListShow.length }} 条</span>
        </div>
      </div>
      <div class="biz-page__hero-side">
        <div class="biz-page__stat">
          <p class="biz-page__stat-label">平均评分</p>
          <p class="biz-page__stat-value">{{ averageScore }}</p>
        </div>
      </div>
    </section>

    <el-card class="biz-page__panel">
      <div class="biz-page__toolbar">
        <div class="biz-page__toolbar-main">
          <h2 class="biz-page__toolbar-title">绩效记录</h2>
          <p class="biz-page__toolbar-desc">按期间检索个人绩效数据，便于快速对比不同考核周期的反馈结果。</p>
        </div>
      </div>

      <el-form :inline="true" class="biz-page__filters">
        <el-form-item label="期间">
          <el-input
            v-model="searchQuery.period"
            placeholder="请输入期间，如 2024-01 或 2024-Q1"
            clearable
            style="width: 240px"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" icon="el-icon-search" @click="getPerformanceList">查询</el-button>
          <el-button type="default" icon="el-icon-refresh-right" @click="resetSearch">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table
        :data="performanceListShow"
        border
        stripe
        v-loading="loading"
        element-loading-text="加载中..."
      >
        <el-table-column type="index" label="#" width="60" align="center" />
        <el-table-column prop="period" label="期间" width="150" align="center" />
        <el-table-column prop="score" label="评分" width="120" align="center">
          <template slot-scope="scope">
            <span v-if="scope.row.score !== null && scope.row.score !== undefined" class="score-text">
              {{ parseFloat(scope.row.score).toFixed(2) }}
            </span>
            <span v-else class="status-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="dimension" label="维度" width="150" align="center">
          <template slot-scope="scope">
            <span v-if="scope.row.dimension">{{ scope.row.dimension }}</span>
            <span v-else class="status-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="comment" label="评价" min-width="300" show-overflow-tooltip>
          <template slot-scope="scope">
            <span v-if="scope.row.comment">{{ scope.row.comment }}</span>
            <span v-else class="status-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="evaluator_name" label="评估人" width="150" align="center">
          <template slot-scope="scope">
            <span v-if="scope.row.evaluator_name">{{ scope.row.evaluator_name }}</span>
            <span v-else class="status-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" align="center">
          <template slot-scope="scope">
            {{ formatDateTime(scope.row.created_at) }}
          </template>
        </el-table-column>
      </el-table>

      <div v-if="!loading && !performanceListShow.length" class="biz-page__table-empty">
        <p class="biz-page__table-empty-title">当前没有绩效记录</p>
        <p class="biz-page__table-empty-desc">可以调整期间筛选，或等待新的绩效考核结果同步后再查看。</p>
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
        period: '',
      },
      performanceList: [],
      performanceListShow: [],
      loading: false,
      currentPage: 1,
      pageSize: 10,
      total: 0,
      currentUserId: '',
    }
  },
  computed: {
    averageScore() {
      const scored = this.performanceList
        .map((item) => Number(item.score))
        .filter((value) => !Number.isNaN(value) && Number.isFinite(value))
      if (!scored.length) return '0.00'
      const avg = scored.reduce((sum, value) => sum + value, 0) / scored.length
      return avg.toFixed(2)
    },
  },
  created() {
    this.currentUserId = window.sessionStorage.getItem('user') || ''
    this.getPerformanceList()
  },
  methods: {
    async getPerformanceList() {
      this.loading = true
      try {
        const params = {
          employee_id: this.currentUserId,
        }
        if (this.searchQuery.period) {
          params.period = this.searchQuery.period
        }
        const { data } = await this.$http.get('/api/performance/', { params })
        const list = Array.isArray(data) ? data : []
        list.sort((a, b) => (b.period || '').localeCompare(a.period || ''))

        this.performanceList = list
        this.total = list.length
        this.currentPage = 1
        this.updatePerformanceListShow()
      } catch (error) {
        console.error('获取绩效列表失败:', error)
        this.$message.error(this.getErrorMessage(error, '获取绩效列表失败'))
        this.performanceList = []
        this.performanceListShow = []
        this.total = 0
      } finally {
        this.loading = false
      }
    },
    updatePerformanceListShow() {
      const start = (this.currentPage - 1) * this.pageSize
      const end = start + this.pageSize
      this.performanceListShow = this.performanceList.slice(start, end)
    },
    resetSearch() {
      this.searchQuery.period = ''
      this.getPerformanceList()
    },
    formatDateTime(dateTime) {
      if (!dateTime) return '-'
      const date = new Date(dateTime)
      const year = date.getFullYear()
      const month = String(date.getMonth() + 1).padStart(2, '0')
      const day = String(date.getDate()).padStart(2, '0')
      const hours = String(date.getHours()).padStart(2, '0')
      const minutes = String(date.getMinutes()).padStart(2, '0')
      const seconds = String(date.getSeconds()).padStart(2, '0')
      return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
    },
    handleSizeChange(val) {
      this.pageSize = val
      this.currentPage = 1
      this.updatePerformanceListShow()
    },
    handleCurrentChange(val) {
      this.currentPage = val
      this.updatePerformanceListShow()
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
.score-text {
  font-size: 16px;
  font-weight: 700;
  color: #3f6a96;
}

.status-muted {
  color: #909399;
}
</style>
