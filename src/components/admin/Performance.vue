<template>
  <div class="biz-page">
    <el-breadcrumb separator-class="el-icon-arrow-right">
      <el-breadcrumb-item :to="{ path: '/admin/home' }">首页</el-breadcrumb-item>
      <el-breadcrumb-item>员工管理</el-breadcrumb-item>
      <el-breadcrumb-item>绩效管理</el-breadcrumb-item>
    </el-breadcrumb>

    <section class="biz-page__hero">
      <div class="biz-page__hero-content">
        <span class="biz-page__eyebrow">Performance Review</span>
        <h1>绩效管理</h1>
        <p>统一维护员工绩效评分与评估维度，便于季度复盘、晋升参考和人才盘点。</p>
        <div class="biz-page__badges">
          <span class="biz-page__badge">总记录 {{ total }}</span>
          <span class="biz-page__badge">当前页 {{ performanceListShow.length }}</span>
          <span class="biz-page__badge">平均分 {{ averageScore }}</span>
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
          <h2>绩效记录</h2>
          <p>支持按工号和期间筛选，并可快速新增、编辑和导出绩效数据。</p>
        </div>
        <div class="biz-page__toolbar-actions">
          <el-button type="success" icon="el-icon-download" @click="exportExcel">导出Excel</el-button>
          <el-button type="primary" icon="el-icon-plus" @click="showAddDialog">新增绩效</el-button>
        </div>
      </div>

      <el-form :inline="true" class="biz-page__filters">
        <el-form-item label="工号">
          <el-input v-model="searchQuery.employee_id" placeholder="请输入工号" clearable style="width: 200px" />
        </el-form-item>
        <el-form-item label="期间">
          <el-input v-model="searchQuery.period" placeholder="请输入期间（如 2026-03 或 2026-Q1）" clearable style="width: 240px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" icon="el-icon-search" @click="getPerformanceList">查询</el-button>
          <el-button type="info" icon="el-icon-refresh-right" @click="resetSearch">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table v-loading="loading" :data="performanceListShow" border stripe style="width: 100%">
        <el-table-column type="index" label="序号" width="68" align="center" />
        <el-table-column prop="employee_id" label="工号" width="110" align="center" />
        <el-table-column prop="employee_name" label="姓名" width="110" align="center" />
        <el-table-column prop="period" label="期间" width="120" align="center" />
        <el-table-column prop="score" label="评分" width="100" align="center">
          <template slot-scope="scope">
            <span v-if="scope.row.score !== null && scope.row.score !== undefined">{{ Number(scope.row.score).toFixed(2) }}</span>
            <span v-else style="color: #909399">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="dimension" label="维度" width="140" align="center">
          <template slot-scope="scope">
            <span>{{ scope.row.dimension || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="comment" label="评价" min-width="220" show-overflow-tooltip>
          <template slot-scope="scope">
            <span>{{ scope.row.comment || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="evaluator_name" label="评估人" width="120" align="center">
          <template slot-scope="scope">
            <span>{{ scope.row.evaluator_name || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="116" fixed="right" align="center">
          <template slot-scope="scope">
            <div class="action-buttons">
              <el-tooltip content="编辑" placement="top">
                <el-button type="primary" icon="el-icon-edit" size="mini" circle @click="showEditDialog(scope.row)" />
              </el-tooltip>
              <el-tooltip content="删除" placement="top">
                <el-button type="danger" icon="el-icon-delete" size="mini" circle @click="deletePerformance(scope.row)" />
              </el-tooltip>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="!loading && performanceListShow.length === 0" class="biz-page__table-empty">
        <i class="el-icon-data-analysis" />
        <strong>当前没有匹配的绩效记录</strong>
        <span>可以调整员工工号或期间条件，或者直接新增一条绩效数据。</span>
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

    <el-dialog :title="dialogTitle" :visible.sync="dialogVisible" width="60%" @close="dialogClosed">
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="108px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="员工工号" prop="employee">
              <el-input v-model="form.employee" placeholder="请输入员工工号" clearable />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="期间" prop="period">
              <el-input v-model="form.period" placeholder="如 2026-03 或 2026-Q1" clearable />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="评分" prop="score">
              <el-input-number v-model="form.score" :precision="2" :min="0" :max="100" :step="0.1" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="维度" prop="dimension">
              <el-input v-model="form.dimension" placeholder="请输入评估维度" clearable maxlength="50" show-word-limit />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="评估人工号" prop="evaluator">
              <el-input v-model="form.evaluator" placeholder="可选" clearable />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="评价" prop="comment">
          <el-input v-model="form.comment" type="textarea" :rows="4" placeholder="请输入评价内容" maxlength="255" show-word-limit />
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
import { exportToExcel as exportPerfToExcel } from '@/utils/excelExport'
import { getErrorMessage } from '@/utils/errorHandler'

export default {
  data() {
    return {
      searchQuery: {
        employee_id: '',
        period: '',
      },
      performanceList: [],
      performanceListShow: [],
      loading: false,
      currentPage: 1,
      pageSize: 15,
      total: 0,
      dialogVisible: false,
      dialogTitle: '新增绩效',
      isEdit: false,
      currentId: null,
      form: {
        employee: '',
        period: '',
        score: null,
        dimension: '',
        comment: '',
        evaluator: '',
      },
      formRules: {
        employee: [{ required: true, message: '请输入员工工号', trigger: 'blur' }],
        period: [{ required: true, message: '请输入期间', trigger: 'blur' }],
      },
    }
  },
  computed: {
    averageScore() {
      const list = this.performanceList
        .map((item) => Number(item.score))
        .filter((score) => !Number.isNaN(score))
      if (list.length === 0) return '-'
      return (list.reduce((sum, score) => sum + score, 0) / list.length).toFixed(1)
    },
    summaryCards() {
      return [
        {
          label: '高绩效记录',
          value: this.performanceList.filter((item) => Number(item.score) >= 90).length,
          helper: '90 分及以上',
        },
        {
          label: '评估维度',
          value: new Set(this.performanceList.map((item) => item.dimension).filter(Boolean)).size,
          helper: '已覆盖维度',
        },
        {
          label: '评估期间',
          value: new Set(this.performanceList.map((item) => item.period).filter(Boolean)).size,
          helper: '统计周期',
        },
      ]
    },
  },
  created() {
    this.getPerformanceList()
  },
  methods: {
    getPerformanceId(row) {
      return row.id || row.performance_id || row.pk
    },
    refreshPageData() {
      const start = (this.currentPage - 1) * this.pageSize
      const end = start + this.pageSize
      this.performanceListShow = this.performanceList.slice(start, end)
    },
    async getPerformanceList() {
      this.loading = true
      try {
        const params = {}
        if (this.searchQuery.employee_id) params.employee_id = this.searchQuery.employee_id
        if (this.searchQuery.period) params.period = this.searchQuery.period

        const { data: res } = await this.$http.get('/api/performance/', { params })
        if (Array.isArray(res)) {
          this.performanceList = res
          this.total = res.length
          this.currentPage = 1
          this.refreshPageData()
        } else {
          this.performanceList = []
          this.performanceListShow = []
          this.total = 0
          this.$message.error('获取绩效列表失败')
        }
      } catch (error) {
        console.error('获取绩效列表失败:', error)
        this.$message.error(getErrorMessage(error, '获取绩效列表失败'))
      } finally {
        this.loading = false
      }
    },
    resetSearch() {
      this.searchQuery = {
        employee_id: '',
        period: '',
      }
      this.currentPage = 1
      this.getPerformanceList()
    },
    showAddDialog() {
      this.dialogTitle = '新增绩效'
      this.isEdit = false
      this.currentId = null
      this.dialogVisible = true
    },
    showEditDialog(row) {
      this.dialogTitle = '编辑绩效'
      this.isEdit = true
      this.currentId = this.getPerformanceId(row)
      this.form = {
        employee: row.employee_id || '',
        period: row.period || '',
        score: row.score !== null && row.score !== undefined ? Number(row.score) : null,
        dimension: row.dimension || '',
        comment: row.comment || '',
        evaluator: row.evaluator_id || '',
      }
      this.dialogVisible = true
    },
    dialogClosed() {
      this.$refs.formRef && this.$refs.formRef.resetFields()
      this.form = {
        employee: '',
        period: '',
        score: null,
        dimension: '',
        comment: '',
        evaluator: '',
      }
      this.currentId = null
      this.isEdit = false
    },
    submitForm() {
      this.$refs.formRef.validate(async (valid) => {
        if (!valid) return

        const payload = {
          employee: this.form.employee,
          period: this.form.period,
          score: this.form.score === null || this.form.score === '' ? null : this.form.score,
          dimension: this.form.dimension || null,
          comment: this.form.comment || null,
          evaluator: this.form.evaluator || null,
        }

        try {
          if (this.isEdit) {
            await this.$http.patch(`/api/performance/${this.currentId}/`, payload)
            this.$message.success('更新绩效记录成功')
          } else {
            await this.$http.post('/api/performance/', payload)
            this.$message.success('新增绩效记录成功')
          }
          this.dialogVisible = false
          this.getPerformanceList()
        } catch (error) {
          const defaultMsg = this.isEdit ? '更新绩效记录失败' : '新增绩效记录失败'
          this.$message.error(getErrorMessage(error, defaultMsg))
        }
      })
    },
    deletePerformance(row) {
      const id = this.getPerformanceId(row)
      this.$confirm('此操作将永久删除该绩效记录，是否继续？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      })
        .then(async () => {
          try {
            await this.$http.delete(`/api/performance/${id}/`)
            this.$message.success('删除绩效记录成功')
            this.getPerformanceList()
          } catch (error) {
            this.$message.error(getErrorMessage(error, '删除绩效记录失败'))
          }
        })
        .catch(() => {
          this.$message.info('已取消删除')
        })
    },
    exportExcel() {
      if (!this.performanceList || this.performanceList.length === 0) {
        this.$message.warning('没有数据可导出')
        return
      }

      const columns = [
        { key: 'employee_id', label: '工号' },
        { key: 'employee_name', label: '姓名' },
        { key: 'period', label: '期间' },
        { key: 'score', label: '评分' },
        { key: 'dimension', label: '维度' },
        { key: 'comment', label: '评价' },
        { key: 'evaluator_name', label: '评估人' },
      ]

      exportPerfToExcel(this.performanceList, columns, '绩效记录')
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

