<template>
  <div class="biz-page">
    <section class="biz-page__hero">
      <div class="biz-page__hero-copy">
        <p class="biz-page__eyebrow">Announcement Center</p>
        <h1 class="biz-page__title">公告中心</h1>
        <p class="biz-page__description">
          查看公司公告、重要通知和紧急提醒。员工端只读，不提供新增和编辑操作。
        </p>
        <div class="biz-page__meta">
          <span class="biz-page__badge">总公告 {{ total }} 条</span>
          <span class="biz-page__badge">紧急 {{ urgentCount }} 条</span>
        </div>
      </div>
      <div class="biz-page__hero-side">
        <div class="biz-page__stat">
          <p class="biz-page__stat-label">重要公告</p>
          <p class="biz-page__stat-value">{{ importantCount }}</p>
        </div>
      </div>
    </section>

    <el-card class="biz-page__panel">
      <div class="biz-page__toolbar">
        <div class="biz-page__toolbar-main">
          <h2 class="biz-page__toolbar-title">公告列表</h2>
          <p class="biz-page__toolbar-desc">支持按标题和级别筛选，帮助快速找到通知内容。</p>
        </div>
      </div>

      <el-form :inline="true" class="biz-page__filters">
        <el-form-item label="标题">
          <el-input v-model="searchQuery.title" placeholder="请输入标题关键词" clearable style="width: 220px" />
        </el-form-item>
        <el-form-item label="级别">
          <el-select v-model="searchQuery.level" placeholder="请选择级别" clearable style="width: 160px">
            <el-option label="普通" value="普通" />
            <el-option label="重要" value="重要" />
            <el-option label="紧急" value="紧急" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" icon="el-icon-search" @click="getAnnouncementList">查询</el-button>
          <el-button type="default" icon="el-icon-refresh-right" @click="resetSearch">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table v-loading="loading" :data="announcementListShow" border stripe>
        <el-table-column type="index" label="#" width="60" align="center" />
        <el-table-column prop="title" label="标题" min-width="220" show-overflow-tooltip />
        <el-table-column prop="level" label="级别" width="100" align="center">
          <template slot-scope="scope">
            <el-tag :type="getLevelTagType(scope.row.level)" size="small">{{ scope.row.level || '-' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="content" label="内容" min-width="300" show-overflow-tooltip>
          <template slot-scope="scope">{{ scope.row.content || '-' }}</template>
        </el-table-column>
        <el-table-column prop="publisher_name" label="发布人" width="120" align="center">
          <template slot-scope="scope">{{ scope.row.publisher_name || '-' }}</template>
        </el-table-column>
        <el-table-column prop="publish_time" label="发布时间" width="180" align="center">
          <template slot-scope="scope">{{ scope.row.publish_time || '-' }}</template>
        </el-table-column>
      </el-table>

      <div v-if="!loading && !announcementListShow.length" class="biz-page__table-empty">
        <p class="biz-page__table-empty-title">当前没有匹配的公告</p>
        <p class="biz-page__table-empty-desc">可以更换标题关键词或级别后重新查询。</p>
      </div>

      <el-pagination
        class="biz-page__pagination"
        :current-page="currentPage"
        :page-sizes="[10, 20, 50]"
        :page-size="pageSize"
        layout="total, sizes, prev, pager, next, jumper"
        :total="total"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
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
        level: '',
      },
      loading: false,
      announcementList: [],
      announcementListShow: [],
      currentPage: 1,
      pageSize: 10,
      total: 0,
    }
  },
  computed: {
    urgentCount() {
      return this.announcementList.filter((item) => item.level === '紧急').length
    },
    importantCount() {
      return this.announcementList.filter((item) => item.level === '重要').length
    },
  },
  created() {
    this.getAnnouncementList()
  },
  methods: {
    getLevelTagType(level) {
      const map = {
        紧急: 'danger',
        重要: 'warning',
        普通: 'info',
      }
      return map[level] || ''
    },
    refreshPageData() {
      const start = (this.currentPage - 1) * this.pageSize
      const end = start + this.pageSize
      this.announcementListShow = this.announcementList.slice(start, end)
    },
    async getAnnouncementList() {
      this.loading = true
      try {
        const params = {}
        if (this.searchQuery.title) params.title = this.searchQuery.title
        if (this.searchQuery.level) params.level = this.searchQuery.level
        const { data } = await this.$http.get('/api/announcement/', { params })
        const list = Array.isArray(data) ? data : []
        this.announcementList = list
        this.total = list.length
        this.currentPage = 1
        this.refreshPageData()
      } catch (error) {
        console.error('获取公告失败:', error)
        this.$message.error('获取公告失败')
        this.announcementList = []
        this.announcementListShow = []
        this.total = 0
      } finally {
        this.loading = false
      }
    },
    resetSearch() {
      this.searchQuery = { title: '', level: '' }
      this.getAnnouncementList()
    },
    handleSizeChange(size) {
      this.pageSize = size
      this.currentPage = 1
      this.refreshPageData()
    },
    handleCurrentChange(page) {
      this.currentPage = page
      this.refreshPageData()
    },
  },
}
</script>
