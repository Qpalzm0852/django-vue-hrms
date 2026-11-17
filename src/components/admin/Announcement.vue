<template>
  <div class="biz-page">
    <el-breadcrumb separator-class="el-icon-arrow-right">
      <el-breadcrumb-item :to="{ path: '/admin/home' }">首页</el-breadcrumb-item>
      <el-breadcrumb-item>员工管理</el-breadcrumb-item>
      <el-breadcrumb-item>公告管理</el-breadcrumb-item>
    </el-breadcrumb>

    <section class="biz-page__hero">
      <div class="biz-page__hero-content">
        <span class="biz-page__eyebrow">Announcement Center</span>
        <h1>公告管理</h1>
        <p>统一维护企业内部公告，按级别和标题快速筛选，保证重要通知及时触达。</p>
        <div class="biz-page__badges">
          <span class="biz-page__badge">总公告 {{ total }}</span>
          <span class="biz-page__badge">当前页 {{ announcementListShow.length }}</span>
          <span class="biz-page__badge">紧急 {{ urgentCount }}</span>
        </div>
      </div>
      <div class="biz-page__hero-stats">
        <article v-for="item in summaryCards" :key="item.label" class="biz-page__stat-card">
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
          <small>{{ item.helper }}</small>
        </article>
      </div>
    </section>

    <el-card class="biz-page__panel" shadow="never">
      <div class="biz-page__toolbar">
        <div class="biz-page__toolbar-copy">
          <h2>公告列表</h2>
          <p>支持新增、编辑、删除和导出，当前共 {{ total }} 条记录。</p>
        </div>
        <div class="biz-page__toolbar-actions">
          <el-button type="success" icon="el-icon-download" @click="exportToExcel">导出Excel</el-button>
          <el-button type="primary" icon="el-icon-plus" @click="showAddDialog">新增公告</el-button>
        </div>
      </div>

      <el-form :inline="true" class="biz-page__filters">
        <el-form-item label="标题">
          <el-input v-model="searchQuery.title" placeholder="请输入标题关键词" clearable style="width: 220px" />
        </el-form-item>
        <el-form-item label="级别">
          <el-select v-model="searchQuery.level" placeholder="请选择级别" clearable style="width: 160px">
            <el-option v-for="item in levelOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" icon="el-icon-search" @click="getAnnouncementList">查询</el-button>
          <el-button type="info" icon="el-icon-refresh-right" @click="resetSearch">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table v-loading="loading" :data="announcementListShow" border stripe style="width: 100%">
        <el-table-column type="index" label="序号" width="68" align="center" />
        <el-table-column prop="title" label="标题" min-width="220" show-overflow-tooltip />
        <el-table-column prop="level" label="级别" width="110" align="center">
          <template slot-scope="scope">
            <el-tag size="small" :type="getLevelTagType(scope.row.level)">
              {{ scope.row.level || '-' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="content" label="内容" min-width="260" show-overflow-tooltip>
          <template slot-scope="scope">
            <span v-if="scope.row.content">{{ scope.row.content }}</span>
            <span v-else style="color: #909399">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="publisher_name" label="发布人" width="120" align="center">
          <template slot-scope="scope">
            <span>{{ scope.row.publisher_name || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="publish_time" label="发布时间" width="180" align="center">
          <template slot-scope="scope">
            <span>{{ scope.row.publish_time || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="116" fixed="right" align="center">
          <template slot-scope="scope">
            <div class="action-buttons">
              <el-tooltip content="编辑" placement="top">
                <el-button type="primary" icon="el-icon-edit" size="mini" circle @click="showEditDialog(scope.row)" />
              </el-tooltip>
              <el-tooltip content="删除" placement="top">
                <el-button type="danger" icon="el-icon-delete" size="mini" circle @click="deleteAnnouncement(scope.row)" />
              </el-tooltip>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="!loading && announcementListShow.length === 0" class="biz-page__table-empty">
        <i class="el-icon-document-remove" />
        <strong>当前没有匹配的公告</strong>
        <span>可以调整筛选条件，或直接新增一条公告。</span>
      </div>

      <el-pagination
        class="biz-page__pagination"
        :current-page="currentPage"
        :page-sizes="[10, 15, 20, 30]"
        :page-size="pageSize"
        layout="total, sizes, prev, pager, next, jumper"
        :total="total"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </el-card>

    <el-dialog :title="dialogTitle" :visible.sync="dialogVisible" width="58%" @close="dialogClosed">
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="108px">
        <el-form-item label="公告标题" prop="title">
          <el-input v-model="form.title" placeholder="请输入公告标题" clearable maxlength="200" show-word-limit />
        </el-form-item>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="级别" prop="level">
              <el-select v-model="form.level" placeholder="请选择级别" clearable style="width: 100%">
                <el-option v-for="item in levelOptions" :key="item.value" :label="item.label" :value="item.value" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="发布人工号" prop="publisher">
              <el-input v-model="form.publisher" placeholder="可选，不填则由后端自动记录" clearable />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="公告内容" prop="content">
          <el-input v-model="form.content" type="textarea" :rows="6" placeholder="请输入公告内容" />
        </el-form-item>
      </el-form>

      <span slot="footer" class="dialog-footer">
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm">确定</el-button>
      </span>
    </el-dialog>
  </div>
</template>

<script>
import { exportToExcel as exportAnnouncementToExcel } from '@/utils/excelExport'
import { getErrorMessage } from '@/utils/errorHandler'

export default {
  data() {
    return {
      searchQuery: {
        title: '',
        level: '',
      },
      levelOptions: [
        { label: '普通', value: '普通' },
        { label: '重要', value: '重要' },
        { label: '紧急', value: '紧急' },
      ],
      announcementList: [],
      announcementListShow: [],
      loading: false,
      currentPage: 1,
      pageSize: 15,
      total: 0,
      dialogVisible: false,
      dialogTitle: '新增公告',
      isEdit: false,
      currentId: null,
      form: {
        title: '',
        content: '',
        level: '',
        publisher: '',
      },
      formRules: {
        title: [{ required: true, message: '请输入公告标题', trigger: 'blur' }],
      },
    }
  },
  computed: {
    urgentCount() {
      return this.announcementList.filter((item) => item.level === '紧急').length
    },
    summaryCards() {
      return [
        {
          label: '紧急公告',
          value: this.urgentCount,
          helper: '优先跟进',
        },
        {
          label: '重要公告',
          value: this.announcementList.filter((item) => item.level === '重要').length,
          helper: '重点通知',
        },
        {
          label: '普通公告',
          value: this.announcementList.filter((item) => item.level === '普通').length,
          helper: '日常消息',
        },
      ]
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
    getAnnouncementId(row) {
      return row.id || row.announcement_id || row.pk
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

        const { data: res } = await this.$http.get('/api/announcement/', { params })
        if (Array.isArray(res)) {
          this.announcementList = res
          this.total = res.length
          this.currentPage = 1
          this.refreshPageData()
        } else {
          this.announcementList = []
          this.announcementListShow = []
          this.total = 0
          this.$message.error('获取公告列表失败')
        }
      } catch (error) {
        console.error('获取公告列表失败:', error)
        this.$message.error(getErrorMessage(error, '获取公告列表失败'))
      } finally {
        this.loading = false
      }
    },
    resetSearch() {
      this.searchQuery = {
        title: '',
        level: '',
      }
      this.currentPage = 1
      this.getAnnouncementList()
    },
    showAddDialog() {
      this.dialogTitle = '新增公告'
      this.isEdit = false
      this.currentId = null
      this.dialogVisible = true
    },
    showEditDialog(row) {
      this.dialogTitle = '编辑公告'
      this.isEdit = true
      this.currentId = this.getAnnouncementId(row)
      this.form = {
        title: row.title || '',
        content: row.content || '',
        level: row.level || '',
        publisher: row.publisher_id || '',
      }
      this.dialogVisible = true
    },
    dialogClosed() {
      this.$refs.formRef && this.$refs.formRef.resetFields()
      this.form = {
        title: '',
        content: '',
        level: '',
        publisher: '',
      }
      this.currentId = null
      this.isEdit = false
    },
    submitForm() {
      this.$refs.formRef.validate(async (valid) => {
        if (!valid) return

        const payload = {
          title: this.form.title,
          content: this.form.content || null,
          level: this.form.level || null,
          publisher: this.form.publisher || null,
        }

        try {
          if (this.isEdit) {
            await this.$http.patch(`/api/announcement/${this.currentId}/`, payload)
            this.$message.success('更新公告成功')
          } else {
            await this.$http.post('/api/announcement/', payload)
            this.$message.success('新增公告成功')
          }
          this.dialogVisible = false
          this.getAnnouncementList()
        } catch (error) {
          const defaultMsg = this.isEdit ? '更新公告失败' : '新增公告失败'
          this.$message.error(getErrorMessage(error, defaultMsg))
        }
      })
    },
    deleteAnnouncement(row) {
      const id = this.getAnnouncementId(row)
      this.$confirm('此操作将永久删除该公告，是否继续？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      })
        .then(async () => {
          try {
            await this.$http.delete(`/api/announcement/${id}/`)
            this.$message.success('删除公告成功')
            this.getAnnouncementList()
          } catch (error) {
            this.$message.error(getErrorMessage(error, '删除公告失败'))
          }
        })
        .catch(() => {
          this.$message.info('已取消删除')
        })
    },
    exportToExcel() {
      if (!this.announcementList || this.announcementList.length === 0) {
        this.$message.warning('没有数据可导出')
        return
      }

      const columns = [
        { key: 'title', label: '标题' },
        { key: 'level', label: '级别' },
        { key: 'content', label: '内容' },
        { key: 'publisher_name', label: '发布人' },
        { key: 'publish_time', label: '发布时间' },
      ]

      exportAnnouncementToExcel(this.announcementList, columns, '公告记录')
      this.$message.success('导出成功')
    },
    handleSizeChange(pageSize) {
      this.pageSize = pageSize
      this.currentPage = 1
      this.refreshPageData()
    },
    handleCurrentChange(currentPage) {
      this.currentPage = currentPage
      this.refreshPageData()
    },
  },
}
</script>

<style lang="less" scoped>
/deep/ .el-breadcrumb {
  margin: 4px 0 10px;
}

/deep/ .el-breadcrumb__inner {
  color: #355d92;
}

.action-buttons {
  display: flex;
  justify-content: center;
  gap: 8px;
}

/deep/ .action-buttons .el-button {
  box-shadow: none;
}

/deep/ .el-dialog {
  border-radius: 16px;
  overflow: hidden;
}

/deep/ .el-dialog__header {
  background: #f8fafc;
  border-bottom: 1px solid #e7edf5;
}

/deep/ .el-dialog__body {
  padding: 20px 22px 14px;
}

/deep/ .el-dialog__footer {
  border-top: 1px solid #e7edf5;
  background: #f8fafc;
}

@media (max-width: 768px) {
  .action-buttons {
    gap: 6px;
  }
}
</style>

