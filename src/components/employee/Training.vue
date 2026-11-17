<template>
  <div class="biz-page">
    <section class="biz-page__hero">
      <div class="biz-page__hero-copy">
        <p class="biz-page__eyebrow">Training Center</p>
        <h1 class="biz-page__title">我的培训</h1>
        <p class="biz-page__description">
          查看可参与或已发布的培训内容，按标题快速检索目标课程，并核对培训时间与适用范围。
        </p>
        <div class="biz-page__meta">
          <span class="biz-page__badge">培训记录 {{ total }} 条</span>
          <span class="biz-page__badge">当前页 {{ trainingListShow.length }} 条</span>
        </div>
      </div>
      <div class="biz-page__hero-side">
        <div class="biz-page__stat">
          <p class="biz-page__stat-label">最近培训开始</p>
          <p class="biz-page__stat-value">{{ latestTrainingStart }}</p>
        </div>
      </div>
    </section>

    <el-card class="biz-page__panel">
      <div class="biz-page__toolbar">
        <div class="biz-page__toolbar-main">
          <h2 class="biz-page__toolbar-title">培训记录</h2>
          <p class="biz-page__toolbar-desc">支持按标题关键词检索培训项目，快速定位某个课程或培训通知。</p>
        </div>
      </div>

      <el-form :inline="true" class="biz-page__filters">
        <el-form-item label="标题">
          <el-input
            v-model="searchQuery.title"
            placeholder="请输入培训标题关键词"
            clearable
            style="width: 220px"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" icon="el-icon-search" @click="getTrainingList">查询</el-button>
          <el-button type="default" icon="el-icon-refresh-right" @click="resetSearch">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table
        :data="trainingListShow"
        border
        stripe
        v-loading="loading"
        element-loading-text="加载中..."
      >
        <el-table-column type="index" label="#" width="60" align="center" />
        <el-table-column prop="title" label="培训标题" min-width="200" show-overflow-tooltip />
        <el-table-column prop="content" label="培训内容" min-width="260" show-overflow-tooltip>
          <template slot-scope="scope">
            <span v-if="scope.row.content">{{ scope.row.content }}</span>
            <span v-else class="status-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="start_time" label="开始时间" width="180" align="center">
          <template slot-scope="scope">
            <span v-if="scope.row.start_time">{{ scope.row.start_time }}</span>
            <span v-else class="status-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="end_time" label="结束时间" width="180" align="center">
          <template slot-scope="scope">
            <span v-if="scope.row.end_time">{{ scope.row.end_time }}</span>
            <span v-else class="status-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="participants_scope" label="参与范围" width="150" align="center">
          <template slot-scope="scope">
            <span v-if="scope.row.participants_scope">{{ scope.row.participants_scope }}</span>
            <span v-else class="status-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" align="center">
          <template slot-scope="scope">
            {{ formatDateTime(scope.row.created_at) }}
          </template>
        </el-table-column>
      </el-table>

      <div v-if="!loading && !trainingListShow.length" class="biz-page__table-empty">
        <p class="biz-page__table-empty-title">当前没有培训记录</p>
        <p class="biz-page__table-empty-desc">可以调整标题关键词，或等待新的培训通知发布后再查看。</p>
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
        title: '',
      },
      trainingList: [],
      trainingListShow: [],
      loading: false,
      currentPage: 1,
      pageSize: 10,
      total: 0,
    }
  },
  computed: {
    latestTrainingStart() {
      if (!this.trainingList.length || !this.trainingList[0].start_time) return '--'
      return this.trainingList[0].start_time.slice(5, 10)
    },
  },
  created() {
    this.getTrainingList()
  },
  methods: {
    async getTrainingList() {
      this.loading = true
      try {
        const params = {}
        if (this.searchQuery.title) {
          params.title = this.searchQuery.title
        }
        const { data } = await this.$http.get('/api/training/', { params })
        const list = Array.isArray(data) ? data : []
        list.sort((a, b) => new Date(b.start_time || 0) - new Date(a.start_time || 0))

        this.trainingList = list
        this.total = list.length
        this.currentPage = 1
        this.updateTrainingListShow()
      } catch (error) {
        console.error('获取培训列表失败:', error)
        this.$message.error(this.getErrorMessage(error, '获取培训列表失败'))
        this.trainingList = []
        this.trainingListShow = []
        this.total = 0
      } finally {
        this.loading = false
      }
    },
    updateTrainingListShow() {
      const start = (this.currentPage - 1) * this.pageSize
      const end = start + this.pageSize
      this.trainingListShow = this.trainingList.slice(start, end)
    },
    resetSearch() {
      this.searchQuery.title = ''
      this.getTrainingList()
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
      this.updateTrainingListShow()
    },
    handleCurrentChange(val) {
      this.currentPage = val
      this.updateTrainingListShow()
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
.status-muted {
  color: #909399;
}
</style>
