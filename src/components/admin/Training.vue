<template>
  <div class="biz-page">
    <el-breadcrumb separator-class="el-icon-arrow-right">
      <el-breadcrumb-item :to="{ path: '/admin/home' }">首页</el-breadcrumb-item>
      <el-breadcrumb-item>员工管理</el-breadcrumb-item>
      <el-breadcrumb-item>培训管理</el-breadcrumb-item>
    </el-breadcrumb>

    <section class="biz-page__hero">
      <div class="biz-page__hero-content">
        <span class="biz-page__eyebrow">Training Hub</span>
        <h1>培训管理</h1>
        <p>统一维护培训活动、时间安排和参与范围，确保组织学习计划清晰可追踪。</p>
        <div class="biz-page__badges">
          <span class="biz-page__badge">总培训 {{ total }}</span>
          <span class="biz-page__badge">当前页 {{ trainingListShow.length }}</span>
          <span class="biz-page__badge">进行中 {{ activeCount }}</span>
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
          <h2>培训记录</h2>
          <p>支持培训计划新增、编辑、删除和导出，统一沉淀组织学习安排。</p>
        </div>
        <div class="biz-page__toolbar-actions">
          <el-button type="success" icon="el-icon-download" @click="exportToExcel">导出Excel</el-button>
          <el-button type="primary" icon="el-icon-plus" @click="showAddDialog">新增培训</el-button>
        </div>
      </div>

      <el-form :inline="true" class="biz-page__filters">
        <el-form-item label="标题">
          <el-input v-model="searchQuery.title" placeholder="请输入培训标题关键词" clearable style="width: 240px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" icon="el-icon-search" @click="getTrainingList">查询</el-button>
          <el-button type="info" icon="el-icon-refresh-right" @click="resetSearch">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table v-loading="loading" :data="trainingListShow" border stripe style="width: 100%">
        <el-table-column type="index" label="序号" width="68" align="center" />
        <el-table-column prop="title" label="培训标题" min-width="220" show-overflow-tooltip />
        <el-table-column prop="content" label="培训内容" min-width="260" show-overflow-tooltip>
          <template slot-scope="scope">
            <span v-if="scope.row.content">{{ scope.row.content }}</span>
            <span v-else style="color: #909399">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="start_time" label="开始时间" width="180" align="center">
          <template slot-scope="scope">
            <span>{{ scope.row.start_time || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="end_time" label="结束时间" width="180" align="center">
          <template slot-scope="scope">
            <span>{{ scope.row.end_time || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="participants_scope" label="参与范围" min-width="180" show-overflow-tooltip>
          <template slot-scope="scope">
            <span>{{ scope.row.participants_scope || '全员可见' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="116" fixed="right" align="center">
          <template slot-scope="scope">
            <div class="action-buttons">
              <el-tooltip content="编辑" placement="top">
                <el-button type="primary" icon="el-icon-edit" size="mini" circle @click="showEditDialog(scope.row)" />
              </el-tooltip>
              <el-tooltip content="删除" placement="top">
                <el-button type="danger" icon="el-icon-delete" size="mini" circle @click="deleteTraining(scope.row)" />
              </el-tooltip>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="!loading && trainingListShow.length === 0" class="biz-page__table-empty">
        <i class="el-icon-reading" />
        <strong>当前没有匹配的培训记录</strong>
        <span>可以调整标题关键词，或直接新增一项培训计划。</span>
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

    <el-dialog :title="dialogTitle" :visible.sync="dialogVisible" width="62%" @close="dialogClosed">
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="110px">
        <el-form-item label="培训标题" prop="title">
          <el-input v-model="form.title" placeholder="请输入培训标题" clearable maxlength="200" show-word-limit />
        </el-form-item>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="开始时间" prop="start_time">
              <el-date-picker
                v-model="form.start_time"
                type="datetime"
                placeholder="请选择开始时间"
                style="width: 100%"
                value-format="yyyy-MM-dd HH:mm:ss"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="结束时间" prop="end_time">
              <el-date-picker
                v-model="form.end_time"
                type="datetime"
                placeholder="请选择结束时间"
                style="width: 100%"
                value-format="yyyy-MM-dd HH:mm:ss"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="参与范围" prop="participants_scope">
          <el-input
            v-model="form.participants_scope"
            placeholder="如：全体员工、技术部、新员工；为空表示全员"
            clearable
            maxlength="100"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="培训内容" prop="content">
          <el-input v-model="form.content" type="textarea" :rows="6" placeholder="请输入培训内容" />
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
import { exportToExcel as exportTrainingToExcel } from '@/utils/excelExport'
import { getErrorMessage } from '@/utils/errorHandler'

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
      pageSize: 15,
      total: 0,
      dialogVisible: false,
      dialogTitle: '新增培训',
      isEdit: false,
      currentId: null,
      form: {
        title: '',
        content: '',
        start_time: '',
        end_time: '',
        participants_scope: '',
      },
      formRules: {
        title: [{ required: true, message: '请输入培训标题', trigger: 'blur' }],
      },
    }
  },
  computed: {
    activeCount() {
      const now = Date.now()
      return this.trainingList.filter((item) => {
        const start = item.start_time ? new Date(item.start_time).getTime() : null
        const end = item.end_time ? new Date(item.end_time).getTime() : null
        if (start && end) return start <= now && now <= end
        return false
      }).length
    },
    summaryCards() {
      return [
        {
          label: '进行中培训',
          value: this.activeCount,
          helper: '当前周期',
        },
        {
          label: '全员培训',
          value: this.trainingList.filter((item) => !item.participants_scope).length,
          helper: '默认覆盖',
        },
        {
          label: '定向培训',
          value: this.trainingList.filter((item) => item.participants_scope).length,
          helper: '指定范围',
        },
      ]
    },
  },
  created() {
    this.getTrainingList()
  },
  methods: {
    getTrainingId(row) {
      return row.id || row.training_id || row.pk
    },
    refreshPageData() {
      const start = (this.currentPage - 1) * this.pageSize
      const end = start + this.pageSize
      this.trainingListShow = this.trainingList.slice(start, end)
    },
    async getTrainingList() {
      this.loading = true
      try {
        const params = {}
        if (this.searchQuery.title) params.title = this.searchQuery.title

        const { data: res } = await this.$http.get('/api/training/', { params })
        if (Array.isArray(res)) {
          this.trainingList = res
          this.total = res.length
          this.currentPage = 1
          this.refreshPageData()
        } else {
          this.trainingList = []
          this.trainingListShow = []
          this.total = 0
          this.$message.error('获取培训列表失败')
        }
      } catch (error) {
        console.error('获取培训列表失败:', error)
        this.$message.error(getErrorMessage(error, '获取培训列表失败'))
      } finally {
        this.loading = false
      }
    },
    resetSearch() {
      this.searchQuery = {
        title: '',
      }
      this.currentPage = 1
      this.getTrainingList()
    },
    showAddDialog() {
      this.dialogTitle = '新增培训'
      this.isEdit = false
      this.currentId = null
      this.dialogVisible = true
    },
    showEditDialog(row) {
      this.dialogTitle = '编辑培训'
      this.isEdit = true
      this.currentId = this.getTrainingId(row)
      this.form = {
        title: row.title || '',
        content: row.content || '',
        start_time: row.start_time || '',
        end_time: row.end_time || '',
        participants_scope: row.participants_scope || '',
      }
      this.dialogVisible = true
    },
    dialogClosed() {
      this.$refs.formRef && this.$refs.formRef.resetFields()
      this.form = {
        title: '',
        content: '',
        start_time: '',
        end_time: '',
        participants_scope: '',
      }
      this.currentId = null
      this.isEdit = false
    },
    submitForm() {
      this.$refs.formRef.validate(async (valid) => {
        if (!valid) return

        if (this.form.start_time && this.form.end_time && this.form.start_time > this.form.end_time) {
          this.$message.warning('结束时间不能早于开始时间')
          return
        }

        const payload = {
          title: this.form.title,
          content: this.form.content || null,
          start_time: this.form.start_time || null,
          end_time: this.form.end_time || null,
          participants_scope: this.form.participants_scope || null,
        }

        try {
          if (this.isEdit) {
            await this.$http.patch(`/api/training/${this.currentId}/`, payload)
            this.$message.success('更新培训记录成功')
          } else {
            await this.$http.post('/api/training/', payload)
            this.$message.success('新增培训记录成功')
          }
          this.dialogVisible = false
          this.getTrainingList()
        } catch (error) {
          const defaultMsg = this.isEdit ? '更新培训记录失败' : '新增培训记录失败'
          this.$message.error(getErrorMessage(error, defaultMsg))
        }
      })
    },
    deleteTraining(row) {
      const id = this.getTrainingId(row)
      this.$confirm('此操作将永久删除该培训记录，是否继续？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      })
        .then(async () => {
          try {
            await this.$http.delete(`/api/training/${id}/`)
            this.$message.success('删除成功')
            this.getTrainingList()
          } catch (error) {
            this.$message.error(getErrorMessage(error, '删除失败'))
          }
        })
        .catch(() => {
          this.$message.info('已取消删除')
        })
    },
    exportToExcel() {
      if (!this.trainingList || this.trainingList.length === 0) {
        this.$message.warning('没有数据可导出')
        return
      }

      const columns = [
        { key: 'title', label: '培训标题' },
        { key: 'content', label: '培训内容' },
        { key: 'start_time', label: '开始时间' },
        { key: 'end_time', label: '结束时间' },
        { key: 'participants_scope', label: '参与范围' },
      ]

      exportTrainingToExcel(this.trainingList, columns, '培训记录')
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

